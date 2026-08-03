#pragma once

#include "baas_installer/sources.hpp"

#include <chrono>
#include <filesystem>
#include <functional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace baas_installer {

enum class GitBackend { GitCli, Libgit2, None };
enum class RepositoryMode { Unchanged, Incremental, Full };
using ProcessObserver = std::function<void(std::string_view task, std::string_view backend, std::string_view chunk)>;

struct GitRemoteHead {
    std::string source;
    std::string commit;
    long long latency_ms{-1};
    bool available{};
};

using GitRemoteProbe = std::function<GitRemoteHead(
    const std::string& source, const std::string& revision, std::chrono::milliseconds timeout)>;

struct GitResult {
    bool success{};
    GitBackend backend{GitBackend::None};
    std::string source;
    std::string commit;
    std::string error;
    RepositoryMode mode{RepositoryMode::Full};
    std::string previous_commit;
    std::filesystem::path staging_path;
};

bool git_cli_available();
std::string git_backend_name(GitBackend backend);
std::string repository_head(const std::filesystem::path& repository);
std::vector<std::pair<GitBackend, std::string>> git_attempt_order(
    const std::vector<std::string>& sources, bool cli_available, bool libgit2_available);

// Works exclusively against `destination`, which must be a staging directory.
// Sources are tried in supplied order. An installed Git CLI is authoritative;
// libgit2 is used only when the CLI is unavailable.
GitResult clone_repository(
    const std::vector<std::string>& sources,
    const std::filesystem::path& destination,
    const std::string& revision = {});

GitResult prepare_git_repository(
    const std::vector<std::string>& sources,
    const std::filesystem::path& live_repository,
    const std::filesystem::path& staging_directory,
    const std::string& revision,
    const ProcessObserver& observer,
    const std::filesystem::path& ranking_cache = {},
    SourceKind source_kind = SourceKind::MainGit,
    GitRemoteProbe remote_probe = {});

bool apply_git_update(const GitResult& prepared,
                      const std::filesystem::path& live_repository,
                      std::string& error,
                      const ProcessObserver& observer = {});

bool finalize_git_repository(const std::filesystem::path& repository,
                             GitBackend backend,
                             std::string& error);
bool compact_git_repository(const std::filesystem::path& repository,
                            GitBackend backend,
                            std::string& error) noexcept;

}  // namespace baas_installer
