#include "baas_installer/transaction.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>

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
    const auto abandoned = paths.tmp_dir / "installer" / "abandoned";
    const auto unowned = paths.tmp_dir / "installer" / "unowned";
    const auto outside = fixture / "outside";
    write(abandoned / "journal.log", "created\n");
    write(abandoned / "payload.bin", "stale");
    write(unowned / "payload.bin", "keep");
    write(outside / "journal.log", "keep\n");
    baas_installer::cleanup_abandoned_transactions(paths);
    if (fs::exists(abandoned) || !fs::exists(unowned) || !fs::exists(outside)) {
        std::cerr << "abandoned transaction cleanup escaped ownership constraints\n";
        return 1;
    }
    write(paths.executable, "installer-binary");
    write(paths.root / "core/ocr/baas_ocr_client/bin/keep.txt", "old-ocr");
    write(paths.root / "app.txt", "old-main");
    write(paths.root / "obsolete.py", "old-module");
    write(paths.root / "config/user.json", "user-data");
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
        if (fs::exists(paths.root / "obsolete.py") || read(paths.root / "config/user.json") != "user-data") {
            std::cerr << "full deployment did not remove stale managed files while preserving user data\n"; return 1;
        }
        transaction.deploy_ocr();
        transaction.rollback();
    }
    const bool good = read(paths.root / "app.txt") == "old-main" && read(paths.root / "obsolete.py") == "old-module" &&
        read(paths.root / "config/user.json") == "user-data" &&
        read(paths.root / "core/ocr/baas_ocr_client/bin/keep.txt") == "old-ocr";
    write(paths.root / "delete.txt", "keep-after-rollback");
    write(paths.root / ".git" / "HEAD", "ref: refs/heads/master");
    {
        baas_installer::InstallTransaction transaction(paths);
        transaction.remove_path(paths.root / "delete.txt");
        transaction.remove_path(paths.root / ".git");
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
        transaction.commit();
    }
    if (!commit_action_called || fs::exists(committed_staging)) {
        std::cerr << "commit actions or staging cleanup failed\n";
        return 1;
    }
    fs::remove_all(fixture, ignored);
    if (!good || !removals_rolled_back || !rollback_action_called) { std::cerr << "rollback failed\n"; return 1; }
    return 0;
}
