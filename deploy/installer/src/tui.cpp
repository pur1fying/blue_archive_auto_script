#include "baas_installer/tui.hpp"
#include "baas_installer/paths.hpp"

#include <algorithm>
#include <atomic>
#include <clocale>
#include <ctime>
#include <iomanip>
#include <sstream>
#include <thread>
#include <unordered_set>

#include <ftxui/component/component.hpp>
#include <ftxui/component/component_options.hpp>
#include <ftxui/component/event.hpp>
#include <ftxui/component/screen_interactive.hpp>
#include <ftxui/dom/elements.hpp>

#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#endif

namespace baas_installer {
namespace {

std::string now_timestamp() {
    const auto now = std::time(nullptr);
    std::tm value{};
#ifdef _WIN32
    localtime_s(&value, &now);
#else
    localtime_r(&now, &value);
#endif
    std::ostringstream output;
    output << std::put_time(&value, "%H:%M:%S");
    return output.str();
}

MessageId task_label(const std::string& id) {
    if (id == "main") return MessageId::TaskMain;
    if (id == "ocr") return MessageId::TaskOcr;
    if (id == "deployment") return MessageId::TaskDeployment;
    if (id == "uv") return MessageId::TaskUv;
    if (id == "verify") return MessageId::TaskVerify;
    return MessageId::TaskLaunch;
}

struct ProgressMapping {
    TaskStatus status;
    MessageId detail;
    double progress;
};

bool map_progress(const std::string& detail, ProgressMapping& mapping) {
    static const std::map<std::string, ProgressMapping> mappings{
        {"checking", {TaskStatus::Running, MessageId::StateChecking, -1.0}},
        {"downloading", {TaskStatus::Running, MessageId::StateDownloading, -1.0}},
        {"ready; waiting for parallel task", {TaskStatus::Succeeded, MessageId::StateComplete, 1.0}},
        {"already current", {TaskStatus::Succeeded, MessageId::StateComplete, 1.0}},
        {"deploying main repository", {TaskStatus::Running, MessageId::StateApplying, 0.35}},
        {"deploying OCR repository", {TaskStatus::Running, MessageId::StateApplying, 0.70}},
        {"verifying deployment", {TaskStatus::Running, MessageId::StateChecking, 0.25}},
        {"deployment verified", {TaskStatus::Succeeded, MessageId::StateComplete, 1.0}},
        {"synchronizing dependencies", {TaskStatus::Running, MessageId::StateApplying, -1.0}},
        {"dependencies synchronized", {TaskStatus::Succeeded, MessageId::StateComplete, 1.0}},
        {"installation completed", {TaskStatus::Succeeded, MessageId::StateComplete, 1.0}},
        {"launching BAAS", {TaskStatus::Running, MessageId::StateApplying, -1.0}},
        {"BAAS launched", {TaskStatus::Succeeded, MessageId::StateComplete, 1.0}},
        {"preparation failed; no live files changed", {TaskStatus::Failed, MessageId::StateFailed, 0.0}},
        {"rolled back", {TaskStatus::Failed, MessageId::StateFailed, 0.0}},
    };
    const auto found = mappings.find(detail);
    if (found == mappings.end()) return false;
    mapping = found->second;
    return true;
}

}  // namespace

InstallerViewModel::InstallerViewModel(const bool setup_required, const Language language,
                                       std::shared_ptr<EventLog> event_log)
    : language_(language), event_log_(event_log ? std::move(event_log) : std::make_shared<EventLog>()) {
    state_.screen = setup_required ? InstallerScreen::Setup : InstallerScreen::Installing;
    for (const auto& id : {"main", "ocr", "deployment", "uv", "verify", "launch"}) {
        state_.tasks.emplace(id, TaskSnapshot{message(language_, task_label(id))});
    }
}

void InstallerViewModel::begin_install() {
    std::scoped_lock lock(mutex_);
    state_.screen = InstallerScreen::Installing;
    state_.error.clear();
    state_.exit_requested = false;
    state_.log_scroll = 0;
    decoders_.clear();
    for (auto& [_, task] : state_.tasks) task = {task.label};
}

void InstallerViewModel::update_task(const std::string& id, const TaskStatus status, std::string detail,
                                    const double progress) {
    std::string label;
    std::string log_detail = detail;
    {
        std::scoped_lock lock(mutex_);
        auto& task = state_.tasks[id];
        if (task.label.empty()) task.label = id;
        task.status = status;
        task.detail = std::move(detail);
        task.progress = std::clamp(progress, -1.0, 1.0);
        label = task.label;
    }
    if (!log_detail.empty()) append_event({now_timestamp(), id, "installer", LogSeverity::Info,
                                           label + ": " + log_detail, false});
}

void InstallerViewModel::append_event(LogEvent event) {
    if (event.timestamp.empty()) event.timestamp = now_timestamp();
    event_log_->publish(std::move(event));
}

void InstallerViewModel::append_process_chunk(const std::string& task, const std::string& backend,
                                              const std::string_view chunk) {
    constexpr std::string_view begin_prefix = "probe-section-begin:";
    constexpr std::string_view end_prefix = "probe-section-end:";
    const auto section_text = [](const std::string_view value) {
        std::string text(value);
        while (!text.empty() && (text.back() == '\r' || text.back() == '\n')) text.pop_back();
        return text;
    };
    if (backend.starts_with(begin_prefix)) {
        begin_log_section(task, "probe", backend.substr(begin_prefix.size()), section_text(chunk));
        return;
    }
    if (backend.starts_with(end_prefix)) {
        end_log_section(task, "probe", backend.substr(end_prefix.size()), section_text(chunk));
        return;
    }
    std::vector<DecodedLine> lines;
    std::string section_id;
    {
        std::scoped_lock lock(mutex_);
        lines = decoders_[task + '\0' + backend].consume(chunk);
        const auto active = active_sections_.find(task + '\0' + backend);
        if (active != active_sections_.end()) section_id = active->second;
    }
    for (auto& line : lines) {
        append_event({now_timestamp(), task, backend, LogSeverity::Info, std::move(line.text),
                      line.replace_last, section_id});
    }
}

void InstallerViewModel::begin_log_section(const std::string& task, const std::string& backend,
                                           std::string section_id, std::string title) {
    {
        std::scoped_lock lock(mutex_);
        active_sections_[task + '\0' + backend] = section_id;
    }
    append_event({.timestamp = now_timestamp(), .task = task, .backend = backend,
                  .severity = LogSeverity::Info, .text = std::move(title),
                  .section_id = std::move(section_id),
                  .section_action = LogSectionAction::Begin});
}

void InstallerViewModel::end_log_section(const std::string& task, const std::string& backend,
                                         const std::string& section_id, std::string summary) {
    {
        std::scoped_lock lock(mutex_);
        const auto active = active_sections_.find(task + '\0' + backend);
        if (active != active_sections_.end() && active->second == section_id) {
            active_sections_.erase(active);
        }
    }
    append_event({.timestamp = now_timestamp(), .task = task, .backend = backend,
                  .severity = LogSeverity::Info, .text = std::move(summary),
                  .section_id = section_id, .section_action = LogSectionAction::End});
}

void InstallerViewModel::scroll_logs(const int delta) {
    const auto count = event_log_->snapshot().size();
    std::scoped_lock lock(mutex_);
    if (delta < 0) {
        const auto amount = static_cast<std::size_t>(-delta);
        state_.log_scroll = amount > state_.log_scroll ? 0 : state_.log_scroll - amount;
    } else {
        state_.log_scroll = std::min(count, state_.log_scroll + static_cast<std::size_t>(delta));
    }
}

void InstallerViewModel::add_log_secret(std::string secret) { event_log_->add_secret(std::move(secret)); }
void InstallerViewModel::set_log_sink(std::string path) { event_log_->set_sink(std::move(path)); }
std::string InstallerViewModel::localized(const MessageId id) const { return message(language_, id); }

void InstallerViewModel::finish_success() {
    {
        std::scoped_lock lock(mutex_);
        state_.screen = InstallerScreen::Installing;
        state_.error.clear();
        state_.exit_requested = true;
    }
    append_event({now_timestamp(), "complete", "installer", LogSeverity::Info,
                  message(language_, MessageId::StateComplete), false});
}

void InstallerViewModel::finish_failure(std::string error) {
    std::string logged_error = error;
    {
        std::scoped_lock lock(mutex_);
        state_.screen = InstallerScreen::Failed;
        state_.error = std::move(error);
        state_.exit_requested = false;
    }
    append_event({now_timestamp(), "complete", "installer", LogSeverity::Error, std::move(logged_error), false});
}

void InstallerViewModel::return_to_setup() {
    std::scoped_lock lock(mutex_);
    state_.screen = InstallerScreen::Setup;
    state_.error.clear();
    state_.exit_requested = false;
    state_.log_scroll = 0;
    decoders_.clear();
    active_sections_.clear();
    active_sections_.clear();
    for (auto& [_, task] : state_.tasks) task = {task.label};
}

InstallerSnapshot InstallerViewModel::snapshot() const {
    InstallerSnapshot result;
    {
        std::scoped_lock lock(mutex_);
        result = state_;
    }
    const auto events = event_log_->snapshot();
    std::unordered_set<std::string> closed_sections;
    for (const auto& event : events) {
        if (!event.section_id.empty() && event.section_action == LogSectionAction::End) {
            closed_sections.insert(event.section_id);
        }
    }
    for (const auto& event : events) {
        if (!event.section_id.empty() && closed_sections.contains(event.section_id) &&
            event.section_action != LogSectionAction::End) {
            continue;
        }
        result.log_lines.push_back(format_log_event(event));
    }
    return result;
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

std::string task_marker(const TaskStatus status) {
    switch (status) {
        case TaskStatus::Pending: return "○";
        case TaskStatus::Running: return " ";
        case TaskStatus::Succeeded: return "✓";
        case TaskStatus::Failed: return "×";
    }
    return " ";
}

void apply_workflow_progress(InstallerViewModel& model, const std::string& task, const std::string& detail) {
    ProgressMapping mapping{TaskStatus::Running, MessageId::StateChecking, -1.0};
    if (map_progress(detail, mapping)) {
        model.update_task(task == "complete" ? "verify" : task, mapping.status,
                          model.localized(mapping.detail), mapping.progress);
        return;
    }
    model.update_task(task, TaskStatus::Running, detail, -1.0);
}

std::string redact_cdk(const std::string& cdk) {
    if (cdk.empty()) return "(none)";
    if (cdk.size() <= 4) return "****";
    return cdk.substr(0, 2) + std::string(cdk.size() - 4, '*') + cdk.substr(cdk.size() - 2);
}

int run_unattended(const std::string& configured_cdk, const TuiInstallAction& install) {
    InstallerViewModel model(false);
    model.begin_install();
    const auto result = install(configured_cdk, model, [] {});
    if (result.success) model.finish_success();
    else model.finish_failure(result.error.empty()
                                  ? message(detect_system_language(), MessageId::StateFailed)
                                  : result.error);
    return result.success ? 0 : 1;
}

namespace {

ftxui::Element project_header(const Language language, const int width) {
    using namespace ftxui;
    const auto centered = [width](Element element) {
        return hbox({filler(), std::move(element), filler()}) |
               size(WIDTH, EQUAL, std::max(1, width - 2));
    };
    return vbox({
        centered(text("██████╗  █████╗  █████╗ ███████╗")),
        centered(text("██╔══██╗██╔══██╗██╔══██╗██╔════╝")),
        centered(text("██████╔╝███████║███████║███████╗")),
        centered(text("██╔══██╗██╔══██║██╔══██║╚════██║")),
        centered(text("██████╔╝██║  ██║██║  ██║███████║")),
        centered(text("╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝")),
        centered(text(message(language, MessageId::Welcome)) | bold | color(Color::Cyan)),
        centered(text("Developed by pur1fying  |  LICENSE: GPL-3.0") | color(Color::GrayLight)),
        centered(text("https://github.com/pur1fying/blue_archive_auto_script") | dim),
        centered(text("Official QQ Group: 658302636") | dim),
    }) | size(WIDTH, EQUAL, std::max(1, width - 2));
}

ftxui::Element task_row(const TaskSnapshot& task) {
    using namespace ftxui;
    Color tint = Color::GrayDark;
    if (task.status == TaskStatus::Running) tint = Color::Cyan;
    else if (task.status == TaskStatus::Succeeded) tint = Color::Green;
    else if (task.status == TaskStatus::Failed) tint = Color::Red;
    Elements row{text(task_marker(task.status)) | color(tint), text("  " + task.label) | bold, filler(),
                 text(task.detail) | dim};
    if (task.progress >= 0) row.push_back(text("  "));
    if (task.progress >= 0) row.push_back(gauge(task.progress) | color(tint) | size(ftxui::WIDTH, ftxui::EQUAL, 18));
    return hbox(std::move(row));
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

ftxui::Element render_setup_view(const InstallerSnapshot&, const Language language, ftxui::Element controls,
                                 const int width, const int height) {
    using namespace ftxui;
    auto content = vbox({
        project_header(language, width),
        separator(),
        text(message(language, MessageId::SetupTitle)) | bold,
        text(message(language, MessageId::GitFallbackHint)) | dim,
        std::move(controls) | flex,
    });
    return std::move(content) | borderRounded |
           size(WIDTH, EQUAL, std::max(1, width)) | size(HEIGHT, EQUAL, std::max(1, height));
}

ftxui::Element render_installation_view(const InstallerSnapshot& snapshot, const Language language,
                                        ftxui::Element footer, const int width, const int height) {
    using namespace ftxui;
    Elements rows;
    for (const auto& id : {"main", "ocr", "deployment", "verify", "uv", "launch"}) {
        rows.push_back(task_row(snapshot.tasks.at(id)));
    }
    const auto visible_lines = static_cast<std::size_t>(std::max(3, height - 23));
    const auto end = snapshot.log_lines.size() - std::min(snapshot.log_scroll, snapshot.log_lines.size());
    const auto start = end > visible_lines ? end - visible_lines : 0;
    Elements logs;
    for (auto index = start; index < end; ++index) logs.push_back(text(snapshot.log_lines[index]) | dim);
    while (logs.size() < visible_lines) logs.push_back(text(""));
    auto content = vbox({
        project_header(language, width),
        separator(),
        vbox(std::move(rows)),
        separator(),
        vbox(std::move(logs)) | border | flex,
        std::move(footer),
    });
    return std::move(content) | borderRounded |
           size(WIDTH, EQUAL, std::max(1, width)) | size(HEIGHT, EQUAL, std::max(1, height));
}

MirrorRecoveryState mirror_failure_recovery(const MirrorRecoveryAction action) {
    return MirrorRecoveryState{
        .use_mirror = true,
        .focus_cdk = action == MirrorRecoveryAction::ReenterCdk,
        .cdk = {},
    };
}

ftxui::Element render_install_target_view(const Language language, ftxui::Element controls,
                                          const std::string& error, const int width,
                                          const int height) {
    using namespace ftxui;
    Elements content{
        project_header(language, width),
        separator(),
        text(message(language, MessageId::InstallDirectoryTitle)) | bold,
        paragraph(message(language, MessageId::InstallDirectoryHint)) | dim,
        std::move(controls) | flex,
    };
    if (!error.empty()) content.push_back(paragraph(error) | color(Color::RedLight));
    return vbox(std::move(content)) | borderRounded |
           size(WIDTH, EQUAL, std::max(1, width)) |
           size(HEIGHT, EQUAL, std::max(1, height));
}

ftxui::Element render_mirror_failure_modal(ftxui::Element background, const Language language,
                                           const std::string& error, ftxui::Element controls,
                                           const int width, const int height) {
    using namespace ftxui;
    auto dialog = vbox({
        text(message(language, MessageId::MirrorFailureTitle)) | bold | color(Color::RedLight),
        separator(),
        paragraph(error) | color(Color::RedLight),
        separator(),
        paragraph(message(language, MessageId::MirrorFailureHint)) | dim,
        separator(),
        std::move(controls),
    }) | borderRounded | size(WIDTH, LESS_THAN, std::max(40, std::min(width - 4, 84)));
    return dbox({std::move(background) | dim, std::move(dialog) | center}) |
           size(WIDTH, EQUAL, std::max(1, width)) |
           size(HEIGHT, EQUAL, std::max(1, height));
}

int run_install_target_tui(const std::filesystem::path& default_root,
                           const TuiTargetAction& select_target) {
    using namespace ftxui;
    configure_utf8_terminal();
    const auto language = detect_system_language();
    auto screen = ScreenInteractive::Fullscreen();
    std::string selected = path_to_utf8(default_root);
    std::string validation_error;
    bool accepted = false;
    auto exit_loop = screen.ExitLoopClosure();

    InputOption path_options = InputOption::Default();
    path_options.multiline = false;
    auto path_input = Input(&selected, selected, path_options);
    auto start = Button(message(language, MessageId::ActionStart), [&] {
        try {
            const auto [success, error] = select_target
                ? select_target(path_from_utf8(selected))
                : std::pair{false, std::string("installation target action is unavailable")};
            if (success) {
                accepted = true;
                exit_loop();
            } else {
                validation_error = error.empty() ? message(language, MessageId::StateFailed) : error;
            }
        } catch (const std::exception& exception) {
            validation_error = exception.what();
        }
    });
    auto controls = Container::Vertical({path_input, start});
    auto renderer = Renderer(controls, [&] {
        auto fields = vbox({hbox({text("  "), path_input->Render() | flex}) | border,
                            separator(), start->Render() | center});
        return render_install_target_view(language, std::move(fields), validation_error,
                                          screen.dimx(), screen.dimy());
    });
    screen.Loop(renderer);
    return accepted ? 0 : 1;
}

int run_tui(const bool setup_required, const std::string& configured_cdk, const TuiInstallAction& install,
            const bool /*auto_exit*/) {
    using namespace ftxui;
    configure_utf8_terminal();
    const auto language = detect_system_language();
    auto screen = ScreenInteractive::Fullscreen();
    InstallerViewModel model(setup_required, language);
    bool use_mirror = !configured_cdk.empty();
    std::string cdk = configured_cdk;
    std::atomic<bool> running{false};
    std::atomic<bool> succeeded{false};
    int active_tab = setup_required ? 0 : 1;
    int failure_controls_tab = 0;
    bool mirror_failure_visible = false;
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
            const auto result = install(chosen_cdk, model, wake);
            if (result.success) {
                succeeded = true;
                model.finish_success();
            } else {
                model.finish_failure(result.error.empty() ? message(language, MessageId::StateFailed)
                                                          : result.error);
            }
            running = false;
            screen.Post([&, success = result.success, failure_kind = result.failure_kind] {
                if (success) {
                    exit_loop();
                } else {
                    mirror_failure_visible = failure_kind == InstallFailureKind::MirrorChyan;
                    failure_controls_tab = mirror_failure_visible ? 1 : 0;
                    if (mirror_failure_visible) cdk.clear();
                    active_tab = 2;
                }
            });
        });
    };

    auto mirror = Checkbox(message(language, MessageId::UseMirror), &use_mirror);
    InputOption password_option = InputOption::Default();
    password_option.password = true;
    password_option.multiline = false;
    auto cdk_input = Input(&cdk, message(language, MessageId::CdkPlaceholder), password_option);
    auto begin = Button(message(language, MessageId::ActionStart), start_install);
    auto retry = Button(message(language, MessageId::ActionRetry), start_install);
    auto close = Button(message(language, MessageId::ActionExit), exit_loop);
    const auto recover = [&](const MirrorRecoveryAction action) {
        if (worker.joinable()) worker.join();
        const auto recovery = mirror_failure_recovery(action);
        use_mirror = recovery.use_mirror;
        cdk = recovery.cdk;
        mirror_failure_visible = false;
        model.return_to_setup();
        active_tab = 0;
        if (recovery.focus_cdk) cdk_input->TakeFocus();
        else mirror->TakeFocus();
    };
    auto reenter_cdk = Button(message(language, MessageId::ActionReenterCdk),
                              [&] { recover(MirrorRecoveryAction::ReenterCdk); });
    auto back_settings = Button(message(language, MessageId::ActionBackSettings),
                                [&] { recover(MirrorRecoveryAction::BackToSettings); });
    auto setup_controls = Container::Vertical({mirror, cdk_input, begin});
    auto install_controls = Renderer([] { return text(""); });
    auto general_failure_controls = Container::Horizontal({retry, close});
    auto mirror_failure_controls = Container::Horizontal({reenter_cdk, back_settings});
    auto result_controls = Container::Tab(
        {general_failure_controls, mirror_failure_controls}, &failure_controls_tab);
    auto controls = Container::Tab({setup_controls, install_controls, result_controls}, &active_tab);

    auto renderer = Renderer(controls, [&] {
        const auto state = model.snapshot();
        if (state.screen == InstallerScreen::Setup) {
            Elements options{mirror->Render()};
            if (use_mirror) options.push_back(hbox({text("CDK  "), cdk_input->Render() | flex}));
            options.push_back(separator());
            options.push_back(begin->Render() | center);
            return render_setup_view(state, language, vbox(std::move(options)) | border | flex,
                                     screen.dimx(), screen.dimy());
        }

        Element footer;
        if (state.screen == InstallerScreen::Failed && !mirror_failure_visible) {
            footer = vbox({text(message(language, MessageId::StateFailed)) | bold | color(Color::Red),
                           paragraph(state.error) | color(Color::RedLight),
                           hbox({retry->Render(), text("  "), close->Render()}) | center});
        } else {
            footer = hbox({gauge(aggregate_progress(state)) | color(Color::Cyan) | flex});
        }
        auto installation = render_installation_view(
            state, language, std::move(footer), screen.dimx(), screen.dimy());
        if (!mirror_failure_visible) return installation;
        auto modal_controls = hbox({reenter_cdk->Render(), text("  "), back_settings->Render()}) | center;
        return render_mirror_failure_modal(std::move(installation), language, state.error,
                                           std::move(modal_controls), screen.dimx(), screen.dimy());
    });

    auto interactive = CatchEvent(renderer, [&](const Event& event) {
        int delta = 0;
        if (event == Event::ArrowUp) delta = 1;
        else if (event == Event::ArrowDown) delta = -1;
        else if (event == Event::PageUp) delta = 10;
        else if (event == Event::PageDown) delta = -10;
        if (delta == 0) return false;
        model.scroll_logs(delta);
        return true;
    });
    if (!setup_required) start_install();
    screen.Loop(interactive);
    if (worker.joinable()) worker.join();
    return succeeded ? 0 : 1;
}

}  // namespace baas_installer
