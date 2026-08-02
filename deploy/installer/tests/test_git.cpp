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

std::string file_url(const fs::path& path) {
#ifdef _WIN32
    return "file:///" + path.generic_string();
#else
    return "file://" + path.generic_string();
#endif
}

bool write_commit(const fs::path& repository, const std::string& value, const std::string& message) {
    std::ofstream(repository / "payload.txt", std::ios::trunc) << value;
    return command({"git", "-C", repository.string(), "add", "payload.txt"}) &&
           command({"git", "-C", repository.string(), "commit", "-m", message});
}
}

int main() {
    const auto attempts = baas_installer::git_attempt_order({"source-a", "source-b"}, true, true);
    const auto fallback_attempts = baas_installer::git_attempt_order({"source-a", "source-b"}, false, true);
    if (attempts.size() != 2 || attempts[0] != std::pair{baas_installer::GitBackend::GitCli, std::string("source-a")} ||
        attempts[1] != std::pair{baas_installer::GitBackend::GitCli, std::string("source-b")} ||
        fallback_attempts.size() != 2 ||
        fallback_attempts[0] != std::pair{baas_installer::GitBackend::Libgit2, std::string("source-a")} ||
        fallback_attempts[1] != std::pair{baas_installer::GitBackend::Libgit2, std::string("source-b")}) {
        std::cerr << "libgit2 must be used only when the installed Git CLI is unavailable\n";
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
    const auto deep_live = root / "deep-live";
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
        !command({"git", "clone", remote.string(), live.string()}) ||
        !command({"git", "clone", remote.string(), deep_live.string()})) {
        std::cerr << "could not create local Git integration fixture\n";
        fs::remove_all(root, ignored);
        return 1;
    }

    const auto first_head = baas_installer::repository_head(live);
    // Treat the primary fixture as a previously installer-managed depth-one
    // checkout. The separate deep fixture verifies one-time normalization.
    std::ofstream(live / ".git" / "shallow", std::ios::trunc) << first_head << '\n';
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

    const auto deep_staging = root / "deep-staging";
    auto normalized = baas_installer::prepare_git_repository(
        {remote.string()}, deep_live, deep_staging, "refs/heads/master", {}, ranking_cache,
        baas_installer::SourceKind::MainGit);
    if (!normalized.success || normalized.mode != baas_installer::RepositoryMode::Full ||
        output({"git", "-C", deep_staging.string(), "rev-parse", "--is-shallow-repository"}) != "true" ||
        output({"git", "-C", deep_staging.string(), "rev-list", "--count", "HEAD"}) != "1") {
        std::cerr << "matching legacy repository was not normalized through a fresh depth-one clone\n";
        fs::remove_all(root, ignored);
        return 1;
    }

    const auto fallback_staging = root / "fallback-staging";
    const auto missing_remote = (root / "missing-remote.git").string();
    auto fallback = baas_installer::prepare_git_repository(
        {missing_remote, remote.string()}, root / "missing-fallback-live", fallback_staging,
        "refs/heads/master", {}, {}, baas_installer::SourceKind::MainGit,
        [&](const std::string& source, const std::string&, std::chrono::milliseconds) {
            return baas_installer::GitRemoteHead{source, first_head, source == missing_remote ? 1LL : 2LL, true};
        });
    if (!fallback.success || fallback.source != remote.string() ||
        fallback.mode != baas_installer::RepositoryMode::Full) {
        std::cerr << "failed real fetch did not fall back to the next successfully probed Git source\n";
        fs::remove_all(root, ignored);
        return 1;
    }

    const auto unavailable_staging = root / "unavailable-staging";
    auto unavailable = baas_installer::prepare_git_repository(
        {remote.string()}, root / "missing-unavailable", unavailable_staging, "refs/heads/master", {}, {},
        baas_installer::SourceKind::MainGit,
        [](const std::string& source, const std::string&, std::chrono::milliseconds) {
            return baas_installer::GitRemoteHead{source, {}, -1, false};
        });
    if (unavailable.success || unavailable.backend != baas_installer::GitBackend::GitCli ||
        fs::exists(unavailable_staging)) {
        std::cerr << "a source rejected by the ten-second CLI probe must not be downloaded again with libgit2\n";
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
    if (!baas_installer::finalize_git_repository(live, incremental.backend, apply_error)) {
        std::cerr << "successful Git validation rejected a depth-one repository: " << apply_error << '\n';
        fs::remove_all(root, ignored);
        return 1;
    }
    if (!baas_installer::compact_git_repository(live, incremental.backend, apply_error)) {
        std::cerr << "Git compaction failed: " << apply_error << '\n';
        fs::remove_all(root, ignored);
        return 1;
    }
    if (
        output({"git", "-C", live.string(), "rev-parse", "--is-shallow-repository"}) != "true" ||
        output({"git", "-C", live.string(), "rev-list", "--count", "HEAD"}) != "1" ||
        !output({"git", "-C", live.string(), "for-each-ref", "--format=%(refname)"}).empty() ||
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
        !write_commit(seed, "three", "windows branch") ||
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
        {file_url(remote)}, root / "missing", libgit_staging, "windows-x64",
        [&](std::string_view, std::string_view backend, std::string_view chunk) {
            if (backend == "libgit2") libgit_chunks.append(chunk);
        });
#ifdef _WIN32
    _putenv_s("PATH", saved_path.c_str());
#else
    setenv("PATH", saved_path.c_str(), 1);
#endif
    if (libgit.success) {
        if (libgit.backend != baas_installer::GitBackend::Libgit2 ||
            baas_installer::repository_head(libgit_staging).empty() || libgit_chunks.empty() ||
            output({"git", "-C", libgit_staging.string(), "rev-parse", "--is-shallow-repository"}) != "true" ||
            output({"git", "-C", libgit_staging.string(), "rev-list", "--count", "HEAD"}) != "1" ||
            !output({"git", "-C", libgit_staging.string(), "for-each-ref", "--format=%(refname)"}).empty() ||
            !output({"git", "-C", libgit_staging.string(), "fsck", "--unreachable"}).empty()) {
            std::cerr << "successful libgit2 clone was not a strict single-commit repository\n";
            return 1;
        }
    } else if (libgit.error.empty() || fs::exists(libgit_staging)) {
        // Some libgit2 builds reject shallow clones through the local file
        // transport. Production sources are HTTP(S); the unsupported test
        // transport must fail closed without leaving a full repository.
        std::cerr << "unsupported libgit2 local transport did not fail closed\n";
        return 1;
    }
    const auto rejected_staging = root / "libgit-rejected-local-path";
#ifdef _WIN32
    _putenv_s("PATH", "");
#else
    setenv("PATH", "", 1);
#endif
    auto rejected_local = baas_installer::clone_repository(
        {remote.string()}, rejected_staging, "windows-x64");
#ifdef _WIN32
    _putenv_s("PATH", saved_path.c_str());
#else
    setenv("PATH", saved_path.c_str(), 1);
#endif
    if (rejected_local.success || fs::exists(rejected_staging)) {
        std::cerr << "libgit2 accepted a local-path source that cannot guarantee depth one\n";
        return 1;
    }
    if (libgit.success) {
        const auto libgit_existing_staging = root / "libgit-existing-staging";
        const auto live_before_libgit = baas_installer::repository_head(live);
#ifdef _WIN32
        _putenv_s("PATH", "");
#else
        setenv("PATH", "", 1);
#endif
        auto libgit_existing = baas_installer::prepare_git_repository(
            {file_url(remote)}, live, libgit_existing_staging, "windows-x64", {});
#ifdef _WIN32
        _putenv_s("PATH", saved_path.c_str());
#else
        setenv("PATH", saved_path.c_str(), 1);
#endif
        if (!libgit_existing.success || libgit_existing.backend != baas_installer::GitBackend::Libgit2 ||
            libgit_existing.mode != baas_installer::RepositoryMode::Full ||
            !fs::is_directory(libgit_existing_staging / ".git") ||
            output({"git", "-C", libgit_existing_staging.string(), "rev-parse", "--is-shallow-repository"}) != "true" ||
            output({"git", "-C", libgit_existing_staging.string(), "rev-list", "--count", "HEAD"}) != "1" ||
            !output({"git", "-C", libgit_existing_staging.string(), "for-each-ref", "--format=%(refname)"}).empty() ||
            !output({"git", "-C", libgit_existing_staging.string(), "fsck", "--unreachable"}).empty() ||
            baas_installer::repository_head(live) != live_before_libgit) {
            std::cerr << "libgit2 existing update was not prepared as a fresh staged branch clone: "
                      << libgit_existing.error << " success=" << libgit_existing.success
                      << " backend=" << baas_installer::git_backend_name(libgit_existing.backend)
                      << " mode=" << static_cast<int>(libgit_existing.mode)
                      << " staging=" << fs::is_directory(libgit_existing_staging / ".git")
                      << " live-before=" << live_before_libgit
                      << " live-after=" << baas_installer::repository_head(live) << '\n';
            return 1;
        }
    }
#endif

    fs::remove_all(root, ignored);
    return 0;
}
