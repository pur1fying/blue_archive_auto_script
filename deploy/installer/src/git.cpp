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

std::map<std::string, std::string> git_environment() {
    return {{"GIT_TERMINAL_PROMPT", "0"}, {"GCM_INTERACTIVE", "Never"}, {"GIT_ASKPASS", ""}, {"SSH_ASKPASS", ""}};
}

ProcessResult hidden_git(std::vector<std::string> arguments) {
    ProcessSpec spec;
    spec.arguments = std::move(arguments);
    spec.environment = git_environment();
    return run_process(spec);
}

int visible_git(std::vector<std::string> arguments, const ProcessObserver& observer) {
    ProcessSpec spec;
    spec.arguments = std::move(arguments);
    spec.environment = git_environment();
    spec.use_pty = true;
    if (observer) observer("repository", "git-cli", "Starting Git operation\r");
    if (observer) spec.on_chunk = [&](const std::string_view chunk) { observer("repository", "git-cli", chunk); };
    return observer ? run_terminal_process(spec).exit_code : run_process(spec).exit_code;
}

std::string first_token(const std::string& output) {
    std::istringstream input(output);
    std::string token;
    input >> token;
    return token;
}

std::string remote_head_cli(const std::string& source, const std::string& revision) {
    const auto wanted = revision.empty() ? "HEAD" : revision;
    const auto result = hidden_git({"git", "ls-remote", source, wanted});
    return result.exit_code == 0 ? first_token(result.output) : std::string{};
}

bool valid_cli_repository(const fs::path& repository) {
    const auto result = hidden_git({"git", "-C", repository.string(), "rev-parse", "--is-inside-work-tree"});
    return result.exit_code == 0 && first_token(result.output) == "true";
}

GitResult clone_with_cli(const std::string& source, const fs::path& destination, const std::string& revision,
                         const ProcessObserver& observer = {}) {
    std::error_code ignored;
    fs::remove_all(destination, ignored);
    fs::create_directories(destination.parent_path(), ignored);
    if (visible_git({"git", "clone", "--filter=blob:none", "--no-checkout", source, destination.string()}, observer) != 0) {
        return {false, GitBackend::GitCli, source, {}, "git clone failed"};
    }
    const std::string wanted = revision.empty() ? "HEAD" : revision;
    if (visible_git({"git", "-C", destination.string(), "checkout", "--force", wanted}, observer) != 0) {
        fs::remove_all(destination, ignored);
        return {false, GitBackend::GitCli, source, {}, "git checkout failed"};
    }
    return {true, GitBackend::GitCli, source, wanted, {}};
}

#ifdef BAAS_INSTALLER_HAS_LIBGIT2
struct Libgit2Progress {
    ProcessObserver observer;
    int last_percent{-1};
};

void emit_libgit2(Libgit2Progress* progress, const std::string& message) {
    if (progress && progress->observer) progress->observer("repository", "libgit2", message);
}

int transfer_progress(const git_indexer_progress* stats, void* payload) {
    auto* progress = static_cast<Libgit2Progress*>(payload);
    const int percent = stats && stats->total_objects != 0
        ? static_cast<int>((100ULL * stats->received_objects) / stats->total_objects) : 0;
    if (progress && percent != progress->last_percent) {
        progress->last_percent = percent;
        std::ostringstream output;
        output << "Receiving objects " << (stats ? stats->received_objects : 0) << "/"
               << (stats ? stats->total_objects : 0) << " (" << percent << "%)\r";
        emit_libgit2(progress, output.str());
    }
    return 0;
}

void checkout_progress(const char*, const size_t completed, const size_t total, void* payload) {
    auto* progress = static_cast<Libgit2Progress*>(payload);
    const int percent = total != 0 ? static_cast<int>((100ULL * completed) / total) : 0;
    if (progress && percent != progress->last_percent) {
        progress->last_percent = percent;
        emit_libgit2(progress, "Checking out files " + std::to_string(completed) + "/" +
                                   std::to_string(total) + " (" + std::to_string(percent) + "%)\r");
    }
}

