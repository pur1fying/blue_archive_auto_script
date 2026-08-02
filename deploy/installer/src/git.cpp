#include "baas_installer/git.hpp"
#include "baas_installer/process.hpp"

#include <algorithm>
#include <chrono>
#include <cctype>
#include <filesystem>
#include <future>
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

ProcessResult hidden_git(std::vector<std::string> arguments,
                         const std::chrono::milliseconds timeout = std::chrono::milliseconds::zero()) {
    ProcessSpec spec;
    spec.arguments = std::move(arguments);
    spec.environment = git_environment();
    spec.timeout = timeout;
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

bool valid_commit(const std::string& value) {
    return value.size() == 40 && std::all_of(value.begin(), value.end(), [](const unsigned char character) {
        return std::isxdigit(character) != 0;
    });
}

GitRemoteHead remote_head_cli(const std::string& source, const std::string& revision,
                              const std::chrono::milliseconds timeout) {
    const auto wanted = revision.empty() ? "HEAD" : revision;
    const auto started = std::chrono::steady_clock::now();
    const auto result = hidden_git({"git", "ls-remote", source, wanted}, timeout);
    const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - started).count();
    const auto commit = result.exit_code == 0 ? first_token(result.output) : std::string{};
    return {source, valid_commit(commit) ? commit : std::string{}, elapsed,
            result.exit_code == 0 && valid_commit(commit)};
}

GitRemoteHead select_git_remote(const std::vector<std::string>& sources, const std::string& revision,
                                const fs::path& ranking_cache, const SourceKind source_kind,
                                GitRemoteProbe probe) {
    if (!probe) probe = remote_head_cli;
    constexpr auto timeout = std::chrono::seconds(10);
    auto cached = ranking_cache.empty()
        ? std::vector<RankedSource>{}
        : load_source_ranking(ranking_cache, source_kind, sources);
    if (!cached.empty()) {
        const auto preferred = std::find_if(cached.begin(), cached.end(), [](const RankedSource& source) {
            return source.preferred && source.available;
        });
        if (preferred != cached.end()) {
            auto observation = probe(preferred->url, revision, timeout);
            if (observation.available && valid_commit(observation.commit)) {
                for (auto& source : cached) {
                    source.preferred = source.url == observation.source;
                    if (source.preferred) {
                        source.latency_ms = observation.latency_ms;
                        source.commit = observation.commit;
                        source.failures = 0;
                        source.available = true;
                    }
                }
                save_source_ranking(ranking_cache, source_kind, cached);
                return observation;
            }
            record_source_failure(cached, preferred->url);
            preferred->available = false;
        }
    }

    std::vector<std::future<GitRemoteHead>> pending;
    std::vector<std::string> measured_sources;
    for (const auto& source : sources) {
        const auto failed_cached = std::find_if(cached.begin(), cached.end(), [&](const RankedSource& item) {
            return item.url == source && !item.available && item.preferred;
        });
        if (failed_cached != cached.end()) continue;
        measured_sources.push_back(source);
        pending.push_back(std::async(std::launch::async, [probe, source, revision] {
            return probe(source, revision, std::chrono::seconds(10));
        }));
    }
    std::vector<RankedSource> ranking;
    for (std::size_t index = 0; index < pending.size(); ++index) {
        auto result = pending[index].get();
        const bool available = result.available && valid_commit(result.commit) && result.latency_ms <= 10000;
        ranking.push_back({measured_sources[index], available ? result.latency_ms : -1, 0,
                           available ? result.commit : std::string{}, false, available});
    }
    for (const auto& source : sources) {
        if (std::find(measured_sources.begin(), measured_sources.end(), source) == measured_sources.end()) {
            const auto old = std::find_if(cached.begin(), cached.end(), [&](const RankedSource& item) {
                return item.url == source;
            });
            ranking.push_back(old == cached.end() ? RankedSource{source, -1, 1, {}, false, false} : *old);
        }
    }
    std::stable_sort(ranking.begin(), ranking.end(), [](const RankedSource& left, const RankedSource& right) {
        if (left.available != right.available) return left.available;
        return left.available && left.latency_ms < right.latency_ms;
    });
    const auto fastest = std::find_if(ranking.begin(), ranking.end(), [](const RankedSource& item) {
        return item.available;
    });
    if (fastest != ranking.end()) fastest->preferred = true;
    if (!ranking_cache.empty()) save_source_ranking(ranking_cache, source_kind, ranking);
    return fastest == ranking.end()
        ? GitRemoteHead{}
        : GitRemoteHead{fastest->url, fastest->commit, fastest->latency_ms, true};
}

