#include "baas_installer/tui.hpp"

#include <iostream>
#include <thread>

namespace {

bool contains(const std::vector<std::string>& lines, const std::string& needle) {
    for (const auto& line : lines) if (line.find(needle) != std::string::npos) return true;
    return false;
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
    for (int i = 0; i < 24; ++i) english.append_process_chunk("uv", "uv", "history " + std::to_string(i) + "\n");
    if (english.snapshot().log_lines.size() < 26) {
        std::cerr << "the unified log must retain full history\n"; return 1;
    }
    english.scroll_logs(5);
    if (english.snapshot().log_scroll != 5) {
        std::cerr << "log view must support scrolling away from the tail\n"; return 1;
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
