#include "baas_installer/transaction.hpp"
#include "baas_installer/deployment_manifest.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <fstream>
#include <stdexcept>

#include <nlohmann/json.hpp>

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

bool is_link_or_reparse_point(const fs::path& path) {
    std::error_code error;
    if (fs::is_symlink(fs::symlink_status(path, error))) return true;
#ifdef _WIN32
    const auto attributes = GetFileAttributesW(path.wstring().c_str());
    return attributes != INVALID_FILE_ATTRIBUTES &&
           (attributes & FILE_ATTRIBUTE_REPARSE_POINT) != 0;
#else
    return false;
#endif
}

bool safe_owned_destination(const fs::path& root, const fs::path& candidate) {
    if (!is_within(root, candidate)) return false;
    const auto base = fs::absolute(root).lexically_normal();
    const auto target = fs::absolute(candidate).lexically_normal();
    if (is_link_or_reparse_point(base)) return false;
    auto current = base;
    const auto relative = target.lexically_relative(base);
    for (const auto& component : relative) {
        if (component == fs::path("..")) return false;
        current /= component;
        std::error_code error;
        if (!fs::exists(current, error)) continue;
        if (error || is_link_or_reparse_point(current)) return false;
    }
    return true;
}

std::string display_path(const fs::path& path) {
    return path_to_utf8(path);
}

}  // namespace

InstallTransaction::InstallTransaction(const InstallPaths& paths) : paths_(paths) {
    const auto root = fs::absolute(paths_.root).lexically_normal();
    const auto expected_tmp = root / "tmp";
    const auto expected_state = root / ".baas-installer";
    if (root.empty() || root == root.root_path() ||
        fs::absolute(paths_.tmp_dir).lexically_normal() != expected_tmp ||
        fs::absolute(paths_.state_dir).lexically_normal() != expected_state ||
        !safe_owned_destination(root, expected_tmp) ||
        !safe_owned_destination(root, expected_state)) {
        throw std::runtime_error("installer transaction paths are not bound to the validated BAAS root");
    }
    const auto state_directory = expected_state;
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
        const auto tick = std::chrono::steady_clock::now().time_since_epoch().count();
        const auto staging_parent = expected_tmp / "installer";
        fs::create_directories(staging_parent);
        for (std::size_t attempt = 0; attempt != 100; ++attempt) {
            const auto candidate = staging_parent /
                (std::to_string(tick) + "-" + std::to_string(attempt));
            std::error_code create_error;
            if (fs::create_directory(candidate, create_error)) {
                staging_root_ = candidate;
                staging_owned_ = true;
                break;
            }
            if (create_error) throw std::runtime_error("could not create transaction staging directory");
        }
        if (!staging_owned_) throw std::runtime_error("could not allocate unique transaction staging directory");
        fs::create_directory(staging_root_ / "rollback");
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
    const bool main_tree = destination == paths_.root;
    const auto tree = main_tree ? DeploymentTree::Main : DeploymentTree::Ocr;
    DeploymentFileSet new_files;
    std::error_code scan_error;
    for (auto iterator = fs::recursive_directory_iterator(source, scan_error);
         !scan_error && iterator != fs::recursive_directory_iterator(); ++iterator) {
        const auto relative = iterator->path().lexically_relative(source);
        const bool preserved = is_protected_installer_path(relative, paths_.executable.filename()) ||
                               is_preserved_user_path(relative, main_tree);
        const bool ocr_tree = skip_ocr_bin && (is_ocr_bin(relative) || is_ocr_bin(relative.parent_path()));
        if (preserved || ocr_tree || !deployment_relative_path_allowed(tree, relative)) {
            if (iterator->is_directory()) iterator.disable_recursion_pending();
            continue;
        }
        if (iterator->is_symlink()) {
            if (iterator->is_directory()) iterator.disable_recursion_pending();
            continue;
        }
        if (iterator->is_regular_file()) new_files.insert(relative);
    }
    if (scan_error) throw std::runtime_error("could not inspect staged deployment tree: " + scan_error.message());

    const auto previous = load_deployment_manifest(paths_, tree);
    if (previous.valid) {
        for (const auto& relative : previous.files) {
            if (new_files.contains(relative)) continue;
            const auto stale = destination / relative;
            std::error_code stale_error;
            if (!fs::is_regular_file(stale, stale_error) || stale_error ||
                !safe_owned_destination(destination, stale)) {
                continue;
            }
            remove_path(stale, main_tree ? RemovalOwnership::MainManifest
                                         : RemovalOwnership::OcrManifest);
        }
    }

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
        if (is_protected_installer_path(relative, paths_.executable.filename()) ||
            is_preserved_user_path(relative, main_tree) ||
            !deployment_relative_path_allowed(tree, relative)) {
            if (entry.is_directory()) iterator.disable_recursion_pending();
            continue;
        }
        if (skip_ocr_bin && (is_ocr_bin(relative) || is_ocr_bin(relative.parent_path()))) {
            if (entry.is_directory()) iterator.disable_recursion_pending();
            continue;
        }
        if (entry.is_symlink()) {
            if (entry.is_directory()) iterator.disable_recursion_pending();
            continue;
        }
        if (entry.is_directory()) continue;
        if (!entry.is_regular_file()) continue;
        const auto target = destination / relative;
        if (!safe_owned_destination(destination, target)) {
            throw std::runtime_error("deployment target crosses a symbolic link or leaves its owned tree: " +
                                     display_path(target));
        }
        const bool exists = fs::exists(target);
        if (exists && !fs::is_regular_file(target)) {
            throw std::runtime_error("deployment target is not an owned regular file: " + display_path(target));
        }
        if (exists && (!previous.valid || !previous.files.contains(relative))) {
            throw std::runtime_error("deployment refused to overwrite a file absent from its ownership manifest: " +
                                     display_path(target));
        }
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

    InstallPaths staged_paths = paths_;
    staged_paths.state_dir = staging_root_ / "manifests";
    save_deployment_manifest_atomic(staged_paths, tree, new_files);
    replace_owned_manifest(deployment_manifest_path(staged_paths, tree),
                           deployment_manifest_path(paths_, tree));
    if (tree == DeploymentTree::Main) main_manifest_.reset();
    else ocr_manifest_.reset();
}

