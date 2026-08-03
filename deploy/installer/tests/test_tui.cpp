#include "baas_installer/tui.hpp"

#include <cmath>
#include <iostream>
#include <thread>

#include <ftxui/dom/elements.hpp>
#include <ftxui/dom/node.hpp>
#include <ftxui/screen/screen.hpp>
#include <ftxui/screen/string.hpp>

namespace {

bool contains(const std::vector<std::string>& lines, const std::string& needle) {
    for (const auto& line : lines) if (line.find(needle) != std::string::npos) return true;
    return false;
}

std::string screen_text(const ftxui::Screen& screen) {
    std::string result;
    for (int y = 0; y < screen.dimy(); ++y) {
        for (int x = 0; x < screen.dimx(); ++x) result += screen.at(x, y);
        result.push_back('\n');
    }
    return result;
}

double horizontal_center(const ftxui::Screen& screen, const std::string& needle) {
    const auto first_visible = needle.find_first_not_of(' ');
    const auto visible = first_visible == std::string::npos ? needle : needle.substr(first_visible);
    for (int y = 0; y < screen.dimy(); ++y) {
        std::string row;
        for (int x = 0; x < screen.dimx(); ++x) {
            const auto& cell = screen.at(x, y);
            row += cell.empty() ? " " : cell;
        }
        const auto position = row.find(visible);
        if (position != std::string::npos) {
            const auto canvas_column = ftxui::string_width(row.substr(0, position)) -
                                       static_cast<int>(first_visible);
            return static_cast<double>(canvas_column) +
                   static_cast<double>(ftxui::string_width(needle)) / 2.0;
        }
    }
    return -1;
}

}  // namespace

