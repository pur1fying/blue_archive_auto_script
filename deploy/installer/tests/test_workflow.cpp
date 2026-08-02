#include "baas_installer/workflow.hpp"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <mutex>
#include <vector>

namespace fs = std::filesystem;
static void write(const fs::path& path, const std::string& text) { fs::create_directories(path.parent_path()); std::ofstream(path) << text; }

int main() {
    const auto fixture = fs::temp_directory_path() / "baas-installer-workflow";
    std::error_code ignored; fs::remove_all(fixture, ignored);
    auto paths = baas_installer::InstallPaths::from_executable(fixture / "install" / "BlueArchiveAutoScript.exe");
    std::vector<std::string> events;
    std::mutex event_mutex;
    baas_installer::WorkflowServices services;
    services.prepare_main = [&](auto& transaction) {
        write(transaction.main_staging_path() / "main.txt", "main");
        { std::lock_guard lock(event_mutex); events.push_back("prepared-main"); }
        return baas_installer::PreparedRepository{
            .success = true, .mode = baas_installer::RepositoryMode::Full, .backend = "git-cli", .version = "main-v2",
            .apply = [&](auto& current, std::string&) { std::lock_guard lock(event_mutex); events.push_back("applied-main"); current.deploy_main(); return true; }};
    };
    services.prepare_ocr = [&](auto& transaction) {
        write(transaction.ocr_staging_path() / "ocr.txt", "ocr");
        { std::lock_guard lock(event_mutex); events.push_back("prepared-ocr"); }
        return baas_installer::PreparedRepository{
            .success = true, .mode = baas_installer::RepositoryMode::Full, .backend = "git-cli", .version = "ocr-v2",
            .apply = [&](auto& current, std::string&) { std::lock_guard lock(event_mutex); events.push_back("applied-ocr"); current.deploy_ocr(); return true; }};
    };
    services.verify_deployment = [&](const auto& current, const auto&, std::string&) { const bool ok=fs::exists(current.root/"main.txt") && fs::exists(current.root/"core/ocr/baas_ocr_client/bin/ocr.txt"); std::lock_guard lock(event_mutex); events.push_back("verified"); return ok; };
    services.sync_uv = [&](const auto&, const auto&, std::string&) { std::lock_guard lock(event_mutex); events.push_back("uv"); return true; };
    services.progress = [&](const std::string& task, const std::string& detail) {
        std::lock_guard lock(event_mutex);
        events.push_back("progress:" + task + ":" + detail);
    };
    baas_installer::InstallerConfig config;
    const auto result = baas_installer::install_or_update(config, paths, services);
    const auto contains = [&](const std::string& wanted) { return std::find(events.begin(), events.end(), wanted) != events.end(); };
    const auto main_applied = std::find(events.begin(), events.end(), "applied-main");
    const auto ocr_applied = std::find(events.begin(), events.end(), "applied-ocr");
    const bool order = result.success && contains("verified") && contains("uv") && main_applied < ocr_applied &&
        config.main_sha == "main-v2" && config.ocr_sha == "ocr-v2" &&
        contains("progress:verify:verifying deployment") && contains("progress:verify:deployment verified") &&
        contains("progress:uv:synchronizing dependencies") && contains("progress:uv:dependencies synchronized") &&
        fs::exists(paths.root / "core/ocr/baas_ocr_client/bin/.baas-installer-managed.json");
    if (!order) { std::cerr << "workflow order failed\n"; return 1; }

    auto failing_paths = baas_installer::InstallPaths::from_executable(fixture / "rollback" / "BlueArchiveAutoScript.exe");
    write(failing_paths.root / "main.txt", "old-main");
    write(failing_paths.root / "core/ocr/baas_ocr_client/bin/ocr.txt", "old-ocr");
    baas_installer::InstallerConfig failing_config;
    failing_config.main_sha = "main-old";
    failing_config.ocr_sha = "ocr-old";
    baas_installer::save_config_atomic(failing_config, failing_paths);
    baas_installer::WorkflowServices failing = services;
    failing.prepare_main = [&](auto& transaction) {
        write(transaction.main_staging_path() / "main.txt", "new-main");
        return baas_installer::PreparedRepository{.success = true, .mode = baas_installer::RepositoryMode::Full,
            .backend = "mirrorchyan", .version = "main-new",
            .apply = [](auto& current, std::string&) { current.deploy_main(); return true; }};
    };
    failing.prepare_ocr = [&](auto& transaction) {
        write(transaction.ocr_staging_path() / "ocr.txt", "new-ocr");
        return baas_installer::PreparedRepository{.success = true, .mode = baas_installer::RepositoryMode::Full,
            .backend = "mirrorchyan", .version = "ocr-new",
            .apply = [](auto& current, std::string&) { current.deploy_ocr(); return true; }};
    };
    failing.verify_deployment = [](const auto&, const auto&, std::string&) { return true; };
    failing.sync_uv = [](const auto&, const auto&, std::string& error) { error = "forced uv failure"; return false; };
    const auto failed = baas_installer::install_or_update(failing_config, failing_paths, failing);
    const auto persisted = baas_installer::load_config(failing_paths);
    if (failed.success || failing_config.main_sha != "main-old" || failing_config.ocr_sha != "ocr-old" ||
        persisted.main_sha != "main-old" || persisted.ocr_sha != "ocr-old" ||
        std::ifstream(failing_paths.root / "main.txt").get() != 'o' ||
        std::ifstream(failing_paths.root / "core/ocr/baas_ocr_client/bin/ocr.txt").get() != 'o') {
        std::cerr << "failed workflow did not roll back files and atomic version state\n";
        return 1;
    }
    fs::remove_all(fixture, ignored);
    return 0;
}
