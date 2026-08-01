#include "baas_installer/workflow.hpp"

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
    services.prepare_main = [&](auto& transaction, std::string&) { write(transaction.main_staging_path() / "main.txt", "main"); std::lock_guard lock(event_mutex); events.push_back("prepared-main"); return true; };
    services.prepare_ocr = [&](auto& transaction, std::string&) { write(transaction.ocr_staging_path() / "ocr.txt", "ocr"); std::lock_guard lock(event_mutex); events.push_back("prepared-ocr"); return true; };
    services.verify_deployment = [&](const auto& current, const auto&, std::string&) { const bool ok=fs::exists(current.root/"main.txt") && fs::exists(current.root/"core/ocr/baas_ocr_client/bin/ocr.txt"); std::lock_guard lock(event_mutex); events.push_back("verified"); return ok; };
    services.sync_uv = [&](const auto&, const auto&, std::string&) { std::lock_guard lock(event_mutex); events.push_back("uv"); return true; };
    baas_installer::InstallerConfig config;
    const auto result = baas_installer::install_or_update(config, paths, services);
    const bool order = result.success && events.size() >= 4 && events[events.size()-2] == "verified" && events.back() == "uv" &&
        fs::exists(paths.root / "core/ocr/baas_ocr_client/bin/.baas-installer-managed.json");
    fs::remove_all(fixture, ignored);
    if (!order) { std::cerr << "workflow order failed\n"; return 1; }
    return 0;
}
