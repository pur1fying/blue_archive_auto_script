#include "baas_installer/config.hpp"
#include "baas_installer/git.hpp"
#include "baas_installer/mirrorchyan.hpp"
#include "baas_installer/paths.hpp"
#include "baas_installer/process.hpp"
#include "baas_installer/sources.hpp"
#include "baas_installer/tui.hpp"
#include "baas_installer/uv_environment.hpp"
#include "baas_installer/workflow.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>

namespace {
std::string ocr_revision() {
#ifdef _WIN32
    return "windows-x64";
#elif defined(__APPLE__) && (defined(__aarch64__) || defined(__arm64__))
    return "macos-arm64";
#elif defined(__APPLE__)
    return "macos-x64";
#else
    return "linux-x64";
#endif
}

std::string read_text(const std::filesystem::path& path) {
    std::ifstream input(path, std::ios::binary);
    return {std::istreambuf_iterator<char>(input), {}};
}

void append_log(const std::filesystem::path& path, const std::string& message) {
    std::error_code ignored;
    std::filesystem::create_directories(path.parent_path(), ignored);
    std::ofstream output(path, std::ios::app);
    output << message << '\n';
}
}

int main(int argc, char* argv[]) {
    baas_installer::configure_utf8_terminal();
    const auto executable = baas_installer::current_executable_path();
    const auto paths = baas_installer::InstallPaths::from_executable(executable);
    if (argc > 1 && std::string(argv[1]) == "--help") {
        std::cout << "BAAS portable installer\n\nOptions:\n  --help       show this help\n  --print-root print the executable-relative install root\n";
        return 0;
    }
    if (argc > 1 && std::string(argv[1]) == "--print-root") { std::cout << paths.root.string() << '\n'; return 0; }
    bool auto_exit = false;
    for (int index = 1; index < argc; ++index) if (std::string(argv[index]) == "--auto-exit") auto_exit = true;
    const bool first_start = !std::filesystem::exists(paths.setup_toml);
    auto config = baas_installer::load_config(paths);
    const auto log_path = paths.logs_dir / "installer.log";
    baas_installer::set_default_process_log(log_path);
    append_log(log_path, "installer started");
    const auto install = [&](const std::string& selected_cdk, baas_installer::InstallerViewModel& model,
                             const std::function<void()>& wake) -> std::pair<bool, std::string> {
        config.mirrorc_cdk = selected_cdk;
        baas_installer::WorkflowServices services;
        std::string prepared_main_sha;
        std::string prepared_ocr_sha;
        services.progress = [&](const std::string& task, const std::string& detail) {
            baas_installer::apply_workflow_progress(model, task, detail);
            append_log(log_path, "[" + task + "] " + detail);
            wake();
        };
        services.prepare_main = [&](baas_installer::InstallTransaction& transaction, std::string& error) {
        if (!config.mirrorc_cdk.empty()) {
            const auto response_path = transaction.staging_root() / "mirrorchyan-response.json";
            const auto request = baas_installer::mirror_latest_url(config.mirrorc_cdk, config.main_sha, config.channel);
            if (baas_installer::run_process({"curl", "--fail", "--silent", "--show-error", "--connect-timeout", "5", "--output", response_path.string(), request}) != 0) {
                error = "MirrorChyan validation request failed";
                return false;
            }
            const auto release = baas_installer::parse_mirror_response(read_text(response_path));
            if (release.status != baas_installer::CdkStatus::Valid) {
                error = "MirrorChyan CDK was rejected or returned an invalid package";
                return false;
            }
            const auto archive = transaction.staging_root() / "main-mirror-package.zip";
            if (!baas_installer::download_mirror_package(release, archive, error)) return false;
            const auto unpacked = transaction.staging_root() / "mirror-unpacked";
            std::error_code ignored;
            std::filesystem::create_directories(unpacked);
            if (baas_installer::run_process({"tar", "-xf", archive.string(), "-C", unpacked.string()}) != 0) {
                error = "MirrorChyan package extraction failed";
                return false;
            }
            std::filesystem::path package_root;
            for (const auto& entry : std::filesystem::recursive_directory_iterator(unpacked, ignored)) {
                if (ignored) break;
                if (entry.is_regular_file() && entry.path().filename() == "main.py") {
                    package_root = entry.path().parent_path();
                    break;
                }
            }
            if (package_root.empty()) { error = "MirrorChyan package did not contain main.py"; return false; }
            std::filesystem::rename(package_root, transaction.main_staging_path(), ignored);
            if (ignored) { error = "could not stage extracted MirrorChyan package"; return false; }
            prepared_main_sha = release.version;
            return true;
        }
        const auto result = baas_installer::clone_repository(
            baas_installer::default_sources(baas_installer::SourceKind::MainGit, config), transaction.main_staging_path());
        if (!result.success) { error = "main repository: " + result.error; return false; }
        prepared_main_sha = baas_installer::repository_head(transaction.main_staging_path());
        return true;
        };
        services.prepare_ocr = [&](baas_installer::InstallTransaction& transaction, std::string& error) {
        const auto result = baas_installer::clone_repository(
            baas_installer::default_sources(baas_installer::SourceKind::OcrGit, config), transaction.ocr_staging_path(), ocr_revision());
        if (!result.success) { error = "OCR repository: " + result.error; return false; }
        prepared_ocr_sha = baas_installer::repository_head(transaction.ocr_staging_path());
        return true;
        };
        services.on_prepared = [&] {
            config.main_sha = prepared_main_sha;
            config.ocr_sha = prepared_ocr_sha;
        };
        services.verify_deployment = [](const baas_installer::InstallPaths& current, const baas_installer::InstallerConfig&, std::string& error) {
        if (!std::filesystem::exists(current.root / "main.py")) { error = "main repository did not contain main.py"; return false; }
        const auto ocr = current.root / "core" / "ocr" / "baas_ocr_client" / "bin";
        if (!std::filesystem::is_directory(ocr) || std::filesystem::is_empty(ocr)) { error = "OCR repository placement is empty"; return false; }
        return true;
        };
        services.sync_uv = [](const baas_installer::InstallPaths& current, const baas_installer::InstallerConfig& settings, std::string& error) {
        return baas_installer::sync_portable_uv(current, settings, error);
        };
        const auto result = baas_installer::install_or_update(config, paths, services);
        if (!result.success) {
            append_log(log_path, "installer failed: " + result.error);
            return {false, result.error};
        }
        if (!auto_exit) {
            baas_installer::apply_workflow_progress(model, "launch", "launching BAAS");
            wake();
#ifdef _WIN32
            auto python = paths.venv_dir / "Scripts" / "pythonw.exe";
            if (!std::filesystem::exists(python)) python = paths.venv_dir / "Scripts" / "python.exe";
#else
            auto python = paths.venv_dir / "bin" / "python";
#endif
            if (!config.uses_portable_runtime()) python = config.runtime_path;
            auto environment = baas_installer::make_uv_environment(paths, config).variables;
            environment["VIRTUAL_ENV"] = paths.venv_dir.string();
            if (!std::filesystem::exists(python) || !std::filesystem::exists(paths.root / "window.py") ||
                !baas_installer::launch_detached({python.string(), (paths.root / "window.py").string()}, environment, paths.root)) {
                const std::string error = "installation succeeded, but BAAS could not be launched";
                model.update_task("launch", baas_installer::TaskStatus::Failed, "BAAS 启动失败", 0.0);
                append_log(log_path, error);
                return {false, error};
            }
            baas_installer::apply_workflow_progress(model, "launch", "BAAS launched");
            wake();
        }
        append_log(log_path, "installer completed");
        return {true, std::string{}};
    };
    if (auto_exit) return baas_installer::run_unattended(config.mirrorc_cdk, install);
    return baas_installer::run_tui(first_start, config.mirrorc_cdk, install);
}
