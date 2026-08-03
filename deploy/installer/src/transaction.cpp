#include "baas_installer/transaction.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <fstream>
#include <stdexcept>

#ifdef _WIN32
#include <windows.h>
#else
#include <fcntl.h>
#include <sys/file.h>
#include <unistd.h>
#endif

namespace fs = std::filesystem;

namespace baas_installer {
namespace {

bool is_ocr_bin(const fs::path& relative) {
    static const fs::path expected{"core/ocr/baas_ocr_client/bin"};
    return relative == expected;
}

bool is_protected_installer_path(const fs::path& relative, const fs::path& executable_name) {
    if (relative.empty()) return true;
    const auto first = *relative.begin();
    if (!executable_name.empty() && first == executable_name) return true;
    static const std::array<fs::path, 7> protected_paths{
        "BlueArchiveAutoScript.exe", "setup.toml", "log", "tmp", "toolkit", ".venv", ".baas-installer"};
    return std::find(protected_paths.begin(), protected_paths.end(), first) != protected_paths.end();
}

bool is_preserved_user_path(const fs::path& relative, const bool main_tree) {
    if (relative.empty()) return true;
    const auto first = *relative.begin();
    if (main_tree) {
        static const std::array<fs::path, 5> paths{"config", "output", "screenshot", "screenshots", "data"};
        return std::find(paths.begin(), paths.end(), first) != paths.end();
    }
    static const std::array<fs::path, 2> paths{"config", "output"};
    return std::find(paths.begin(), paths.end(), first) != paths.end();
}

bool is_within(const fs::path& root, const fs::path& candidate) {
    const auto base = fs::absolute(root).lexically_normal();
    const auto target = fs::absolute(candidate).lexically_normal();
    auto base_it = base.begin();
    auto target_it = target.begin();
    for (; base_it != base.end(); ++base_it, ++target_it) {
        if (target_it == target.end() || *target_it != *base_it) return false;
    }
    return true;
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

void cleanup_abandoned_transactions_unlocked(const InstallPaths& paths) {
    std::error_code error;
    const auto root = fs::weakly_canonical(paths.tmp_dir / "installer", error);
    if (error || !fs::is_directory(root, error)) return;
    for (fs::directory_iterator item(root, error), end; !error && item != end; item.increment(error)) {
        if (!item->is_directory(error)) continue;
        const auto child = fs::weakly_canonical(item->path(), error);
        if (error) { error.clear(); continue; }
        if (child.parent_path() != root || !fs::is_regular_file(child / "journal.log", error)) {
            error.clear();
            continue;
        }
        fs::remove_all(child, error);
        error.clear();
    }
}

InstallTransaction::InstallTransaction(const InstallPaths& paths) : paths_(paths) {
    const auto state_directory = paths_.state_dir.empty() ? paths_.root / ".baas-installer" : paths_.state_dir;
    fs::create_directories(state_directory);
    const auto lock_path = state_directory / "installer.lock";
#ifdef _WIN32
    const HANDLE handle = CreateFileW(lock_path.wstring().c_str(), GENERIC_READ | GENERIC_WRITE, 0, nullptr,
                                      OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (handle == INVALID_HANDLE_VALUE) throw std::runtime_error("another installer is already running");
    lock_handle_ = reinterpret_cast<std::intptr_t>(handle);
#else
    const int descriptor = open(lock_path.c_str(), O_CREAT | O_RDWR, 0600);
    if (descriptor < 0 || flock(descriptor, LOCK_EX | LOCK_NB) != 0) {
        if (descriptor >= 0) close(descriptor);
        throw std::runtime_error("another installer is already running");
    }
    lock_handle_ = descriptor;
#endif
    try {
        cleanup_abandoned_transactions_unlocked(paths_);
        const auto tick = std::chrono::steady_clock::now().time_since_epoch().count();
        staging_root_ = paths_.tmp_dir / "installer" / std::to_string(tick);
        fs::create_directories(staging_root_ / "rollback");
        journal("created");
    } catch (...) {
        release_lock();
        throw;
    }
}

InstallTransaction::~InstallTransaction() {
    if (!settled_) rollback();
    release_lock();
}

void InstallTransaction::release_lock() noexcept {
    if (lock_handle_ == -1) return;
#ifdef _WIN32
    CloseHandle(reinterpret_cast<HANDLE>(lock_handle_));
#else
    const int descriptor = static_cast<int>(lock_handle_);
    (void)flock(descriptor, LOCK_UN);
    close(descriptor);
#endif
    lock_handle_ = -1;
}

fs::path InstallTransaction::main_staging_path() const { return staging_root_ / "main"; }
fs::path InstallTransaction::ocr_staging_path() const { return staging_root_ / "ocr"; }

void InstallTransaction::journal(const std::string& event) const {
    std::ofstream output(staging_root_ / "journal.log", std::ios::app);
    output << event << '\n';
}

void InstallTransaction::deploy_tree(const fs::path& source, const fs::path& destination, const bool skip_ocr_bin) {
    if (!fs::is_directory(source)) throw std::runtime_error("verified staging directory is missing");
    std::vector<fs::path> stale;
    std::error_code scan_error;
    if (fs::is_directory(destination)) {
        for (auto iterator = fs::recursive_directory_iterator(destination, scan_error);
             !scan_error && iterator != fs::recursive_directory_iterator(); ++iterator) {
            const auto relative = iterator->path().lexically_relative(destination);
            const bool preserved = is_protected_installer_path(relative, paths_.executable.filename()) ||
                                   is_preserved_user_path(relative, destination == paths_.root);
            const bool ocr_tree = skip_ocr_bin && (is_ocr_bin(relative) || is_ocr_bin(relative.parent_path()));
            if (preserved || ocr_tree) {
                if (iterator->is_directory()) iterator.disable_recursion_pending();
                continue;
            }
            const auto staged = source / relative;
            if (iterator->is_directory()) {
                if (fs::exists(staged) && !fs::is_directory(staged)) {
                    stale.push_back(iterator->path());
                    iterator.disable_recursion_pending();
                }
            } else if (!fs::exists(staged) || !fs::is_regular_file(staged)) {
                stale.push_back(iterator->path());
            }
        }
        if (scan_error) throw std::runtime_error("could not inspect live deployment tree: " + scan_error.message());
    }
    std::sort(stale.begin(), stale.end(), [](const fs::path& left, const fs::path& right) {
        return std::distance(left.begin(), left.end()) > std::distance(right.begin(), right.end());
    });
    for (const auto& path : stale) if (fs::exists(path)) remove_path(path);

    for (auto iterator = fs::recursive_directory_iterator(source); iterator != fs::recursive_directory_iterator(); ++iterator) {
        const auto& entry = *iterator;
        // `relative()` may canonicalize through the active ANSI code page on
        // Windows.  Staging names can legitimately contain CJK characters, so
        // retain the native path components without a conversion round-trip.
        const auto relative = entry.path().lexically_relative(source);
        if (!relative.empty() && *relative.begin() == fs::path(".git")) {
            if (entry.is_directory()) iterator.disable_recursion_pending();
            continue;
        }
        if (is_protected_installer_path(relative, paths_.executable.filename())) {
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
        changes_.push_back({target, backup, exists, false});
        fs::copy_file(entry.path(), target, fs::copy_options::overwrite_existing, error);
        if (error) throw std::runtime_error("could not deploy staged file '" + display_path(target) + "': " + error.message());
    }
}

void InstallTransaction::deploy_main() {
    deploy_main_from(main_staging_path());
}

void InstallTransaction::deploy_main_from(const fs::path& source) {
    journal("deploy-main");
    deploy_tree(source, paths_.root, true);
}

void InstallTransaction::deploy_ocr() {
    deploy_ocr_from(ocr_staging_path());
}

void InstallTransaction::deploy_ocr_from(const fs::path& source) {
    journal("deploy-ocr");
    deploy_tree(source, paths_.root / "core" / "ocr" / "baas_ocr_client" / "bin", false);
}

void InstallTransaction::replace_file(const fs::path& source, const fs::path& destination) {
    if (!fs::is_regular_file(source)) throw std::runtime_error("replacement source file is missing");
    if (!is_within(paths_.root, destination)) throw std::runtime_error("replacement destination escapes install root");
    const auto relative = fs::absolute(destination).lexically_normal().lexically_relative(fs::absolute(paths_.root).lexically_normal());
    if (relative.empty() || is_protected_installer_path(relative, paths_.executable.filename())) {
        throw std::runtime_error("replacement destination is protected");
    }
    const bool exists = fs::exists(destination);
    if (exists && fs::is_directory(destination)) throw std::runtime_error("replacement destination is a directory");
    const auto backup = staging_root_ / "rollback" / std::to_string(changes_.size());
    std::error_code error;
    fs::create_directories(destination.parent_path(), error);
    if (error) throw std::runtime_error("could not create replacement directory: " + error.message());
    if (exists) {
        fs::copy_file(destination, backup, fs::copy_options::overwrite_existing, error);
        if (error) throw std::runtime_error("could not back up replacement file: " + error.message());
    }
    changes_.push_back({destination, backup, exists, false});
    fs::copy_file(source, destination, fs::copy_options::overwrite_existing, error);
    if (error) throw std::runtime_error("could not replace live file: " + error.message());
    journal("replace:" + display_path(destination));
}

void InstallTransaction::replace_directory(const fs::path& source, const fs::path& destination) {
    if (!fs::is_directory(source)) throw std::runtime_error("replacement source directory is missing");
    if (!is_within(staging_root_, source) || !is_within(paths_.root, destination)) {
        throw std::runtime_error("directory replacement escapes the installation transaction");
    }
    const auto relative = fs::absolute(destination).lexically_normal().lexically_relative(
        fs::absolute(paths_.root).lexically_normal());
    if (relative.empty() || is_protected_installer_path(relative, paths_.executable.filename())) {
        throw std::runtime_error("replacement directory is protected");
    }
    const bool exists = fs::exists(destination);
    const auto backup = staging_root_ / "rollback" / std::to_string(changes_.size());
    std::error_code error;
    fs::create_directories(destination.parent_path(), error);
    if (error) throw std::runtime_error("could not create replacement directory parent: " + error.message());
    if (exists) {
        fs::create_directories(backup.parent_path(), error);
        if (!error) fs::rename(destination, backup, error);
        if (error) throw std::runtime_error("could not back up replacement directory: " + error.message());
    }
    changes_.push_back({destination, backup, exists, true});
    fs::rename(source, destination, error);
    if (error) throw std::runtime_error("could not move replacement directory: " + error.message());
    journal("replace-directory:" + display_path(destination));
}

void InstallTransaction::remove_path(const fs::path& destination) {
    if (!is_within(paths_.root, destination)) throw std::runtime_error("removal destination escapes install root");
    const auto relative = fs::absolute(destination).lexically_normal().lexically_relative(fs::absolute(paths_.root).lexically_normal());
    if (relative.empty() || is_protected_installer_path(relative, paths_.executable.filename())) {
        throw std::runtime_error("removal destination is protected");
    }
    if (!fs::exists(destination)) return;
    const bool directory = fs::is_directory(destination);
    const auto backup = staging_root_ / "rollback" / std::to_string(changes_.size());
    std::error_code error;
    fs::create_directories(backup.parent_path(), error);
    if (error) throw std::runtime_error("could not create removal backup directory: " + error.message());
    if (directory) {
        fs::rename(destination, backup, error);
    } else {
        fs::copy_file(destination, backup, fs::copy_options::overwrite_existing, error);
        if (!error) fs::remove(destination, error);
    }
    if (error) throw std::runtime_error("could not remove live path transactionally: " + error.message());
    changes_.push_back({destination, backup, true, directory});
    journal("remove:" + display_path(destination));
}

void InstallTransaction::add_rollback_action(std::function<void()> action) {
    if (action) rollback_actions_.push_back(std::move(action));
}

void InstallTransaction::add_commit_action(std::function<void()> action) {
    if (action) commit_actions_.push_back(std::move(action));
}

void InstallTransaction::add_post_commit_action(std::function<void()> action) {
    if (action) post_commit_actions_.push_back(std::move(action));
}

void InstallTransaction::write_ocr_managed_marker(const std::string& branch, const std::string& commit) {
    const auto target = paths_.root / "core" / "ocr" / "baas_ocr_client" / "bin" / ".baas-installer-managed.json";
    const bool exists = fs::exists(target);
    const auto backup = staging_root_ / "rollback" / std::to_string(changes_.size());
    fs::create_directories(target.parent_path());
    if (exists) fs::copy_file(target, backup, fs::copy_options::overwrite_existing);
    changes_.push_back({target, backup, exists, false});
    std::ofstream output(target, std::ios::trunc);
    output << "{\"schema_version\":1,\"managed_by\":\"baas-installer\",\"branch\":\""
           << branch << "\",\"commit\":\"" << commit << "\"}\n";
    output.close();
    if (!output) throw std::runtime_error("could not write OCR managed marker");
    journal("ocr-marker");
}

void InstallTransaction::prepare_commit() {
    if (commit_prepared_) return;
    for (auto& action : commit_actions_) action();
    commit_prepared_ = true;
}

std::string InstallTransaction::commit() {
    prepare_commit();
    journal("committed");
    settled_ = true;
    std::error_code ignored;
    fs::remove_all(staging_root_, ignored);
    std::string failures;
    for (auto& action : post_commit_actions_) {
        try {
            action();
        } catch (const std::exception& error) {
            if (!failures.empty()) failures += "; ";
            failures += error.what();
        } catch (...) {
            if (!failures.empty()) failures += "; ";
            failures += "unknown post-commit maintenance failure";
        }
    }
    return failures;
}

void InstallTransaction::rollback() noexcept {
    std::error_code ignored;
    for (auto action = rollback_actions_.rbegin(); action != rollback_actions_.rend(); ++action) {
        try { (*action)(); } catch (...) {}
    }
    for (auto it = changes_.rbegin(); it != changes_.rend(); ++it) {
        if (it->directory) {
            fs::remove_all(it->destination, ignored);
            if (it->existed) {
                fs::create_directories(it->destination.parent_path(), ignored);
                fs::rename(it->backup, it->destination, ignored);
            }
        } else if (it->existed) {
            fs::create_directories(it->destination.parent_path(), ignored);
            fs::copy_file(it->backup, it->destination, fs::copy_options::overwrite_existing, ignored);
        } else {
            fs::remove(it->destination, ignored);
        }
    }
    journal("rolled-back");
    settled_ = true;
    fs::remove_all(staging_root_, ignored);
}

}  // namespace baas_installer