void InstallTransaction::cleanup_staging() noexcept {
    if (!staging_owned_) return;
    const auto expected_parent = fs::absolute(paths_.root / "tmp" / "installer").lexically_normal();
    const auto staging = fs::absolute(staging_root_).lexically_normal();
    std::error_code error;
    if (staging.parent_path() != expected_parent ||
        !safe_owned_destination(expected_parent, staging) ||
        !fs::is_regular_file(staging / "journal.log", error) || error) {
        return;
    }
    fs::remove_all(staging, error);
    if (!error) staging_owned_ = false;
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
    if (!safe_owned_destination(paths_.root, destination)) {
        throw std::runtime_error("replacement destination escapes install root or crosses a link");
    }
    const auto relative = fs::absolute(destination).lexically_normal().lexically_relative(fs::absolute(paths_.root).lexically_normal());
    if (relative.empty() || is_protected_installer_path(relative, paths_.executable.filename())) {
        throw std::runtime_error("replacement destination is protected");
    }
    const bool exists = fs::exists(destination);
    if (exists && fs::is_directory(destination)) throw std::runtime_error("replacement destination is a directory");
    const auto main_root = fs::absolute(paths_.root).lexically_normal();
    const auto ocr_root = main_root / "core" / "ocr" / "baas_ocr_client" / "bin";
    const auto target = fs::absolute(destination).lexically_normal();
    const bool ocr = is_within(ocr_root, target);
    const auto tree = ocr ? DeploymentTree::Ocr : DeploymentTree::Main;
    const auto live_root = ocr ? ocr_root : main_root;
    const auto owned_relative = target.lexically_relative(live_root);
    auto& manifest = mutable_manifest(tree);
    if (!deployment_relative_path_allowed(tree, owned_relative) ||
        (exists && !manifest.contains(owned_relative))) {
        throw std::runtime_error("replacement refused because installer ownership was not proven");
    }
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
    manifest.insert(owned_relative);
    journal("replace:" + display_path(destination));
}

