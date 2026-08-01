#pragma once

#include <filesystem>
#include <string>
#include <vector>

namespace baas_installer {

enum class GitBackend { GitCli, Libgit2, None };

struct GitResult {
    bool success{};
    GitBackend backend{GitBackend::None};
    std::string source;
    std::string commit;
    std::string error;
};

bool git_cli_available();
std::string git_backend_name(GitBackend backend);
std::string repository_head(const std::filesystem::path& repository);

// Works exclusively against `destination`, which must be a staging directory.
// Sources are tried in supplied order. Git CLI is always attempted before the
// built-in libgit2 backend for every source.
GitResult clone_repository(
    const std::vector<std::string>& sources,
    const std::filesystem::path& destination,
    const std::string& revision = {});

}  // namespace baas_installer
