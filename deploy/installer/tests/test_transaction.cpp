#include "baas_installer/transaction.hpp"
#include "baas_installer/deployment_manifest.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace fs = std::filesystem;

static void write(const fs::path& path, const std::string& text) {
    fs::create_directories(path.parent_path());
    std::ofstream(path) << text;
}

static std::string read(const fs::path& path) { std::ifstream input(path); return {std::istreambuf_iterator<char>(input), {}}; }

int main() {
    const auto fixture = fs::temp_directory_path() / "baas-installer-transaction";
    std::error_code ignored;
    fs::remove_all(fixture, ignored);
    baas_installer::InstallPaths paths;
    paths.root = fixture / "install";
    paths.executable = paths.root / "custom-linux-installer";
    paths.tmp_dir = paths.root / "tmp";
    paths.state_dir = paths.root / ".baas-installer";
    const auto abandoned = paths.tmp_dir / "installer" / "abandoned";
    const auto unowned = paths.tmp_dir / "installer" / "unowned";
    const auto outside = fixture / "outside";
    write(abandoned / "journal.log", "created\n");
    write(abandoned / "payload.bin", "stale");
    write(unowned / "payload.bin", "keep");
    write(outside / "journal.log", "keep\n");
    {
        baas_installer::InstallTransaction cleanup_owner(paths);
        bool second_rejected = false;
        try {
            baas_installer::InstallTransaction concurrent(paths);
            concurrent.rollback();
        } catch (const std::exception&) {
            second_rejected = true;
        }
        if (!second_rejected || !fs::exists(cleanup_owner.staging_root())) {
            std::cerr << "concurrent installer did not respect the active transaction lock\n";
            return 1;
        }
        cleanup_owner.rollback();
    }
    if (!fs::exists(abandoned) || !fs::exists(unowned) || !fs::exists(outside)) {
        std::cerr << "journal text alone incorrectly authorized recursive cleanup\n";
        return 1;
    }
    {
        baas_installer::InstallTransaction after_release(paths);
        after_release.rollback();
    }
    write(paths.executable, "installer-binary");
    write(paths.root / "core/ocr/baas_ocr_client/bin/keep.txt", "old-ocr");
    write(paths.root / "app.txt", "old-main");
    write(paths.root / "obsolete.py", "old-module");
    write(paths.root / "config/user.json", "user-data");
    write(paths.root / "family-photo.jpg", "user-owned-root-file");
    write(paths.root / "personal/archive.zip", "user-owned-nested-file");
    baas_installer::save_deployment_manifest_atomic(
        paths, baas_installer::DeploymentTree::Main, {fs::path("app.txt")});
    baas_installer::save_deployment_manifest_atomic(
        paths, baas_installer::DeploymentTree::Ocr, {fs::path("keep.txt")});
    fs::path rolled_back_staging;
    {
        baas_installer::InstallTransaction transaction(paths);
        rolled_back_staging = transaction.staging_root();
        write(transaction.main_staging_path() / "app.txt", "new-main");
        write(transaction.main_staging_path() / ".git/HEAD", "new-git-head");
        write(transaction.main_staging_path() / "core/ocr/baas_ocr_client/bin/keep.txt", "bad-main-ocr");
        write(transaction.ocr_staging_path() / "keep.txt", "new-ocr");
        transaction.deploy_main();
        transaction.replace_directory(transaction.main_staging_path() / ".git", paths.root / ".git");
        if (read(paths.executable) != "installer-binary") {
            std::cerr << "main deployment removed the running installer\n";
            return 1;
        }
        if (read(paths.root / ".git/HEAD") != "new-git-head" ||
            fs::exists(transaction.main_staging_path() / ".git")) {
            std::cerr << "Git metadata directory was not moved transactionally\n";
            return 1;
        }
        if (read(paths.root / "core/ocr/baas_ocr_client/bin/keep.txt") != "old-ocr") { std::cerr << "main overwrote OCR\n"; return 1; }
        if (!fs::exists(paths.root / "obsolete.py") || read(paths.root / "config/user.json") != "user-data" ||
            read(paths.root / "family-photo.jpg") != "user-owned-root-file" ||
            read(paths.root / "personal/archive.zip") != "user-owned-nested-file") {
            std::cerr << "legacy full deployment deleted an unknown file without an ownership manifest\n"; return 1;
        }
        transaction.deploy_ocr();
        transaction.rollback();
    }
    const bool good = read(paths.root / "app.txt") == "old-main" && read(paths.root / "obsolete.py") == "old-module" &&
        read(paths.root / "config/user.json") == "user-data" &&
        read(paths.root / "family-photo.jpg") == "user-owned-root-file" &&
        read(paths.root / "personal/archive.zip") == "user-owned-nested-file" &&
        read(paths.root / "core/ocr/baas_ocr_client/bin/keep.txt") == "old-ocr";
    write(paths.root / "delete.txt", "keep-after-rollback");
    write(paths.root / ".git" / "HEAD", "ref: refs/heads/master");
    baas_installer::save_deployment_manifest_atomic(
        paths, baas_installer::DeploymentTree::Main, {fs::path("delete.txt")});
    {
        baas_installer::InstallTransaction transaction(paths);
        transaction.remove_path(paths.root / "delete.txt", baas_installer::RemovalOwnership::MainManifest);
        transaction.remove_path(paths.root / ".git", baas_installer::RemovalOwnership::GitMetadata);
        if (fs::exists(paths.root / "delete.txt") || fs::exists(paths.root / ".git")) {
            std::cerr << "transactional removal did not hide live paths\n";
            return 1;
        }
        transaction.rollback();
    }
    const bool removals_rolled_back = read(paths.root / "delete.txt") == "keep-after-rollback" &&
        read(paths.root / ".git" / "HEAD") == "ref: refs/heads/master";
    if (fs::exists(rolled_back_staging)) {
        std::cerr << "rollback retained transaction staging\n";
        return 1;
    }
    bool rollback_action_called = false;
    bool commit_action_called = false;
    {
        baas_installer::InstallTransaction transaction(paths);
        transaction.add_rollback_action([&] { rollback_action_called = true; });
        transaction.rollback();
    }
    fs::path committed_staging;
    {
        baas_installer::InstallTransaction transaction(paths);
        committed_staging = transaction.staging_root();
        transaction.add_commit_action([&] { commit_action_called = true; });
        transaction.add_rollback_action([&] { commit_action_called = false; });
        if (!transaction.commit().empty()) {
            std::cerr << "successful post-commit action reported an error\n";
            return 1;
        }
    }
    if (!commit_action_called || fs::exists(committed_staging)) {
        std::cerr << "commit actions or staging cleanup failed\n";
        return 1;
    }
    bool rolled_back_after_commit = false;
    {
        baas_installer::InstallTransaction transaction(paths);
        transaction.add_rollback_action([&] { rolled_back_after_commit = true; });
        transaction.add_post_commit_action([] { throw std::runtime_error("maintenance failed"); });
        const auto post_error = transaction.commit();
        if (post_error.find("maintenance failed") == std::string::npos) {
            std::cerr << "post-commit failure was not surfaced\n";
            return 1;
        }
    }
    if (rolled_back_after_commit) {
        std::cerr << "durable commit incorrectly rolled back after maintenance failure\n";
        return 1;
    }

    const auto owned_paths = baas_installer::InstallPaths::from_root(
        fixture / "owned-install", "BAAS-Installer.exe");
    write(owned_paths.root / "collision.txt", "user-owned-collision");
    {
        baas_installer::InstallTransaction transaction(owned_paths);
        write(transaction.main_staging_path() / "collision.txt", "repository-collision");
        bool refused = false;
        try {
            transaction.deploy_main();
        } catch (const std::exception&) {
            refused = true;
        }
        transaction.rollback();
        if (!refused || read(owned_paths.root / "collision.txt") != "user-owned-collision") {
            std::cerr << "full deployment overwrote a file absent from its ownership manifest\n";
            return 1;
        }
    }
    fs::remove(owned_paths.root / "collision.txt", ignored);
    {
        baas_installer::InstallTransaction transaction(owned_paths);
        write(transaction.main_staging_path() / "keep.py", "v1");
        write(transaction.main_staging_path() / "obsolete-owned.py", "owned-v1");
        transaction.deploy_main();
        if (!transaction.commit().empty()) return 1;
    }
    write(owned_paths.root / "never-managed-user.txt", "preserve-user");
    {
        baas_installer::InstallTransaction transaction(owned_paths);
        write(transaction.main_staging_path() / "keep.py", "v2");
        transaction.deploy_main();
        if (fs::exists(owned_paths.root / "obsolete-owned.py") ||
            read(owned_paths.root / "never-managed-user.txt") != "preserve-user" ||
            !transaction.commit().empty()) {
            std::cerr << "manifest update did not limit stale removal to previously owned files\n";
            return 1;
        }
    }

    write(owned_paths.root / "preserve-after-corrupt-manifest.py", "unknown-after-corruption");
    std::ofstream(baas_installer::deployment_manifest_path(
        owned_paths, baas_installer::DeploymentTree::Main), std::ios::trunc) << "corrupt";
    {
        baas_installer::InstallTransaction transaction(owned_paths);
        write(transaction.main_staging_path() / "keep.py", "v3");
        bool refused = false;
        try {
            transaction.deploy_main();
        } catch (const std::exception&) {
            refused = true;
        }
        transaction.rollback();
        if (!refused || read(owned_paths.root / "preserve-after-corrupt-manifest.py") !=
                            "unknown-after-corruption" || read(owned_paths.root / "keep.py") != "v2") {
            std::cerr << "a corrupt ownership manifest authorized deployment mutation\n";
            return 1;
        }
    }

    bool outside_refused = false;
    write(outside / "user-file.txt", "outside-user-data");
    {
        baas_installer::InstallTransaction transaction(owned_paths);
        try {
            transaction.remove_path(outside / "user-file.txt",
                                    baas_installer::RemovalOwnership::MainManifest);
        } catch (const std::exception&) {
            outside_refused = true;
        }
        transaction.rollback();
    }
    if (!outside_refused || read(outside / "user-file.txt") != "outside-user-data") {
        std::cerr << "transaction removal escaped the BAAS installation root\n";
        return 1;
    }

    const auto directory_to_file_paths = baas_installer::InstallPaths::from_root(
        fixture / "directory-to-file-install", "BAAS-Installer.exe");
    write(directory_to_file_paths.root / "payload/old.txt", "old-owned-file");
    baas_installer::save_deployment_manifest_atomic(
        directory_to_file_paths, baas_installer::DeploymentTree::Main,
        {fs::path("payload/old.txt")});
    {
        baas_installer::InstallTransaction transaction(directory_to_file_paths);
        const auto source = transaction.main_staging_path() / "replacement";
        write(source / "payload", "new-regular-file");
        transaction.deploy_main_from(source);
        if (!transaction.commit().empty()) return 1;
    }
    if (!fs::is_regular_file(directory_to_file_paths.root / "payload") ||
        read(directory_to_file_paths.root / "payload") != "new-regular-file") {
        std::cerr << "an empty owned directory could not be replaced by a tracked file\n";
        return 1;
    }

    const auto incremental_paths = baas_installer::InstallPaths::from_root(
        fixture / "incremental-install", "BAAS-Installer.exe");
    write(incremental_paths.root / "modified.py", "old-modified");
    write(incremental_paths.root / "deleted.py", "old-deleted");
    baas_installer::save_deployment_manifest_atomic(
        incremental_paths, baas_installer::DeploymentTree::Main,
        {fs::path("modified.py"), fs::path("deleted.py")});
    {
        baas_installer::InstallTransaction transaction(incremental_paths);
        const auto additions = transaction.main_staging_path() / "incremental";
        write(additions / "modified.py", "new-modified");
        write(additions / "added.py", "new-added");
        transaction.replace_file(additions / "modified.py", incremental_paths.root / "modified.py");
        transaction.replace_file(additions / "added.py", incremental_paths.root / "added.py");
        transaction.remove_path(incremental_paths.root / "deleted.py",
                                baas_installer::RemovalOwnership::MainManifest);
        if (!transaction.commit().empty()) return 1;
    }
    const auto incremental_manifest = baas_installer::load_deployment_manifest(
        incremental_paths, baas_installer::DeploymentTree::Main);
    if (!incremental_manifest.valid ||
        incremental_manifest.files != baas_installer::DeploymentFileSet{
            fs::path("added.py"), fs::path("modified.py")} ||
        read(incremental_paths.root / "modified.py") != "new-modified" ||
        read(incremental_paths.root / "added.py") != "new-added" ||
        fs::exists(incremental_paths.root / "deleted.py")) {
        std::cerr << "incremental deployment did not atomically update its ownership manifest\n";
        return 1;
    }

    const auto marker_collision_paths = baas_installer::InstallPaths::from_root(
        fixture / "marker-collision-install", "BAAS-Installer.exe");
    const auto marker_collision = marker_collision_paths.root /
        "core/ocr/baas_ocr_client/bin/.baas-installer-managed.json";
    write(marker_collision, "user-owned-marker-name");
    bool marker_collision_refused = false;
    {
        baas_installer::InstallTransaction transaction(marker_collision_paths);
        try {
            transaction.write_ocr_managed_marker("windows-x64", std::string(40, 'a'));
        } catch (const std::exception&) {
            marker_collision_refused = true;
        }
        transaction.rollback();
    }
    if (!marker_collision_refused || read(marker_collision) != "user-owned-marker-name") {
        std::cerr << "OCR managed marker overwrote an unrecognized existing file\n";
        return 1;
    }

    auto redirected_paths = owned_paths;
    redirected_paths.tmp_dir = outside / "user-tmp";
    redirected_paths.state_dir = outside / "user-state";
    write(redirected_paths.tmp_dir / "sentinel.txt", "external-temp-data");
    bool redirected_refused = false;
    try {
        baas_installer::InstallTransaction transaction(redirected_paths);
        transaction.rollback();
    } catch (const std::exception&) {
        redirected_refused = true;
    }
    if (!redirected_refused || read(redirected_paths.tmp_dir / "sentinel.txt") !=
                                   "external-temp-data") {
        std::cerr << "transaction accepted redirected scratch or state directories\n";
        return 1;
    }

    const auto link_root = owned_paths.root / "linked-user-directory";
    const auto external_link_target = outside / "linked-user-directory";
    fs::create_directories(external_link_target);
    std::error_code link_error;
    fs::create_directory_symlink(external_link_target, link_root, link_error);
    if (!link_error) {
        bool link_refused = false;
        {
            baas_installer::InstallTransaction transaction(owned_paths);
            write(transaction.main_staging_path() / "linked-user-directory" / "attack.txt", "installer-data");
            try {
                transaction.deploy_main();
            } catch (const std::exception&) {
                link_refused = true;
            }
            transaction.rollback();
        }
        if (!link_refused || fs::exists(external_link_target / "attack.txt")) {
            std::cerr << "deployment followed a symlink outside the BAAS root\n";
            return 1;
        }
    }

    fs::remove_all(fixture, ignored);
    if (!good || !removals_rolled_back || !rollback_action_called) { std::cerr << "rollback failed\n"; return 1; }
    return 0;
}
