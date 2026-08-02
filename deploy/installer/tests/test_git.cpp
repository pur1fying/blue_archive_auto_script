#include "baas_installer/git.hpp"
#include "baas_installer/process.hpp"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <cstdlib>

namespace {
namespace fs = std::filesystem;

bool command(std::initializer_list<std::string> arguments) {
    return baas_installer::run_process(std::vector<std::string>(arguments)) == 0;
}

bool write_commit(const fs::path& repository, const std::string& value, const std::string& message) {
    std::ofstream(repository / "payload.txt", std::ios::trunc) << value;
    return command({"git", "-C", repository.string(), "add", "payload.txt"}) &&
           command({"git", "-C", repository.string(), "commit", "-m", message});
}
}

int main() {
    const auto attempts = baas_installer::git_attempt_order({"source-a", "source-b"}, true, true);
    if (attempts.size() != 4 || attempts[0] != std::pair{baas_installer::GitBackend::GitCli, std::string("source-a")} ||
        attempts[1] != std::pair{baas_installer::GitBackend::GitCli, std::string("source-b")} ||
        attempts[2] != std::pair{baas_installer::GitBackend::Libgit2, std::string("source-a")} ||
        attempts[3] != std::pair{baas_installer::GitBackend::Libgit2, std::string("source-b")}) {
        std::cerr << "Git backend order must exhaust CLI sources before libgit2\n";
        return 1;
    }
    if (baas_installer::git_backend_name(baas_installer::GitBackend::GitCli) != "git-cli") {
        std::cerr << "git backend label failed\n";
        return 1;
    }
    if (baas_installer::git_backend_name(baas_installer::GitBackend::None) != "none") {
        std::cerr << "none backend label failed\n";
        return 1;
    }

    const auto unique = std::to_string(std::chrono::steady_clock::now().time_since_epoch().count());
    const auto root = fs::temp_directory_path() / ("baas-installer-git-test-" + unique);
    const auto remote = root / "remote.git";
    const auto seed = root / "seed";
    const auto live = root / "live";
    const auto staging = root / "staging";
    std::error_code ignored;
    fs::remove_all(root, ignored);
    fs::create_directories(root);
    if (!command({"git", "init", "--bare", remote.string()}) ||
        !command({"git", "init", seed.string()}) ||
        !command({"git", "-C", seed.string(), "config", "user.email", "installer@example.invalid"}) ||
        !command({"git", "-C", seed.string(), "config", "user.name", "Installer Test"}) ||
        !write_commit(seed, "one", "first") ||
        !command({"git", "-C", seed.string(), "branch", "-M", "master"}) ||
        !command({"git", "-C", seed.string(), "remote", "add", "origin", remote.string()}) ||
        !command({"git", "-C", seed.string(), "push", "-u", "origin", "master"}) ||
        !command({"git", "clone", remote.string(), live.string()})) {
        std::cerr << "could not create local Git integration fixture\n";
        fs::remove_all(root, ignored);
        return 1;
    }

    const auto first_head = baas_installer::repository_head(live);
    fs::remove(live / ".git" / "FETCH_HEAD", ignored);
    auto unchanged = baas_installer::prepare_git_repository(
        {remote.string()}, live, staging, "refs/heads/master", {});
    if (!unchanged.success || unchanged.mode != baas_installer::RepositoryMode::Unchanged ||
        unchanged.commit != first_head || fs::exists(live / ".git" / "FETCH_HEAD")) {
        std::cerr << "matching remote head must skip fetch and clone\n";
        fs::remove_all(root, ignored);
        return 1;
    }

    if (!write_commit(seed, "two", "second") ||
        !command({"git", "-C", seed.string(), "push", "origin", "master"})) {
        std::cerr << "could not advance local Git remote\n";
        fs::remove_all(root, ignored);
        return 1;
    }
    std::string visible_chunks;
    auto incremental = baas_installer::prepare_git_repository(
        {remote.string()}, live, staging, "refs/heads/master",
        [&](std::string_view, std::string_view, std::string_view chunk) { visible_chunks.append(chunk); });
    if (!incremental.success || incremental.mode != baas_installer::RepositoryMode::Incremental ||
        incremental.commit == first_head || baas_installer::repository_head(live) != first_head ||
        !fs::exists(live / ".git" / "FETCH_HEAD") || visible_chunks.empty()) {
        std::cerr << "changed remote must fetch without changing the live work tree\n";
        fs::remove_all(root, ignored);
        return 1;
    }
    std::string apply_error;
    if (!baas_installer::apply_git_update(incremental, live, apply_error) ||
        baas_installer::repository_head(live) != incremental.commit || !fs::is_directory(live / ".git")) {
        std::cerr << "incremental Git apply failed: " << apply_error << '\n';
        fs::remove_all(root, ignored);
        return 1;
    }

    const auto corrupt = root / "corrupt";
    fs::create_directories(corrupt / ".git" / "objects");
    const auto full_staging = root / "full-staging";
    auto full = baas_installer::prepare_git_repository(
        {remote.string()}, corrupt, full_staging, "refs/heads/master", {});
    if (!full.success || full.mode != baas_installer::RepositoryMode::Full ||
        baas_installer::repository_head(full_staging) != incremental.commit) {
        std::cerr << "corrupt repository must prepare a full staged clone\n";
        fs::remove_all(root, ignored);
        return 1;
    }

#ifdef BAAS_INSTALLER_TEST_HAS_LIBGIT2
    if (!command({"git", "-C", seed.string(), "checkout", "-b", "windows-x64"}) ||
        !command({"git", "-C", seed.string(), "push", "origin", "windows-x64"})) {
        std::cerr << "could not create OCR-style remote branch\n";
        return 1;
    }
    const auto libgit_staging = root / "libgit-staging";
    std::string libgit_chunks;
    const char* inherited_path = std::getenv("PATH");
    const std::string saved_path = inherited_path ? inherited_path : "";
#ifdef _WIN32
    _putenv_s("PATH", "");
#else
    setenv("PATH", "", 1);
#endif
    auto libgit = baas_installer::prepare_git_repository(
        {remote.string()}, root / "missing", libgit_staging, "refs/heads/windows-x64",
        [&](std::string_view, std::string_view backend, std::string_view chunk) {
            if (backend == "libgit2") libgit_chunks.append(chunk);
        });
#ifdef _WIN32
    _putenv_s("PATH", saved_path.c_str());
#else
    setenv("PATH", saved_path.c_str(), 1);
#endif
    if (!libgit.success || libgit.backend != baas_installer::GitBackend::Libgit2 ||
        baas_installer::repository_head(libgit_staging).empty() || libgit_chunks.empty()) {
        std::cerr << "libgit2 did not clone and report progress for an OCR remote branch: " << libgit.error << '\n';
        return 1;
    }
#endif

    fs::remove_all(root, ignored);
    return 0;
}