bool valid_cli_repository(const fs::path& repository) {
    const auto result = hidden_git({"git", "-C", repository.string(), "rev-parse", "--is-inside-work-tree"});
    return result.exit_code == 0 && first_token(result.output) == "true";
}

GitResult clone_with_cli(const std::string& source, const fs::path& destination, const std::string& revision,
                         const std::string& commit,
                         const ProcessObserver& observer = {}) {
    std::error_code ignored;
    fs::remove_all(destination, ignored);
    fs::create_directories(destination.parent_path(), ignored);
    if (hidden_git({"git", "init", destination.string()}).exit_code != 0) {
        return {false, GitBackend::GitCli, source, {}, "git init failed"};
    }
    const std::string wanted = revision.empty() ? "HEAD" : revision;
    if (visible_git({"git", "-C", destination.string(), "fetch", "--depth=1", "--no-tags", source, wanted}, observer) != 0 ||
        hidden_git({"git", "-C", destination.string(), "checkout", "--detach", "--force", commit}).exit_code != 0) {
        fs::remove_all(destination, ignored);
        return {false, GitBackend::GitCli, source, {}, "shallow git fetch or checkout failed"};
    }
    return {true, GitBackend::GitCli, source, commit, {}};
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
    // libgit2's local filesystem transport rejects shallow fetches. Production
    // repository sources are HTTP(S), where depth-one is mandatory.
    if (source.find("://") != std::string::npos) options.fetch_opts.depth = 1;
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
            const auto remote = remote_head_cli(source, revision, std::chrono::seconds(10));
            if (!remote.available) continue;
            last = clone_with_cli(source, destination, revision, remote.commit);
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
                                 const ProcessObserver& observer, const fs::path& ranking_cache,
                                 const SourceKind source_kind, GitRemoteProbe remote_probe) {
    GitResult last{false, GitBackend::None, {}, {}, "no repository source succeeded"};
    const bool use_cli = git_cli_available();
    const auto local_head = repository_head(live_repository);
    const bool valid_live = !local_head.empty() && (!use_cli || valid_cli_repository(live_repository));

    if (use_cli) {
        const auto selected = select_git_remote(sources, revision, ranking_cache, source_kind, std::move(remote_probe));
        if (selected.available) {
            if (valid_live && local_head == selected.commit) {
                GitResult result{true, GitBackend::GitCli, selected.source, selected.commit, {}};
                result.mode = RepositoryMode::Unchanged;
                result.previous_commit = local_head;
                return result;
            }
            if (valid_live) {
                const auto wanted = revision.empty() ? "HEAD" : revision;
                if (visible_git({"git", "-C", live_repository.string(), "fetch", "--depth=1", "--no-tags",
                                 selected.source, wanted}, observer) == 0) {
                    GitResult result{true, GitBackend::GitCli, selected.source, selected.commit, {}};
                    result.mode = RepositoryMode::Incremental;
                    result.previous_commit = local_head;
                    return result;
                }
                last = {false, GitBackend::GitCli, selected.source, {}, "git fetch failed"};
            } else {
                auto result = clone_with_cli(selected.source, staging_directory, revision, selected.commit, observer);
                if (result.success) {
                    result.mode = RepositoryMode::Full;
                    result.commit = repository_head(staging_directory);
                    result.staging_path = staging_directory;
                    return result;
                }
                last = result;
            }
        } else {
            last = {false, GitBackend::GitCli, {}, {}, "every Git source failed its remote SHA check"};
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

bool finalize_git_repository(const fs::path& repository, const GitBackend backend, std::string& error) {
    error.clear();
    if (backend != GitBackend::GitCli) {
        // Without the CLI, updates deploy a fresh depth-one libgit2 staging
        // repository, so there are no previous live objects to prune.
        return true;
    }
    for (const auto& arguments : std::vector<std::vector<std::string>>{
             {"git", "-C", repository.string(), "checkout", "--detach", "--force", "HEAD"},
             {"git", "-C", repository.string(), "reflog", "expire", "--expire=now", "--all"},
             {"git", "-C", repository.string(), "gc", "--prune=now"}}) {
        if (hidden_git(arguments).exit_code != 0) {
            error = "could not compact the shallow Git repository";
            return false;
        }
    }
    const auto shallow = hidden_git({"git", "-C", repository.string(), "rev-parse", "--is-shallow-repository"});
    const auto count = hidden_git({"git", "-C", repository.string(), "rev-list", "--count", "HEAD"});
    if (shallow.exit_code != 0 || first_token(shallow.output) != "true" ||
        count.exit_code != 0 || first_token(count.output) != "1") {
        error = "Git repository did not retain exactly one shallow commit";
        return false;
    }
    return true;
}

}  // namespace baas_installer
