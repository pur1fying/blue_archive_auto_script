#include "baas_installer/git.hpp"
#include "baas_installer/process.hpp"

#include <filesystem>
#include <sstream>

#ifdef BAAS_INSTALLER_HAS_LIBGIT2
#include <git2.h>
#endif

namespace fs = std::filesystem;

namespace baas_installer {
namespace {

GitResult clone_with_cli(const std::string& source, const fs::path& destination, const std::string& revision) {
    std::error_code ignored;
    fs::remove_all(destination, ignored);
    fs::create_directories(destination.parent_path(), ignored);
    if (run_process({"git", "clone", "--filter=blob:none", "--no-checkout", source, destination.string()}) != 0) {
        return {false, GitBackend::GitCli, source, {}, "git clone failed"};
    }
    const std::string wanted = revision.empty() ? "HEAD" : revision;
    if (run_process({"git", "-C", destination.string(), "checkout", "--force", wanted}) != 0) {
        fs::remove_all(destination, ignored);
        return {false, GitBackend::GitCli, source, {}, "git checkout failed"};
    }
    return {true, GitBackend::GitCli, source, wanted, {}};
}

#ifdef BAAS_INSTALLER_HAS_LIBGIT2
GitResult clone_with_libgit2(const std::string& source, const fs::path& destination, const std::string& revision) {
    std::error_code ignored;
    fs::remove_all(destination, ignored);
    fs::create_directories(destination.parent_path(), ignored);
    git_libgit2_init();
    git_repository* repository = nullptr;
    git_clone_options options = GIT_CLONE_OPTIONS_INIT;
    const int cloned = git_clone(&repository, source.c_str(), destination.string().c_str(), &options);
    if (cloned != 0) {
        const auto* error = git_error_last();
        git_libgit2_shutdown();
        return {false, GitBackend::Libgit2, source, {}, error ? error->message : "libgit2 clone failed"};
    }
    if (!revision.empty()) {
        git_object* object = nullptr;
        const int resolved = git_revparse_single(&object, repository, revision.c_str());
        const int checked_out = resolved == 0 ? git_checkout_tree(repository, object, nullptr) : resolved;
        if (object != nullptr) git_object_free(object);
        if (checked_out != 0) {
            const auto* error = git_error_last();
            git_repository_free(repository);
            git_libgit2_shutdown();
            fs::remove_all(destination, ignored);
            return {false, GitBackend::Libgit2, source, {}, error ? error->message : "libgit2 checkout failed"};
        }
    }
    git_repository_free(repository);
    git_libgit2_shutdown();
    return {true, GitBackend::Libgit2, source, revision.empty() ? "HEAD" : revision, {}};
}
#endif

}  // namespace

bool git_cli_available() {
#ifdef _WIN32
    return run_process({"git", "--version"}) == 0;
#else
    return run_process({"git", "--version"}) == 0;
#endif
}

std::string git_backend_name(const GitBackend backend) {
    switch (backend) {
        case GitBackend::GitCli: return "git-cli";
        case GitBackend::Libgit2: return "libgit2";
        default: return "none";
    }
}

std::string repository_head(const fs::path& repository) {
    if (!git_cli_available()) return {};
    ProcessSpec spec;
    spec.arguments = {"git", "-C", repository.string(), "rev-parse", "HEAD"};
    const auto result = run_process(spec);
    if (result.exit_code != 0) return {};
    std::istringstream input(result.output);
    std::string head;
    std::getline(input, head);
    if (!head.empty() && head.back() == '\r') head.pop_back();
    return head;
}

GitResult clone_repository(const std::vector<std::string>& sources, const fs::path& destination, const std::string& revision) {
    GitResult last{false, GitBackend::None, {}, {}, "no repository source succeeded"};
    const bool use_cli = git_cli_available();
    for (const auto& source : sources) {
        if (use_cli) {
            last = clone_with_cli(source, destination, revision);
            if (last.success) return last;
        }
#ifdef BAAS_INSTALLER_HAS_LIBGIT2
        last = clone_with_libgit2(source, destination, revision);
        if (last.success) return last;
#endif
    }
    return last;
}

}  // namespace baas_installer
