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
    bool setup_seen_before_prepare = false;
    baas_installer::WorkflowServices services;
    services.prepare_main = [&](auto& transaction) {
        const auto persisted = baas_installer::load_config(paths);
        setup_seen_before_prepare = fs::exists(paths.setup_toml) &&
            persisted.mirrorc_cdk == "selected-cdk" &&
            persisted.main_sha == "main-v1" && persisted.ocr_sha == "ocr-v1";
        write(transaction.main_staging_path() / "main.txt", "main");
        { std::lock_guard lock(event_mutex); events.push_back("prepared-main"); }
        return baas_installer::PreparedRepository{
            .success = true, .mode = baas_installer::RepositoryMode::Full, .backend = "git-cli", .version = "main-v2", .revision = "master",
            .apply = [&](auto& current, std::string&) { std::lock_guard lock(event_mutex); events.push_back("applied-main"); current.deploy_main(); return true; }};
    };
    services.prepare_ocr = [&](auto& transaction) {
        write(transaction.ocr_staging_path() / "ocr.txt", "ocr");
        { std::lock_guard lock(event_mutex); events.push_back("prepared-ocr"); }
        return baas_installer::PreparedRepository{
            .success = true, .mode = baas_installer::RepositoryMode::Full, .backend = "git-cli", .version = "0123456789012345678901234567890123456789", .revision = "windows-x64",
            .apply = [&](auto& current, std::string&) { std::lock_guard lock(event_mutex); events.push_back("applied-ocr"); current.deploy_ocr(); return true; }};
    };
    services.verify_deployment = [&](const auto& current, const auto&, std::string&) { const bool ok=fs::exists(current.root/"main.txt") && fs::exists(current.root/"core/ocr/baas_ocr_client/bin/ocr.txt"); std::lock_guard lock(event_mutex); events.push_back("verified"); return ok; };
    services.sync_uv = [&](const auto&, const auto&, std::string&) { std::lock_guard lock(event_mutex); events.push_back("uv"); return true; };
    services.progress = [&](const std::string& task, const std::string& detail) {
        std::lock_guard lock(event_mutex);
        events.push_back("progress:" + task + ":" + detail);
    };
    baas_installer::InstallerConfig config;
    config.mirrorc_cdk = "selected-cdk";
    config.main_sha = "main-v1";
    config.ocr_sha = "ocr-v1";
    const auto result = baas_installer::install_or_update(config, paths, services);
    const auto contains = [&](const std::string& wanted) { return std::find(events.begin(), events.end(), wanted) != events.end(); };
    const auto main_applied = std::find(events.begin(), events.end(), "applied-main");
    const auto ocr_applied = std::find(events.begin(), events.end(), "applied-ocr");
    const auto marker_path = paths.root / "core/ocr/baas_ocr_client/bin/.baas-installer-managed.json";
    std::ifstream marker_input(marker_path);
    const std::string marker{std::istreambuf_iterator<char>(marker_input), {}};
    const bool order = result.success && setup_seen_before_prepare && contains("verified") && contains("uv") && main_applied < ocr_applied &&
        config.main_sha == "main-v2" && config.ocr_sha == "0123456789012345678901234567890123456789" &&
        contains("progress:verify:verifying deployment") && contains("progress:verify:deployment verified") &&
        contains("progress:uv:synchronizing dependencies") && contains("progress:uv:dependencies synchronized") &&
        marker.find("\"branch\":\"windows-x64\"") != std::string::npos &&
        marker.find("\"commit\":\"0123456789012345678901234567890123456789\"") != std::string::npos;
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
            .backend = "mirrorchyan", .version = "main-new", .revision = "master",
            .apply = [](auto& current, std::string&) { current.deploy_main(); return true; }};
    };
    failing.prepare_ocr = [&](auto& transaction) {
        write(transaction.ocr_staging_path() / "ocr.txt", "new-ocr");
        return baas_installer::PreparedRepository{.success = true, .mode = baas_installer::RepositoryMode::Full,
            .backend = "mirrorchyan", .version = "ocr-new", .revision = "windows-x64",
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

    auto commit_failure_paths = baas_installer::InstallPaths::from_executable(
        fixture / "commit-failure" / "BlueArchiveAutoScript.exe");
    write(commit_failure_paths.root / "main.txt", "old-main");
    write(commit_failure_paths.root / "core/ocr/baas_ocr_client/bin/ocr.txt", "old-ocr");
    baas_installer::InstallerConfig commit_failure_config;
    commit_failure_config.main_sha = "main-old";
    commit_failure_config.ocr_sha = "ocr-old";
    baas_installer::save_config_atomic(commit_failure_config, commit_failure_paths);
    baas_installer::WorkflowServices commit_failure = services;
    commit_failure.prepare_main = [&](auto& transaction) {
        write(transaction.main_staging_path() / "main.txt", "new-main");
        return baas_installer::PreparedRepository{.success = true, .mode = baas_installer::RepositoryMode::Full,
            .backend = "git-cli", .version = "main-new", .revision = "master",
            .apply = [](auto& current, std::string&) {
                current.deploy_main();
                current.add_commit_action([] {});
                return true;
            }};
    };
    commit_failure.prepare_ocr = [&](auto& transaction) {
        write(transaction.ocr_staging_path() / "ocr.txt", "new-ocr");
        return baas_installer::PreparedRepository{.success = true, .mode = baas_installer::RepositoryMode::Full,
            .backend = "git-cli", .version = "ocr-new", .revision = "windows-x64",
            .apply = [](auto& current, std::string&) {
                current.deploy_ocr();
                current.add_commit_action([] { throw std::runtime_error("forced finalizer failure"); });
                return true;
            }};
    };
    commit_failure.verify_deployment = [](const auto&, const auto&, std::string&) { return true; };
    commit_failure.sync_uv = [](const auto&, const auto&, std::string&) { return true; };
    const auto commit_failed = baas_installer::install_or_update(
        commit_failure_config, commit_failure_paths, commit_failure);
    const auto commit_failure_persisted = baas_installer::load_config(commit_failure_paths);
    if (commit_failed.success || commit_failure_config.main_sha != "main-old" ||
        commit_failure_config.ocr_sha != "ocr-old" || commit_failure_persisted.main_sha != "main-old" ||
        commit_failure_persisted.ocr_sha != "ocr-old" ||
        std::ifstream(commit_failure_paths.root / "main.txt").get() != 'o' ||
        std::ifstream(commit_failure_paths.root / "core/ocr/baas_ocr_client/bin/ocr.txt").get() != 'o') {
        std::cerr << "commit-action failure did not preserve files and durable version state\n";
        return 1;
    }

    auto maintenance_failure_paths = baas_installer::InstallPaths::from_executable(
        fixture / "maintenance-failure" / "BlueArchiveAutoScript.exe");
    write(maintenance_failure_paths.root / "main.txt", "old-main");
    write(maintenance_failure_paths.root / "core/ocr/baas_ocr_client/bin/ocr.txt", "old-ocr");
    baas_installer::InstallerConfig maintenance_failure_config;
    maintenance_failure_config.main_sha = "main-old";
    maintenance_failure_config.ocr_sha = "ocr-old";
    baas_installer::save_config_atomic(maintenance_failure_config, maintenance_failure_paths);
    baas_installer::WorkflowServices maintenance_failure = services;
    maintenance_failure.prepare_main = [&](auto& transaction) {
        write(transaction.main_staging_path() / "main.txt", "new-main");
        return baas_installer::PreparedRepository{.success = true, .mode = baas_installer::RepositoryMode::Full,
            .backend = "git-cli", .version = "main-new", .revision = "master",
            .apply = [](auto& current, std::string&) {
                current.deploy_main();
                current.add_post_commit_action([] { throw std::runtime_error("forced maintenance failure"); });
                return true;
            }};
    };
    maintenance_failure.prepare_ocr = [&](auto& transaction) {
        write(transaction.ocr_staging_path() / "ocr.txt", "new-ocr");
        return baas_installer::PreparedRepository{.success = true, .mode = baas_installer::RepositoryMode::Full,
            .backend = "git-cli", .version = "ocr-new", .revision = "windows-x64",
            .apply = [](auto& current, std::string&) { current.deploy_ocr(); return true; }};
    };
    maintenance_failure.verify_deployment = [](const auto&, const auto&, std::string&) { return true; };
    maintenance_failure.sync_uv = [](const auto&, const auto&, std::string&) { return true; };
    const auto maintenance_failed = baas_installer::install_or_update(
        maintenance_failure_config, maintenance_failure_paths, maintenance_failure);
    const auto maintenance_persisted = baas_installer::load_config(maintenance_failure_paths);
    if (maintenance_failed.success || maintenance_failed.error.find("forced maintenance failure") == std::string::npos ||
        maintenance_failure_config.main_sha != "main-new" || maintenance_failure_config.ocr_sha != "ocr-new" ||
        maintenance_persisted.main_sha != "main-new" || maintenance_persisted.ocr_sha != "ocr-new" ||
        std::ifstream(maintenance_failure_paths.root / "main.txt").get() != 'n' ||
        std::ifstream(maintenance_failure_paths.root / "core/ocr/baas_ocr_client/bin/ocr.txt").get() != 'n') {
        std::cerr << "post-commit maintenance failure did not preserve the durable installation state\n";
        return 1;
    }

    auto preparation_failure_paths = baas_installer::InstallPaths::from_executable(
        fixture / "preparation-failure" / "BlueArchiveAutoScript.exe");
    baas_installer::InstallerConfig preparation_failure_config;
    preparation_failure_config.mirrorc_cdk = "selected-cdk";
    preparation_failure_config.main_sha = "main-old";
    preparation_failure_config.ocr_sha = "ocr-old";
    baas_installer::WorkflowServices preparation_failure = services;
    preparation_failure.prepare_main = [](auto&) {
        return baas_installer::PreparedRepository{.success = false, .error = "forced preparation failure"};
    };
    preparation_failure.prepare_ocr = [](auto&) {
        return baas_installer::PreparedRepository{.success = false, .error = "forced preparation failure"};
    };
    const auto preparation_failed = baas_installer::install_or_update(
        preparation_failure_config, preparation_failure_paths, preparation_failure);
    const auto preparation_persisted = baas_installer::load_config(preparation_failure_paths);
    if (preparation_failed.success || !fs::exists(preparation_failure_paths.setup_toml) ||
        preparation_persisted.mirrorc_cdk != "selected-cdk" ||
        preparation_persisted.main_sha != "main-old" || preparation_persisted.ocr_sha != "ocr-old") {
        std::cerr << "preparation failure must retain the initial setup.toml and old versions\n";
        return 1;
    }
    fs::remove_all(fixture, ignored);
    return 0;
}
