#include "baas_installer/tui.hpp"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <clocale>
#include <thread>

#include <ftxui/component/component.hpp>
#include <ftxui/component/component_options.hpp>
#include <ftxui/component/screen_interactive.hpp>
#include <ftxui/dom/elements.hpp>

#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#endif

namespace baas_installer {

InstallerViewModel::InstallerViewModel(const bool setup_required) {
    state_.screen = setup_required ? InstallerScreen::Setup : InstallerScreen::Installing;
    state_.tasks = {
        {"main", {"主仓库"}},
        {"ocr", {"OCR 组件"}},
        {"deployment", {"文件部署"}},
        {"uv", {"Python / uv"}},
        {"verify", {"完整性检查"}},
        {"launch", {"启动 BAAS"}},
    };
}

void InstallerViewModel::begin_install() {
    std::scoped_lock lock(mutex_);
    state_.screen = InstallerScreen::Installing;
    state_.error.clear();
    state_.log_lines.clear();
    for (auto& [_, task] : state_.tasks) task = {task.label};
}

void InstallerViewModel::update_task(const std::string& id, const TaskStatus status, std::string detail, double progress) {
    std::scoped_lock lock(mutex_);
    auto& task = state_.tasks[id];
    if (task.label.empty()) task.label = id;
    task.status = status;
    task.detail = std::move(detail);
    task.progress = std::clamp(progress, -1.0, 1.0);
    if (!task.detail.empty()) {
        state_.log_lines.push_back(task.label + "：" + task.detail);
        if (state_.log_lines.size() > 8) state_.log_lines.erase(state_.log_lines.begin());
    }
}

void InstallerViewModel::finish_success() {
    std::scoped_lock lock(mutex_);
    state_.screen = InstallerScreen::Succeeded;
    state_.error.clear();
    state_.log_lines.push_back("安装完成，BAAS 已可使用");
}

void InstallerViewModel::finish_failure(std::string error) {
    std::scoped_lock lock(mutex_);
    state_.screen = InstallerScreen::Failed;
    state_.error = std::move(error);
    state_.log_lines.push_back("安装失败：" + state_.error);
}

InstallerSnapshot InstallerViewModel::snapshot() const {
    std::scoped_lock lock(mutex_);
    return state_;
}

bool configure_utf8_terminal() {
#ifdef _WIN32
    const bool input_ok = SetConsoleCP(CP_UTF8) != 0;
    const bool output_ok = SetConsoleOutputCP(CP_UTF8) != 0;
    if (const HANDLE output = GetStdHandle(STD_OUTPUT_HANDLE); output != INVALID_HANDLE_VALUE) {
        DWORD mode = 0;
        if (GetConsoleMode(output, &mode)) SetConsoleMode(output, mode | ENABLE_VIRTUAL_TERMINAL_PROCESSING);
    }
    return input_ok && output_ok;
#else
    return std::setlocale(LC_ALL, "") != nullptr;
#endif
}

void apply_workflow_progress(InstallerViewModel& model, const std::string& task, const std::string& detail) {
    auto status = TaskStatus::Running;
    double progress = -1.0;
    if (detail.find("ready") != std::string::npos || detail.find("verified") != std::string::npos ||
        detail.find("synchronized") != std::string::npos || detail.find("completed") != std::string::npos ||
        detail.find("launched") != std::string::npos) {
        status = TaskStatus::Succeeded;
        progress = 1.0;
    } else if (detail.find("failed") != std::string::npos || detail.find("rolled back") != std::string::npos) {
        status = TaskStatus::Failed;
        progress = 0.0;
    } else if (task == "deployment" && detail.find("main repository") != std::string::npos) {
        progress = 0.35;
    } else if (task == "deployment" && detail.find("OCR repository") != std::string::npos) {
        progress = 0.70;
    } else if (task == "verify") {
        progress = 0.25;
    }
    static const std::map<std::string, std::string> localized{
        {"downloading", "正在下载"},
        {"ready; waiting for parallel task", "下载完成，等待并行任务"},
        {"deploying main repository", "正在部署主仓库"},
        {"deploying OCR repository", "正在部署 OCR 组件"},
        {"verifying deployment", "正在检查部署结果"},
        {"deployment verified", "部署检查通过"},
        {"synchronizing dependencies", "正在同步 Python 依赖"},
        {"dependencies synchronized", "Python 依赖同步完成"},
        {"installation completed", "安装已完成"},
        {"launching BAAS", "正在启动 BAAS"},
        {"BAAS launched", "BAAS 已启动"},
        {"preparation failed; no live files changed", "下载准备失败，现有文件未被修改"},
        {"rolled back", "部署失败，已回滚"},
    };
    const auto found = localized.find(detail);
    model.update_task(task == "complete" ? "verify" : task, status, found == localized.end() ? detail : found->second, progress);
}

std::string redact_cdk(const std::string& cdk) {
    if (cdk.empty()) return "(none)";
    if (cdk.size() <= 4) return "****";
    return cdk.substr(0, 2) + std::string(cdk.size() - 4, '*') + cdk.substr(cdk.size() - 2);
}

int run_unattended(const std::string& configured_cdk, const TuiInstallAction& install) {
    InstallerViewModel model(false);
    model.begin_install();
    const auto [success, error] = install(configured_cdk, model, [] {});
    if (success) model.finish_success();
    else model.finish_failure(error.empty() ? "安装过程未提供错误信息" : error);
    return success ? 0 : 1;
}

namespace {

ftxui::Element task_row(const TaskSnapshot& task, const std::size_t frame) {
    using namespace ftxui;
    Element marker;
    Color tint = Color::GrayDark;
    switch (task.status) {
        case TaskStatus::Pending: marker = text("○"); break;
        case TaskStatus::Running: marker = task.progress < 0 ? spinner(21, frame) : text("●"); tint = Color::Cyan; break;
        case TaskStatus::Succeeded: marker = text("✓"); tint = Color::Green; break;
        case TaskStatus::Failed: marker = text("×"); tint = Color::Red; break;
    }
    Element indicator = task.progress >= 0 ? gauge(task.progress) : filler();
    return vbox({
        hbox({marker | color(tint), text("  " + task.label) | bold, filler(), text(task.detail) | dim}),
        hbox({text("   "), indicator | color(tint) | flex}),
    });
}

double aggregate_progress(const InstallerSnapshot& snapshot) {
    double total = 0.0;
    for (const auto& id : {"main", "ocr", "deployment", "verify", "uv", "launch"}) {
        const auto& task = snapshot.tasks.at(id);
        if (task.status == TaskStatus::Succeeded) total += 1.0;
        else if (task.status == TaskStatus::Running) total += task.progress >= 0 ? task.progress : 0.10;
    }
    return total / 6.0;
}

}  // namespace

int run_tui(const bool setup_required, const std::string& configured_cdk, const TuiInstallAction& install, const bool auto_exit) {
    using namespace ftxui;
    configure_utf8_terminal();
    auto screen = ScreenInteractive::Fullscreen();
    InstallerViewModel model(setup_required);
    bool use_mirror = !configured_cdk.empty();
    std::string cdk = configured_cdk;
    std::atomic<bool> running{false};
    std::atomic<bool> stop_ticks{false};
    std::atomic<std::size_t> frame{0};
    int active_tab = setup_required ? 0 : 1;
    std::thread worker;

    auto wake = [&] { screen.PostEvent(Event::Custom); };
    auto exit_loop = screen.ExitLoopClosure();
    std::function<void()> start_install;
    start_install = [&] {
        if (running.exchange(true)) return;
        if (worker.joinable()) worker.join();
        model.begin_install();
        active_tab = 1;
        wake();
        worker = std::thread([&, chosen_cdk = use_mirror ? cdk : std::string{}] {
            const auto [success, error] = install(chosen_cdk, model, wake);
            if (success) model.finish_success();
            else model.finish_failure(error.empty() ? "安装过程未提供错误信息" : error);
            running = false;
            screen.Post([&, should_exit = auto_exit] {
                active_tab = 2;
                if (should_exit) exit_loop();
            });
        });
    };

    auto mirror = Checkbox("使用 MirrorChyan CDK", &use_mirror);
    InputOption password_option = InputOption::Default();
    password_option.password = true;
    password_option.multiline = false;
    auto cdk_input = Input(&cdk, "输入 CDK", password_option);
    auto begin = Button("开始安装", start_install);
    auto retry = Button("重试", start_install);
    auto close = Button("退出", exit_loop);
    auto setup_controls = Container::Vertical({mirror, cdk_input, begin});
    auto install_controls = Renderer([] { return text(""); });
    auto result_controls = Container::Horizontal({retry, close});
    auto controls = Container::Tab({setup_controls, install_controls, result_controls}, &active_tab);

    auto renderer = Renderer(controls, [&] {
        const auto state = model.snapshot();
        const auto header = vbox({
            text("BLUE ARCHIVE AUTO SCRIPT") | bold | color(Color::Cyan),
            text("安装与迁移工具") | color(Color::GrayLight),
        }) | center;

        if (state.screen == InstallerScreen::Setup) {
            Elements options{mirror->Render()};
            if (use_mirror) options.push_back(hbox({text("CDK  "), cdk_input->Render() | flex}));
            options.push_back(separator());
            options.push_back(begin->Render() | center);
            return vbox({header, separator(), text("安装源设置") | bold, text("没有 CDK 时将使用 Git，并按镜像源自动回退。") | dim,
                         vbox(std::move(options)) | border | size(WIDTH, GREATER_THAN, 48)}) |
                borderRounded | size(WIDTH, GREATER_THAN, 68) | center;
        }

        Elements rows;
        for (const auto& id : {"main", "ocr", "deployment", "verify", "uv", "launch"}) {
            rows.push_back(task_row(state.tasks.at(id), frame.load()));
            rows.push_back(separatorEmpty());
        }
        Elements logs{text("最近状态") | bold};
        for (const auto& line : state.log_lines) logs.push_back(text("  " + line) | dim);
        Element footer;
        if (state.screen == InstallerScreen::Succeeded) {
            footer = vbox({text("安装完成") | bold | color(Color::Green), text("BAAS 已准备就绪。"), close->Render() | center});
        } else if (state.screen == InstallerScreen::Failed) {
            footer = vbox({text("安装失败") | bold | color(Color::Red), paragraph(state.error) | color(Color::RedLight),
                           hbox({retry->Render(), text("  "), close->Render()}) | center});
        } else {
            footer = hbox({text("总体进度  "), gauge(aggregate_progress(state)) | color(Color::Cyan) | flex});
        }
        return vbox({header, separator(), vbox(std::move(rows)) | flex, separator(), vbox(std::move(logs)) | size(HEIGHT, LESS_THAN, 10),
                     separator(), footer}) |
            borderRounded | size(WIDTH, GREATER_THAN, 76) | size(HEIGHT, GREATER_THAN, 28) | center;
    });

    std::thread ticker([&] {
        while (!stop_ticks) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            frame.fetch_add(1);
            wake();
        }
    });
    if (!setup_required) start_install();
    screen.Loop(renderer);
    stop_ticks = true;
    if (ticker.joinable()) ticker.join();
    if (worker.joinable()) worker.join();
    return model.snapshot().screen == InstallerScreen::Succeeded ? 0 : 1;
}

}  // namespace baas_installer
