#include "baas_installer/transaction.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <fstream>
#include <stdexcept>

#ifdef _WIN32
#include <windows.h>
#endif

namespace fs = std::filesystem;

namespace baas_installer {
namespace {

bool is_ocr_bin(const fs::path& relative) {
    static const fs::path expected{"core/ocr/baas_ocr_client/bin"};
    return relative == expected;
}

bool is_protected_installer_path(const fs::path& relative) {
    const auto first = *relative.begin();
    static const std::array<fs::path, 7> protected_paths{
        "BlueArchiveAutoScript.exe", "setup.toml", "log", "tmp", "toolkit", ".venv", ".baas-installer"};
    return std::find(protected_paths.begin(), protected_paths.end(), first) != protected_paths.end();
}

std::string display_path(const fs::path& path) {
#ifdef _WIN32
    const auto wide = path.wstring();
    const auto size = WideCharToMultiByte(CP_UTF8, 0, wide.data(), static_cast<int>(wide.size()), nullptr, 0, nullptr, nullptr);
    std::string text(size, '\0');
    WideCharToMultiByte(CP_UTF8, 0, wide.data(), static_cast<int>(wide.size()), text.data(), size, nullptr, nullptr);
    return text;
#else
    return path.string();
#endif
}

}  // namespace

InstallTransaction::InstallTransaction(const InstallPaths& paths) : paths_(paths) {
    const auto tick = std::chrono::steady_clock::now().time_since_epoch().count();
    staging_root_ = paths_.tmp_dir / "installer" / std::to_string(tick);
    fs::create_directories(staging_root_ / "rollback");
    journal("created");
}

InstallTransaction::~InstallTransaction() { if (!settled_) rollback(); }

fs::path InstallTransaction::main_staging_path() const { return staging_root_ / "main"; }
fs::path InstallTransaction::ocr_staging_path() const { return staging_root_ / "ocr"; }

void InstallTransaction::journal(const std::string& event) const {
    std::ofstream output(staging_root_ / "journal.log", std::ios::app);
    output << event << '\n';
}

void InstallTransaction::deploy_tree(const fs::path& source, const fs::path& destination, const bool skip_ocr_bin) {
    if (!fs::is_directory(source)) throw std::runtime_error("verified staging directory is missing");
    for (auto iterator = fs::recursive_directory_iterator(source); iterator != fs::recursive_directory_iterator(); ++iterator) {
        const auto& entry = *iterator;
        // `relative()` may canonicalize through the active ANSI code page on
        // Windows.  Staging names can legitimately contain CJK characters, so
        // retain the native path components without a conversion round-trip.
        const auto relative = entry.path().lexically_relative(source);
        if (is_protected_installer_path(relative)) {
            if (entry.is_directory()) iterator.disable_recursion_pending();
            continue;
        }
        if (skip_ocr_bin && (is_ocr_bin(relative) || is_ocr_bin(relative.parent_path()))) {
            if (entry.is_directory()) iterator.disable_recursion_pending();
            continue;
        }
        if (entry.is_directory()) continue;
        if (!entry.is_regular_file()) continue;
        const auto target = destination / relative;
        const bool exists = fs::exists(target);
        const auto backup = staging_root_ / "rollback" / std::to_string(changes_.size());
        std::error_code error;
        fs::create_directories(target.parent_path(), error);
        if (error) throw std::runtime_error("could not create a deployment directory: " + error.message());
        if (exists) {
            fs::create_directories(backup.parent_path(), error);
            if (error) throw std::runtime_error("could not create a rollback directory: " + error.message());
            fs::copy_file(target, backup, fs::copy_options::overwrite_existing, error);
            if (error) throw std::runtime_error("could not back up a live file: " + error.message());
            // Legacy Git metadata is often copied from a read-only medium.
            // The backup above keeps rollback safe; now make the live target
            // replaceable instead of failing the whole staged update.
            fs::permissions(target, fs::perms::owner_write, fs::perm_options::add, error);
            if (error) throw std::runtime_error("could not make a live file writable: " + error.message());
        }
        journal("copy-index=" + std::to_string(changes_.size()));
        fs::copy_file(entry.path(), target, fs::copy_options::overwrite_existing, error);
        if (error) throw std::runtime_error("could not deploy staged file '" + display_path(target) + "': " + error.message());
        changes_.push_back({target, backup, exists});
    }
}

void InstallTransaction::deploy_main() {
    journal("deploy-main");
    deploy_tree(main_staging_path(), paths_.root, true);
}

void InstallTransaction::deploy_ocr() {
    journal("deploy-ocr");
    deploy_tree(ocr_staging_path(), paths_.root / "core" / "ocr" / "baas_ocr_client" / "bin", false);
}

void InstallTransaction::write_ocr_managed_marker() {
    const auto target = paths_.root / "core" / "ocr" / "baas_ocr_client" / "bin" / ".baas-installer-managed.json";
    const bool exists = fs::exists(target);
    const auto backup = staging_root_ / "rollback" / std::to_string(changes_.size());
    fs::create_directories(target.parent_path());
    if (exists) fs::copy_file(target, backup, fs::copy_options::overwrite_existing);
    std::ofstream output(target, std::ios::trunc);
    output << "{\"schema_version\":1,\"managed_by\":\"baas-installer\"}\n";
    output.close();
    changes_.push_back({target, backup, exists});
    journal("ocr-marker");
}

void InstallTransaction::commit() {
    journal("committed");
    settled_ = true;
    std::error_code ignored;
    fs::remove_all(staging_root_, ignored);
}

void InstallTransaction::rollback() noexcept {
    std::error_code ignored;
    for (auto it = changes_.rbegin(); it != changes_.rend(); ++it) {
        if (it->existed) fs::copy_file(it->backup, it->destination, fs::copy_options::overwrite_existing, ignored);
        else fs::remove(it->destination, ignored);
    }
    journal("rolled-back");
    settled_ = true;
}

}  // namespace baas_installer
