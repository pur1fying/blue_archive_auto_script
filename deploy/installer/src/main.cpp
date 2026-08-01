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
}

int main(int argc, char* argv[]) {
    const auto executable = baas_installer::current_executable_path();
    const auto paths = baas_installer::InstallPaths::from_executable(executable);
    if (argc > 1 && std::string(argv[1]) == "--help") {
        std::cout << "BAAS portable installer\n\nOptions:\n  --help       show this help\n  --print-root print the executable-relative install root\n";
        return 0;
    }
    if (argc > 1 && std::string(argv[1]) == "--print-root") { std::cout << paths.root.string() << '\n'; return 0; }
    const bool first_start = !std::filesystem::exists(paths.setup_toml);
    auto config = baas_installer::load_config(paths);
    baas_installer::print_tui_banner();
    baas_installer::print_progress("root", "ready", paths.root.string());
    if (first_start) {
        if (baas_installer::ask_yes_no("Do you have a MirrorChyan CDK?")) {
            config.mirrorc_cdk = baas_installer::ask_secret("MirrorChyan CDK (masked): ");
            baas_installer::print_progress("MirrorChyan", "configured", baas_installer::redact_cdk(config.mirrorc_cdk));
        } else baas_installer::print_progress("MirrorChyan", "not selected", "Git source fallback will be used");
        // The install workflow will make the final atomic write after all
        // staged work is successful; retaining this in-memory answer prevents
        // a cancelled first run from creating a half-configured installation.
    }
    baas_installer::WorkflowServices services;
    std::string prepared_main_sha;
    std::string prepared_ocr_sha;
    services.progress = [](const std::string& task, const std::string& detail) {
        baas_installer::print_progress(task, "working", detail);
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
        baas_installer::print_progress("installer", "failed", result.error);
        return 1;
    }
    baas_installer::print_progress("installer", "complete", "BAAS is ready to launch");
    return 0;
}