int main() {
    const auto redacted = baas_installer::redact_cdk("abcdef1234");
    if (redacted.find("abcdef1234") != std::string::npos || redacted.find("ab") != 0 || redacted.size() != 10) {
        std::cerr << "CDK redaction failed\n"; return 1;
    }

    baas_installer::InstallerViewModel english(true, baas_installer::Language::English);
    baas_installer::InstallerViewModel chinese(true, baas_installer::Language::SimplifiedChinese);
    if (english.snapshot().tasks.at("main").label != "Main repository" ||
        chinese.snapshot().tasks.at("main").label != "主仓库") {
        std::cerr << "task labels must follow the selected system language\n"; return 1;
    }
    if (baas_installer::task_marker(baas_installer::TaskStatus::Running) != " ") {
        std::cerr << "running tasks must not use an animated spinner or glyph\n"; return 1;
    }

    auto english_screen = ftxui::Screen::Create(ftxui::Dimension::Fixed(100), ftxui::Dimension::Fixed(40));
    auto english_view = baas_installer::render_setup_view(
        english.snapshot(), baas_installer::Language::English, ftxui::text("controls"), 100, 40);
    ftxui::Render(english_screen, english_view);
    const auto english_rendered = screen_text(english_screen);
    if (english_screen.at(0, 0) == " " || english_screen.at(99, 0) == " " ||
        english_screen.at(0, 39) == " " || english_screen.at(99, 39) == " " ||
        english_rendered.find("██████╗  █████╗  █████╗ ███████╗") == std::string::npos ||
        english_rendered.find("██╔══██╗██╔══██╗██╔══██╗██╔════╝") == std::string::npos ||
        english_rendered.find("██████╔╝███████║███████║███████╗") == std::string::npos ||
        english_rendered.find("██╔══██╗██╔══██║██╔══██║╚════██║") == std::string::npos ||
        english_rendered.find("██████╔╝██║  ██║██║  ██║███████║") == std::string::npos ||
        english_rendered.find("╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝") == std::string::npos ||
        english_rendered.find("    ____  ___    ___   _____") != std::string::npos ||
        english_rendered.find("Welcome to BlueArchive Auto Script!") == std::string::npos ||
        english_rendered.find("Developed by pur1fying") == std::string::npos ||
        english_rendered.find("LICENSE: GPL-3.0") == std::string::npos ||
        english_rendered.find("https://github.com/pur1fying/blue_archive_auto_script") == std::string::npos ||
        english_rendered.find("Official QQ Group: 658302636") == std::string::npos ||
        english_rendered.find("欢迎使用蔚蓝档案自动脚本！") != std::string::npos) {
        std::cerr << "English setup renderer did not fill the viewport or restore project identity\n";
        return 1;
    }
    const auto title_top_center = horizontal_center(english_screen, "██████╗  █████╗  █████╗ ███████╗");
    const auto title_middle_center = horizontal_center(english_screen, "██╔══██╗██╔══██║██╔══██║╚════██║");
    const auto title_bottom_center = horizontal_center(english_screen, "╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝");
    const auto project_url_center = horizontal_center(
        english_screen, "https://github.com/pur1fying/blue_archive_auto_script");
    if (title_top_center < 0 || title_middle_center < 0 || title_bottom_center < 0 || project_url_center < 0 ||
        std::abs(title_top_center - title_middle_center) > 0.5 ||
        std::abs(title_top_center - title_bottom_center) > 0.5 ||
        std::abs(title_top_center - project_url_center) > 0.5) {
        std::cerr << "every header line must be centered independently: top=" << title_top_center
                  << " bottom=" << title_bottom_center << " url=" << project_url_center << '\n';
        return 1;
    }

    auto chinese_screen = ftxui::Screen::Create(ftxui::Dimension::Fixed(100), ftxui::Dimension::Fixed(40));
    auto chinese_view = baas_installer::render_setup_view(
        chinese.snapshot(), baas_installer::Language::SimplifiedChinese, ftxui::text("controls"), 100, 40);
    ftxui::Render(chinese_screen, chinese_view);
    const auto chinese_rendered = screen_text(chinese_screen);
    if (chinese_rendered.find("欢迎使用蔚蓝档案自动脚本！") == std::string::npos ||
        chinese_rendered.find("Welcome to BlueArchive Auto Script!") != std::string::npos) {
        std::cerr << "Chinese setup renderer did not select the localized welcome\n";
        return 1;
    }

    english.begin_install();
    std::thread main_progress([&] {
        english.update_task("main", baas_installer::TaskStatus::Running, "Downloading", 0.25);
    });
    std::thread ocr_progress([&] {
        english.update_task("ocr", baas_installer::TaskStatus::Running, "Downloading", 0.50);
    });
    main_progress.join();
    ocr_progress.join();
    auto running = english.snapshot();
    if (running.screen != baas_installer::InstallerScreen::Installing || running.tasks.size() < 6 ||
        running.tasks.at("main").progress != 0.25 || running.tasks.at("ocr").progress != 0.50) {
        std::cerr << "parallel task progress was lost\n"; return 1;
    }

    // Carriage-return progress updates replace only the previous line from the
    // same task/backend. Interleaved OCR output must remain visible.
    english.append_process_chunk("main", "git", "Receiving 10%\r");
    english.append_process_chunk("ocr", "mirror", "OCR download\n");
    english.append_process_chunk("main", "git", "Receiving 20%\r");
    auto logs = english.snapshot().log_lines;
    if (contains(logs, "Receiving 10%") || !contains(logs, "Receiving 20%") || !contains(logs, "OCR download")) {
        std::cerr << "interleaved PTY progress replacement is incorrect\n"; return 1;
    }
    for (int i = 0; i < 24; ++i) {
        const auto index = (i < 10 ? "0" : "") + std::to_string(i);
        english.append_process_chunk("uv", "uv", "history-" + index + "\n");
    }
    if (english.snapshot().log_lines.size() < 26) {
        std::cerr << "the unified log must retain full history\n"; return 1;
    }
    english.scroll_logs(5);
    if (english.snapshot().log_scroll != 5) {
        std::cerr << "log view must support scrolling away from the tail\n"; return 1;
    }

    auto installation_screen = ftxui::Screen::Create(ftxui::Dimension::Fixed(100), ftxui::Dimension::Fixed(40));
    auto installation_view = baas_installer::render_installation_view(
        english.snapshot(), baas_installer::Language::English, ftxui::text("footer"), 100, 40);
    ftxui::Render(installation_screen, installation_view);
    const auto installation_rendered = screen_text(installation_screen);
    if (installation_screen.at(0, 0) == " " || installation_screen.at(99, 0) == " " ||
        installation_screen.at(0, 39) == " " || installation_screen.at(99, 39) == " " ||
        installation_rendered.find("history-02") == std::string::npos ||
        installation_rendered.find("history-18") == std::string::npos ||
        installation_rendered.find("history-01") != std::string::npos ||
        installation_rendered.find("history-19") != std::string::npos) {
        std::cerr << "installation renderer did not fill the viewport or derive log capacity from its height\n";
        return 1;
    }

    baas_installer::apply_workflow_progress(english, "main", "downloading");
    baas_installer::apply_workflow_progress(english, "ocr", "already current");
    baas_installer::apply_workflow_progress(english, "deployment", "deploying OCR repository");
    baas_installer::apply_workflow_progress(english, "uv", "dependencies synchronized");
    const auto mapped = english.snapshot();
    if (mapped.tasks.at("main").detail != "Downloading" ||
        mapped.tasks.at("ocr").status != baas_installer::TaskStatus::Succeeded ||
        mapped.tasks.at("deployment").progress <= 0.5 ||
        mapped.tasks.at("uv").status != baas_installer::TaskStatus::Succeeded) {
        std::cerr << "workflow protocol events were not mapped exactly/localized\n"; return 1;
    }

    english.finish_success();
    const auto success = english.snapshot();
    if (!success.exit_requested || success.screen != baas_installer::InstallerScreen::Installing) {
        std::cerr << "successful launch must request immediate exit without a success page\n"; return 1;
    }

    baas_installer::InstallerViewModel failed(false, baas_installer::Language::English);
    failed.begin_install();
    failed.finish_failure("Git download failed");
    const auto failure = failed.snapshot();
    if (failure.screen != baas_installer::InstallerScreen::Failed || failure.error != "Git download failed") {
        std::cerr << "failure screen must retain actionable error\n"; return 1;
    }

    if (!baas_installer::configure_utf8_terminal()) {
        std::cerr << "terminal UTF-8/VT initialization failed\n"; return 1;
    }
    bool unattended_called = false;
    const int unattended_exit = baas_installer::run_unattended("", [&](const std::string&, auto& model, const auto&) {
        unattended_called = true;
        model.update_task("main", baas_installer::TaskStatus::Succeeded, "done", 1.0);
        return std::pair{true, std::string{}};
    });
    if (!unattended_called || unattended_exit != 0) {
        std::cerr << "unattended verification must execute the install without a terminal loop\n"; return 1;
    }
    return 0;
}
