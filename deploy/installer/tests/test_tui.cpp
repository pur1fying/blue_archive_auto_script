#include "baas_installer/tui.hpp"

#include <iostream>
#include <thread>

int main() {
    const auto redacted = baas_installer::redact_cdk("abcdef1234");
    if (redacted.find("abcdef1234") != std::string::npos || redacted.find("ab") != 0 || redacted.size() != 10) {
        std::cerr << "CDK redaction failed\n"; return 1;
    }

    baas_installer::InstallerViewModel model(true);
    if (model.snapshot().screen != baas_installer::InstallerScreen::Setup) {
        std::cerr << "first run must start on setup screen\n"; return 1;
    }
    model.begin_install();
    std::thread main_progress([&] {
        model.update_task("main", baas_installer::TaskStatus::Running, "正在下载主仓库", 0.25);
    });
    std::thread ocr_progress([&] {
        model.update_task("ocr", baas_installer::TaskStatus::Running, "正在下载 OCR", 0.50);
    });
    main_progress.join();
    ocr_progress.join();
    auto running = model.snapshot();
    if (running.screen != baas_installer::InstallerScreen::Installing || running.tasks.size() < 5) {
        std::cerr << "install screen must expose all task rows\n"; return 1;
    }
    if (running.tasks.at("main").progress != 0.25 || running.tasks.at("ocr").progress != 0.50) {
        std::cerr << "parallel task progress was lost\n"; return 1;
    }
    model.update_task("main", baas_installer::TaskStatus::Succeeded, "主仓库就绪", 1.0);
    model.update_task("deployment", baas_installer::TaskStatus::Running, "部署主仓库", 0.40);
    model.update_task("ocr", baas_installer::TaskStatus::Succeeded, "OCR 就绪", 1.0);
    model.update_task("deployment", baas_installer::TaskStatus::Succeeded, "主仓库与 OCR 已部署", 1.0);
    model.update_task("uv", baas_installer::TaskStatus::Running, "同步 Python 依赖", 0.75);
    model.finish_success();
    if (model.snapshot().screen != baas_installer::InstallerScreen::Succeeded) {
        std::cerr << "successful install must reach terminal success screen\n"; return 1;
    }

    baas_installer::InstallerViewModel failed(false);
    failed.begin_install();
    failed.finish_failure("Git 下载失败");
    const auto failure = failed.snapshot();
    if (failure.screen != baas_installer::InstallerScreen::Failed || failure.error != "Git 下载失败") {
        std::cerr << "failure screen must retain actionable error\n"; return 1;
    }

    baas_installer::InstallerViewModel mapped(false);
    baas_installer::apply_workflow_progress(mapped, "main", "downloading");
    baas_installer::apply_workflow_progress(mapped, "ocr", "ready; waiting for parallel task");
    baas_installer::apply_workflow_progress(mapped, "deployment", "deploying OCR repository");
    baas_installer::apply_workflow_progress(mapped, "uv", "synchronizing dependencies");
    const auto mapped_state = mapped.snapshot();
    if (mapped_state.tasks.at("main").status != baas_installer::TaskStatus::Running ||
        mapped_state.tasks.at("main").detail != "正在下载" ||
        mapped_state.tasks.at("ocr").status != baas_installer::TaskStatus::Succeeded ||
        mapped_state.tasks.at("deployment").progress <= 0.5 ||
        mapped_state.tasks.at("uv").status != baas_installer::TaskStatus::Running) {
        std::cerr << "workflow progress was not mapped to visible task state\n"; return 1;
    }
    if (!baas_installer::configure_utf8_terminal()) {
        std::cerr << "terminal UTF-8/VT initialization failed\n"; return 1;
    }
    bool unattended_called = false;
    const int unattended_exit = baas_installer::run_unattended("", [&](const std::string&, auto& unattended_model, const auto&) {
        unattended_called = true;
        unattended_model.update_task("main", baas_installer::TaskStatus::Succeeded, "done", 1.0);
        return std::pair{true, std::string{}};
    });
    if (!unattended_called || unattended_exit != 0) {
        std::cerr << "unattended verification must execute the install without a terminal loop\n"; return 1;
    }
    return 0;
}
