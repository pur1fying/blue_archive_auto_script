#include "baas_installer/git.hpp"
#include "baas_installer/process.hpp"

#include <chrono>
#include <atomic>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <cstdlib>
#include <thread>

namespace {
namespace fs = std::filesystem;

bool command(std::initializer_list<std::string> arguments) {
    return baas_installer::run_process(std::vector<std::string>(arguments)) == 0;
}

std::string output(std::initializer_list<std::string> arguments) {
    baas_installer::ProcessSpec spec;
    spec.arguments.assign(arguments);
    auto result = baas_installer::run_process(spec);
    while (!result.output.empty() && std::isspace(static_cast<unsigned char>(result.output.back()))) {
        result.output.pop_back();
    }
    return result.exit_code == 0 ? result.output : std::string{};
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
    const auto ranking_cache = root / ".baas-installer" / "source-ranking-v1.json";
    std::atomic<int> active_probes{0};
    std::atomic<int> maximum_probes{0};
    std::atomic<int> probe_calls{0};
    const auto parallel_probe = [&](const std::string& source, const std::string&,
                                    const std::chrono::milliseconds timeout) {
        ++probe_calls;
        const int current = ++active_probes;
        auto maximum = maximum_probes.load();
        while (current > maximum && !maximum_probes.compare_exchange_weak(maximum, current)) {}
        std::this_thread::sleep_for(std::chrono::milliseconds(source == "fast" ? 10 : 30));
        --active_probes;
        return baas_installer::GitRemoteHead{source, first_head, source == "fast" ? 10LL : 30LL,
                                             timeout == std::chrono::seconds(10)};
    };
    auto measured = baas_installer::prepare_git_repository(
        {"slow-a", "fast", "slow-b"}, live, staging, "refs/heads/master", {}, ranking_cache,
        baas_installer::SourceKind::MainGit, parallel_probe);
    if (!measured.success || measured.mode != baas_installer::RepositoryMode::Unchanged ||
        measured.source != "fast" || probe_calls != 3 || maximum_probes <= 1) {
        std::cerr << "uncached Git SHA probes must run concurrently and select the fastest valid response\n";
        fs::remove_all(root, ignored);
        return 1;
    }
    probe_calls = 0;
    maximum_probes = 0;
    measured = baas_installer::prepare_git_repository(
        {"slow-a", "fast", "slow-b"}, live, staging, "refs/heads/master", {}, ranking_cache,
        baas_installer::SourceKind::MainGit, parallel_probe);
    if (!measured.success || measured.source != "fast" || probe_calls != 1) {
        std::cerr << "cached Git SHA check must query only the preferred source\n";
        fs::remove_all(root, ignored);
        return 1;
    }
    fs::remove(live / ".git" / "FETCH_HEAD", ignored);
    auto unchanged = baas_installer::prepare_git_repository(
        {remote.string()}, live, staging, "refs/heads/master", {}, ranking_cache,
        baas_installer::SourceKind::MainGit);
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
        [&](std::string_view, std::string_view, std::string_view chunk) { visible_chunks.append(chunk); },
        ranking_cache, baas_installer::SourceKind::MainGit);
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
    if (!baas_installer::finalize_git_repository(live, incremental.backend, apply_error) ||
        output({"git", "-C", live.string(), "rev-parse", "--is-shallow-repository"}) != "true" ||
        output({"git", "-C", live.string(), "rev-list", "--count", "HEAD"}) != "1" ||
        output({"git", "-C", live.string(), "fsck", "--unreachable"}).find(first_head) != std::string::npos) {
        std::cerr << "successful Git finalization did not retain exactly one shallow commit\n";
        fs::remove_all(root, ignored);
        return 1;
    }

    const auto corrupt = root / "corrupt";
    fs::create_directories(corrupt / ".git" / "objects");
    const auto full_staging = root / "full-staging";
    auto full = baas_installer::prepare_git_repository(
        {remote.string()}, corrupt, full_staging, "refs/heads/master", {}, ranking_cache,
        baas_installer::SourceKind::MainGit);
    if (!full.success || full.mode != baas_installer::RepositoryMode::Full ||
        baas_installer::repository_head(full_staging) != incremental.commit ||
        output({"git", "-C", full_staging.string(), "rev-parse", "--is-shallow-repository"}) != "true" ||
        output({"git", "-C", full_staging.string(), "rev-list", "--count", "HEAD"}) != "1") {
        std::cerr << "corrupt repository must prepare a full shallow staged repository\n";
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