void InstallTransaction::replace_directory(const fs::path& source, const fs::path& destination) {
    if (!fs::is_directory(source)) throw std::runtime_error("replacement source directory is missing");
    if (!safe_owned_destination(staging_root_, source) ||
        !safe_owned_destination(paths_.root, destination)) {
        throw std::runtime_error("directory replacement escapes the installation transaction");
    }
    const auto relative = fs::absolute(destination).lexically_normal().lexically_relative(
        fs::absolute(paths_.root).lexically_normal());
    static const fs::path main_git{".git"};
    static const fs::path ocr_git{"core/ocr/baas_ocr_client/bin/.git"};
    if (relative != main_git && relative != ocr_git) {
        throw std::runtime_error("directory replacement is limited to installer-managed Git metadata");
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

void InstallTransaction::replace_owned_manifest(const fs::path& source, const fs::path& destination) {
    const bool known_destination = destination == deployment_manifest_path(paths_, DeploymentTree::Main) ||
                                   destination == deployment_manifest_path(paths_, DeploymentTree::Ocr);
    if (!known_destination || !safe_owned_destination(staging_root_, source) ||
        !safe_owned_destination(paths_.root, destination) || !fs::is_regular_file(source)) {
        throw std::runtime_error("deployment manifest replacement was not owned by this transaction");
    }
    const bool exists = fs::exists(destination);
    if (exists && !fs::is_regular_file(destination)) {
        throw std::runtime_error("existing deployment manifest is not a regular file");
    }
    const auto backup = staging_root_ / "rollback" / std::to_string(changes_.size());
    std::error_code error;
    fs::create_directories(destination.parent_path(), error);
    if (error) throw std::runtime_error("could not create deployment manifest directory: " + error.message());
    if (exists) {
        fs::copy_file(destination, backup, fs::copy_options::overwrite_existing, error);
        if (error) throw std::runtime_error("could not back up deployment manifest: " + error.message());
    }
    changes_.push_back({destination, backup, exists, false});
    fs::copy_file(source, destination, fs::copy_options::overwrite_existing, error);
    if (error) throw std::runtime_error("could not replace deployment manifest: " + error.message());
    journal("replace-manifest:" + display_path(destination));
}

DeploymentFileSet& InstallTransaction::mutable_manifest(const DeploymentTree tree) {
    auto& pending = tree == DeploymentTree::Main ? main_manifest_ : ocr_manifest_;
    if (!pending) {
        const auto loaded = load_deployment_manifest(paths_, tree);
        if (!loaded.valid) {
            throw std::runtime_error("incremental deployment requires a valid ownership manifest");
        }
        pending = loaded.files;
    }
    return *pending;
}

void InstallTransaction::stage_pending_manifests() {
    InstallPaths staged_paths = paths_;
    staged_paths.state_dir = staging_root_ / "incremental-manifests";
    const auto stage = [&](const DeploymentTree tree, const DeploymentFileSet& files) {
        save_deployment_manifest_atomic(staged_paths, tree, files);
        replace_owned_manifest(deployment_manifest_path(staged_paths, tree),
                               deployment_manifest_path(paths_, tree));
    };
    if (main_manifest_) stage(DeploymentTree::Main, *main_manifest_);
    if (ocr_manifest_) stage(DeploymentTree::Ocr, *ocr_manifest_);
}

void InstallTransaction::remove_path(const fs::path& destination,
                                     const RemovalOwnership ownership) {
    if (!safe_owned_destination(paths_.root, destination)) {
        throw std::runtime_error("removal destination escapes install root or crosses a link");
    }
    const auto main_root = fs::absolute(paths_.root).lexically_normal();
    const auto ocr_root = main_root / "core" / "ocr" / "baas_ocr_client" / "bin";
    const auto target = fs::absolute(destination).lexically_normal();
    bool owned = false;
    bool directory_allowed = false;
    DeploymentFileSet* pending_manifest = nullptr;
    fs::path manifest_relative;
    if (ownership == RemovalOwnership::GitMetadata) {
        owned = target == main_root / ".git" || target == ocr_root / ".git";
        directory_allowed = true;
    } else {
        const auto tree = ownership == RemovalOwnership::MainManifest
                              ? DeploymentTree::Main
                              : DeploymentTree::Ocr;
        const auto live_root = tree == DeploymentTree::Main ? main_root : ocr_root;
        const auto relative = target.lexically_relative(live_root);
        auto& manifest = mutable_manifest(tree);
        owned = deployment_relative_path_allowed(tree, relative) && manifest.contains(relative);
        pending_manifest = &manifest;
        manifest_relative = relative;
    }
    if (!owned) throw std::runtime_error("removal refused because installer ownership was not proven");
    if (!fs::exists(destination)) return;
    const bool directory = fs::is_directory(destination);
    if (directory && !directory_allowed) {
        throw std::runtime_error("manifest-owned removal is limited to regular files");
    }
    if (!directory && !fs::is_regular_file(destination)) {
        throw std::runtime_error("removal target is not an owned regular file");
    }
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
    if (pending_manifest != nullptr) pending_manifest->erase(manifest_relative);
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
    if (exists) {
        if (!fs::is_regular_file(target)) {
            throw std::runtime_error("existing OCR ownership marker is not a regular file");
        }
        try {
            std::ifstream input(target, std::ios::binary);
            const auto document = nlohmann::json::parse(input);
            if (document.at("schema_version").get<int>() != 1 ||
                document.at("managed_by").get<std::string>() != "baas-installer") {
                throw std::runtime_error("unrecognized OCR ownership marker");
            }
        } catch (const std::exception&) {
            throw std::runtime_error("refusing to overwrite an unrecognized OCR ownership marker");
        }
    }
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
    stage_pending_manifests();
    for (auto& action : commit_actions_) action();
    commit_prepared_ = true;
}

std::string InstallTransaction::commit() {
    prepare_commit();
    journal("committed");
    settled_ = true;
    cleanup_staging();
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
            auto discard_name = fs::path("discard-directory-");
            discard_name += it->backup.filename().native();
            const auto discard = staging_root_ / "rollback" / discard_name;
            fs::rename(it->destination, discard, ignored);
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
    cleanup_staging();
}

}  // namespace baas_installer