std::string branch_name(const std::string& revision) {
    static const std::string prefix = "refs/heads/";
    return revision.starts_with(prefix) ? revision.substr(prefix.size()) : std::string{};
}

GitResult clone_with_libgit2(const std::string& source, const fs::path& destination, const std::string& revision,
                             const ProcessObserver& observer = {}) {
    std::error_code ignored;
    fs::remove_all(destination, ignored);
    fs::create_directories(destination.parent_path(), ignored);
    git_libgit2_init();
    git_repository* repository = nullptr;
    git_clone_options options = GIT_CLONE_OPTIONS_INIT;
    Libgit2Progress progress{observer};
    options.fetch_opts.callbacks.transfer_progress = transfer_progress;
    options.fetch_opts.callbacks.payload = &progress;
    options.checkout_opts.progress_cb = checkout_progress;
    options.checkout_opts.progress_payload = &progress;
    const auto wanted_branch = branch_name(revision);
    if (!wanted_branch.empty()) options.checkout_branch = wanted_branch.c_str();
    emit_libgit2(&progress, "Starting libgit2 clone\r");
    const int cloned = git_clone(&repository, source.c_str(), destination.string().c_str(), &options);
    if (cloned != 0) {
        const auto* error = git_error_last();
        git_libgit2_shutdown();
        return {false, GitBackend::Libgit2, source, {}, error ? error->message : "libgit2 clone failed"};
    }
    if (!revision.empty()) {
        git_object* object = nullptr;
        const int resolved = git_revparse_single(&object, repository, revision.c_str());
        git_checkout_options checkout = GIT_CHECKOUT_OPTIONS_INIT;
        checkout.checkout_strategy = GIT_CHECKOUT_FORCE;
        checkout.progress_cb = checkout_progress;
        checkout.progress_payload = &progress;
        const int checked_out = resolved == 0 ? git_checkout_tree(repository, object, &checkout) : resolved;
        const int head_updated = checked_out == 0 && !wanted_branch.empty()
            ? git_repository_set_head(repository, revision.c_str())
            : (checked_out == 0 ? git_repository_set_head_detached(repository, git_object_id(object)) : checked_out);
        if (object != nullptr) git_object_free(object);
        if (checked_out != 0 || head_updated != 0) {
            const auto* error = git_error_last();
            git_repository_free(repository);
            git_libgit2_shutdown();
            fs::remove_all(destination, ignored);
            return {false, GitBackend::Libgit2, source, {}, error ? error->message : "libgit2 checkout failed"};
        }
    }
    git_repository_free(repository);
    git_libgit2_shutdown();
    emit_libgit2(&progress, "libgit2 clone completed\r");
    return {true, GitBackend::Libgit2, source, revision.empty() ? "HEAD" : revision, {}};
}

GitResult prepare_existing_with_libgit2(const std::vector<std::string>& sources, const fs::path& repository_path,
                                        const std::string& revision, const std::string& local_head,
                                        const ProcessObserver& observer = {}) {
    git_libgit2_init();
    git_repository* repository = nullptr;
    if (git_repository_open(&repository, repository_path.string().c_str()) != 0) {
        const auto* detail = git_error_last();
        const std::string error = detail ? detail->message : "libgit2 repository open failed";
        git_libgit2_shutdown();
        return {false, GitBackend::Libgit2, {}, {}, error};
    }
    GitResult last{false, GitBackend::Libgit2, {}, {}, "no libgit2 remote source succeeded"};
    Libgit2Progress progress{observer};
    const std::string wanted = revision.empty() ? "HEAD" : revision;
    for (const auto& source : sources) {
        git_remote* remote = nullptr;
        if (git_remote_create_anonymous(&remote, repository, source.c_str()) != 0) {
            const auto* detail = git_error_last();
            last = {false, GitBackend::Libgit2, source, {}, detail ? detail->message : "libgit2 remote create failed"};
            continue;
        }
        git_fetch_options options = GIT_FETCH_OPTIONS_INIT;
        options.callbacks.transfer_progress = transfer_progress;
        options.callbacks.payload = &progress;
        std::string remote_head;
        if (git_remote_connect(remote, GIT_DIRECTION_FETCH, &options.callbacks, &options.proxy_opts,
                               &options.custom_headers) == 0) {
            const git_remote_head** heads = nullptr;
            size_t count = 0;
            if (git_remote_ls(&heads, &count, remote) == 0) {
                for (size_t index = 0; index < count; ++index) {
                    if (heads[index] && wanted == heads[index]->name) {
                        char oid[GIT_OID_HEXSZ + 1]{};
                        git_oid_tostr(oid, sizeof(oid), &heads[index]->oid);
                        remote_head = oid;
                        break;
                    }
                }
            }
            git_remote_disconnect(remote);
        }
        if (remote_head.empty()) {
            const auto* detail = git_error_last();
            last = {false, GitBackend::Libgit2, source, {}, detail ? detail->message : "libgit2 remote lookup failed"};
            git_remote_free(remote);
            continue;
        }
        if (remote_head == local_head) {
            GitResult result{true, GitBackend::Libgit2, source, remote_head, {}};
            result.mode = RepositoryMode::Unchanged;
            result.previous_commit = local_head;
            git_remote_free(remote);
            git_repository_free(repository);
            git_libgit2_shutdown();
            return result;
        }
        const std::string refspec = "+" + wanted + ":refs/baas-installer/prepared";
        char* refspec_value = const_cast<char*>(refspec.c_str());
        git_strarray refspecs{&refspec_value, 1};
        if (git_remote_fetch(remote, &refspecs, &options, nullptr) == 0) {
            emit_libgit2(&progress, "libgit2 fetch completed\r");
            GitResult result{true, GitBackend::Libgit2, source, remote_head, {}};
            result.mode = RepositoryMode::Incremental;
            result.previous_commit = local_head;
            git_remote_free(remote);
            git_repository_free(repository);
            git_libgit2_shutdown();
            return result;
        }
        const auto* detail = git_error_last();
        last = {false, GitBackend::Libgit2, source, {}, detail ? detail->message : "libgit2 fetch failed"};
        git_remote_free(remote);
    }
    git_repository_free(repository);
    git_libgit2_shutdown();
    return last;
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

std::vector<std::pair<GitBackend, std::string>> git_attempt_order(
    const std::vector<std::string>& sources, const bool cli_available, const bool libgit2_available) {
    std::vector<std::pair<GitBackend, std::string>> attempts;
    if (cli_available) for (const auto& source : sources) attempts.emplace_back(GitBackend::GitCli, source);
    if (libgit2_available) for (const auto& source : sources) attempts.emplace_back(GitBackend::Libgit2, source);
    return attempts;
}

std::string repository_head(const fs::path& repository) {
    if (git_cli_available()) {
        const auto result = hidden_git({"git", "-C", repository.string(), "rev-parse", "HEAD"});
        if (result.exit_code == 0) return first_token(result.output);
    }
#ifdef BAAS_INSTALLER_HAS_LIBGIT2
    git_libgit2_init();
    git_repository* handle = nullptr;
    git_oid oid{};
    std::string value;
    if (git_repository_open(&handle, repository.string().c_str()) == 0 && git_reference_name_to_id(&oid, handle, "HEAD") == 0) {
        char text[GIT_OID_HEXSZ + 1]{};
        git_oid_tostr(text, sizeof(text), &oid);
        value = text;
    }
    if (handle) git_repository_free(handle);
    git_libgit2_shutdown();
    return value;
#else
    return {};
#endif
}

GitResult clone_repository(const std::vector<std::string>& sources, const fs::path& destination, const std::string& revision) {
    GitResult last{false, GitBackend::None, {}, {}, "no repository source succeeded"};
    const bool use_cli = git_cli_available();
    if (use_cli) {
        for (const auto& source : sources) {
            last = clone_with_cli(source, destination, revision);
            if (last.success) return last;
        }
    }
#ifdef BAAS_INSTALLER_HAS_LIBGIT2
    for (const auto& source : sources) {
            last = clone_with_libgit2(source, destination, revision);
        if (last.success) return last;
    }
#endif
    return last;
}

GitResult prepare_git_repository(const std::vector<std::string>& sources, const fs::path& live_repository,
                                 const fs::path& staging_directory, const std::string& revision,
                                 const ProcessObserver& observer) {
    GitResult last{false, GitBackend::None, {}, {}, "no repository source succeeded"};
    const bool use_cli = git_cli_available();
    const auto local_head = repository_head(live_repository);
    const bool valid_live = !local_head.empty() && (!use_cli || valid_cli_repository(live_repository));

    if (use_cli) {
        for (const auto& source : sources) {
            const auto remote_head = remote_head_cli(source, revision);
            if (remote_head.empty()) {
                last = {false, GitBackend::GitCli, source, {}, "git ls-remote failed"};
                continue;
            }
            if (valid_live && local_head == remote_head) {
                GitResult result{true, GitBackend::GitCli, source, remote_head, {}};
                result.mode = RepositoryMode::Unchanged;
                result.previous_commit = local_head;
                return result;
            }
            if (valid_live) {
                if (visible_git({"git", "-C", live_repository.string(), "fetch", "--no-tags", "--depth", "1", source,
                                 remote_head}, observer) == 0) {
                    GitResult result{true, GitBackend::GitCli, source, remote_head, {}};
                    result.mode = RepositoryMode::Incremental;
                    result.previous_commit = local_head;
                    return result;
                }
                last = {false, GitBackend::GitCli, source, {}, "git fetch failed"};
                continue;
            }
            auto result = clone_with_cli(source, staging_directory, remote_head, observer);
            if (result.success) {
                result.mode = RepositoryMode::Full;
                result.commit = repository_head(staging_directory);
                result.staging_path = staging_directory;
                return result;
            }
            last = result;
        }
    }

#ifdef BAAS_INSTALLER_HAS_LIBGIT2
    if (valid_live) {
        auto result = prepare_existing_with_libgit2(sources, live_repository, revision, local_head, observer);
        if (result.success) return result;
        last = result;
    } else {
        for (const auto& source : sources) {
            auto result = clone_with_libgit2(source, staging_directory, revision, observer);
            if (result.success) {
                result.mode = RepositoryMode::Full;
                result.commit = repository_head(staging_directory);
                result.staging_path = staging_directory;
                return result;
            }
            last = result;
        }
    }
#endif
    return last;
}

bool apply_git_update(const GitResult& prepared, const fs::path& live_repository, std::string& error,
                      const ProcessObserver& observer) {
    if (!prepared.success) {
        error = prepared.error.empty() ? "Git repository was not prepared" : prepared.error;
        return false;
    }
    if (prepared.mode == RepositoryMode::Unchanged) return true;
    if (prepared.mode == RepositoryMode::Full) {
        error = "full Git deployment must be applied by the install transaction";
        return false;
    }
    if (prepared.backend == GitBackend::GitCli) {
        if (visible_git({"git", "-C", live_repository.string(), "reset", "--hard", prepared.commit}, observer) == 0) {
            return true;
        }
        error = "git hard reset failed";
        return false;
    }
#ifdef BAAS_INSTALLER_HAS_LIBGIT2
    if (observer) observer("repository", "libgit2", "Applying libgit2 hard reset\r");
    git_libgit2_init();
    git_repository* repository = nullptr;
    git_object* object = nullptr;
    const int opened = git_repository_open(&repository, live_repository.string().c_str());
    const int resolved = opened == 0 ? git_revparse_single(&object, repository, prepared.commit.c_str()) : opened;
    const int reset = resolved == 0 ? git_reset(repository, object, GIT_RESET_HARD, nullptr) : resolved;
    if (object) git_object_free(object);
    if (repository) git_repository_free(repository);
    if (reset != 0) {
        const auto* detail = git_error_last();
        error = detail ? detail->message : "libgit2 hard reset failed";
    }
    git_libgit2_shutdown();
    if (reset == 0 && observer) observer("repository", "libgit2", "libgit2 hard reset completed\r");
    return reset == 0;
#else
    error = "libgit2 is not available";
    return false;
#endif
}

}  // namespace baas_installer
