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

struct GitRemoteSelection {
    std::vector<GitRemoteHead> candidates;
    bool cache_hit{};
};

bool contains_source(const std::vector<std::string>& values, const std::string& source) {
    return std::find(values.begin(), values.end(), source) != values.end();
}

GitRemoteSelection select_git_remotes(const std::vector<std::string>& sources, const std::string& revision,
                                      const fs::path& ranking_cache, const SourceKind source_kind,
                                      const GitRemoteProbe& probe,
                                      const std::vector<std::string>& excluded = {},
                                      const bool allow_cached = true) {
    constexpr auto timeout = std::chrono::seconds(10);
    auto cached = ranking_cache.empty()
        ? std::vector<RankedSource>{}
        : load_source_ranking(ranking_cache, source_kind, sources);
    if (allow_cached && !cached.empty()) {
        const auto preferred = std::find_if(cached.begin(), cached.end(), [](const RankedSource& source) {
            return source.preferred && source.available;
        });
        if (preferred != cached.end() && !contains_source(excluded, preferred->url)) {
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
                return {{observation}, true};
            }
            record_source_failure(cached, preferred->url);
            preferred->available = false;
            preferred->preferred = false;
        }
    }

    std::vector<std::future<GitRemoteHead>> pending;
    std::vector<std::string> measured_sources;
    for (const auto& source : sources) {
        if (contains_source(excluded, source)) continue;
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
    GitRemoteSelection selection;
    for (const auto& item : ranking) {
        if (item.available && valid_commit(item.commit)) {
            selection.candidates.push_back({item.url, item.commit, item.latency_ms, true});
        }
    }
    return selection;
}

void mark_git_source_failure(const fs::path& ranking_cache, const SourceKind source_kind,
                             const std::vector<std::string>& sources, const std::string& failed) {
    if (ranking_cache.empty()) return;
    auto ranking = load_source_ranking(ranking_cache, source_kind, sources);
    if (ranking.empty()) return;
    record_source_failure(ranking, failed);
    for (auto& item : ranking) {
        if (item.url == failed) {
            item.available = false;
            item.preferred = false;
        }
    }
    const auto next = std::find_if(ranking.begin(), ranking.end(), [](const RankedSource& item) {
        return item.available;
    });
    if (next != ranking.end()) next->preferred = true;
    save_source_ranking(ranking_cache, source_kind, ranking);
}

bool valid_cli_repository(const fs::path& repository) {
    const auto result = hidden_git({"git", "-C", repository.string(), "rev-parse", "--is-inside-work-tree"});
    return result.exit_code == 0 && first_token(result.output) == "true";
}

bool depth_one_cli_repository(const fs::path& repository) {
    const auto shallow = hidden_git({"git", "-C", repository.string(), "rev-parse", "--is-shallow-repository"});
    const auto count = hidden_git({"git", "-C", repository.string(), "rev-list", "--count", "HEAD"});
    return shallow.exit_code == 0 && first_token(shallow.output) == "true" &&
           count.exit_code == 0 && first_token(count.output) == "1";
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
struct Libgit2Runtime {
    Libgit2Runtime() {
        git_libgit2_init();
        git_libgit2_opts(GIT_OPT_SET_SERVER_CONNECT_TIMEOUT, 10000);
        git_libgit2_opts(GIT_OPT_SET_SERVER_TIMEOUT, 10000);
    }
    ~Libgit2Runtime() { git_libgit2_shutdown(); }
};

void ensure_libgit2() {
    static Libgit2Runtime runtime;
    (void)runtime;
}

std::string normalized_remote_ref(const std::string& revision) {
    if (revision.empty()) return "HEAD";
    return revision.starts_with("refs/") ? revision : "refs/heads/" + revision;
}

GitRemoteHead remote_head_libgit2(const std::string& source, const std::string& revision,
                                  const std::chrono::milliseconds timeout) {
    ensure_libgit2();
    const auto started = std::chrono::steady_clock::now();
    git_remote* remote = nullptr;
    std::string commit;
    if (git_remote_create_anonymous(&remote, nullptr, source.c_str()) == 0) {
        git_remote_callbacks callbacks = GIT_REMOTE_CALLBACKS_INIT;
        git_proxy_options proxy = GIT_PROXY_OPTIONS_INIT;
        git_strarray headers{};
        if (git_remote_connect(remote, GIT_DIRECTION_FETCH, &callbacks, &proxy, &headers) == 0) {
            const git_remote_head** heads = nullptr;
            size_t count = 0;
            const auto wanted = normalized_remote_ref(revision);
            if (git_remote_ls(&heads, &count, remote) == 0) {
                for (size_t index = 0; index < count; ++index) {
                    if (heads[index] && wanted == heads[index]->name) {
                        char oid[GIT_OID_HEXSZ + 1]{};
                        git_oid_tostr(oid, sizeof(oid), &heads[index]->oid);
                        commit = oid;
                        break;
                    }
                }
            }
            git_remote_disconnect(remote);
        }
        git_remote_free(remote);
    }
    const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - started).count();
    const bool available = elapsed <= timeout.count() && valid_commit(commit);
    return {source, available ? commit : std::string{}, elapsed, available};
}

bool depth_one_libgit2_repository(const fs::path& repository_path) {
    ensure_libgit2();
    git_repository* repository = nullptr;
    git_revwalk* walk = nullptr;
    git_reference_iterator* references = nullptr;
    bool valid = false;
    if (git_repository_open(&repository, repository_path.string().c_str()) == 0 &&
        git_repository_is_shallow(repository) == 1 && git_revwalk_new(&walk, repository) == 0 &&
        git_revwalk_push_head(walk) == 0) {
        git_oid oid{};
        std::size_t count = 0;
        while (count <= 1 && git_revwalk_next(&oid, walk) == 0) ++count;
        git_reference* reference = nullptr;
        const int iterator_created = git_reference_iterator_glob_new(&references, repository, "refs/*");
        const int next = iterator_created == 0 ? git_reference_next(&reference, references) : iterator_created;
        if (reference) git_reference_free(reference);
        valid = count == 1 && iterator_created == 0 && next == GIT_ITEROVER;
    }
    if (references) git_reference_iterator_free(references);
    if (walk) git_revwalk_free(walk);
    if (repository) git_repository_free(repository);
    return valid;
}

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
    if (revision.starts_with(prefix)) return revision.substr(prefix.size());
    // Production OCR revisions are supplied as a plain branch name such as
    // "windows-x64".  Tell libgit2 to clone that branch directly instead of
    // cloning the default branch and then failing a local revparse.
    return !revision.empty() && !revision.starts_with("refs/") ? revision : std::string{};
}

struct SingleBranchRemote {
    std::string refspec;
};

int create_single_branch_remote(git_remote** output, git_repository* repository, const char* name,
                                const char* url, void* payload) {
    const auto* single = static_cast<SingleBranchRemote*>(payload);
    return git_remote_create_with_fetchspec(output, repository, name, url, single->refspec.c_str());
}

bool detach_and_remove_refs(git_repository* repository, std::string& error) {
    git_reference* head = nullptr;
    git_reference_iterator* iterator = nullptr;
    git_reference* reference = nullptr;
    git_oid oid{};
    const int resolved = git_repository_head(&head, repository);
    if (resolved == 0) oid = *git_reference_target(head);
    const int detached = resolved == 0 ? git_repository_set_head_detached(repository, &oid) : resolved;
    if (head) git_reference_free(head);
    if (detached != 0 || git_reference_iterator_glob_new(&iterator, repository, "refs/*") != 0) {
        const auto* detail = git_error_last();
        error = detail ? detail->message : "could not detach libgit2 repository";
        if (iterator) git_reference_iterator_free(iterator);
        return false;
    }
    int next = 0;
    while ((next = git_reference_next(&reference, iterator)) == 0) {
        const int removed = git_reference_delete(reference);
        git_reference_free(reference);
        reference = nullptr;
        if (removed != 0) break;
    }
    if (reference) git_reference_free(reference);
    git_reference_iterator_free(iterator);
    if (next != GIT_ITEROVER) {
        const auto* detail = git_error_last();
        error = detail ? detail->message : "could not remove libgit2 repository refs";
        return false;
    }
    return true;
}

GitResult clone_with_libgit2(const std::string& source, const fs::path& destination, const std::string& revision,
                             const ProcessObserver& observer = {}) {
    if (source.find("://") == std::string::npos) {
        return {false, GitBackend::Libgit2, source, {},
                "libgit2 fallback requires a URL source to guarantee a depth-one clone"};
    }
    const auto wanted_branch = branch_name(revision);
    if (wanted_branch.empty()) {
        return {false, GitBackend::Libgit2, source, {},
                "libgit2 fallback requires a named branch to guarantee a single-branch clone"};
    }
    std::error_code ignored;
    fs::remove_all(destination, ignored);
    fs::create_directories(destination.parent_path(), ignored);
    ensure_libgit2();
    git_repository* repository = nullptr;
    git_clone_options options = GIT_CLONE_OPTIONS_INIT;
    Libgit2Progress progress{observer};
    options.fetch_opts.callbacks.transfer_progress = transfer_progress;
    options.fetch_opts.callbacks.payload = &progress;
    options.fetch_opts.depth = 1;
    options.fetch_opts.download_tags = GIT_REMOTE_DOWNLOAD_TAGS_NONE;
    options.checkout_opts.progress_cb = checkout_progress;
    options.checkout_opts.progress_payload = &progress;
    options.checkout_branch = wanted_branch.c_str();
    SingleBranchRemote single_remote{
        "+refs/heads/" + wanted_branch + ":refs/remotes/origin/" + wanted_branch};
    options.remote_cb = create_single_branch_remote;
    options.remote_cb_payload = &single_remote;
    emit_libgit2(&progress, "Starting libgit2 clone\r");
    const int cloned = git_clone(&repository, source.c_str(), destination.string().c_str(), &options);
    if (cloned != 0) {
        const auto* detail = git_error_last();
        const std::string message = detail ? detail->message : "libgit2 clone failed";
        return {false, GitBackend::Libgit2, source, {}, message};
    }
    std::string cleanup_error;
    if (!detach_and_remove_refs(repository, cleanup_error)) {
        git_repository_free(repository);
        fs::remove_all(destination, ignored);
        return {false, GitBackend::Libgit2, source, {}, cleanup_error};
    }
    git_repository_free(repository);
    emit_libgit2(&progress, "libgit2 clone completed\r");
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

std::vector<std::pair<GitBackend, std::string>> git_attempt_order(
    const std::vector<std::string>& sources, const bool cli_available, const bool libgit2_available) {
    std::vector<std::pair<GitBackend, std::string>> attempts;
    if (cli_available) {
        for (const auto& source : sources) attempts.emplace_back(GitBackend::GitCli, source);
    } else if (libgit2_available) {
        for (const auto& source : sources) attempts.emplace_back(GitBackend::Libgit2, source);
    }
    return attempts;
}

std::string repository_head(const fs::path& repository) {
    if (git_cli_available()) {
        const auto result = hidden_git({"git", "-C", repository.string(), "rev-parse", "HEAD"});
        if (result.exit_code == 0) return first_token(result.output);
    }
#ifdef BAAS_INSTALLER_HAS_LIBGIT2
    ensure_libgit2();
    git_repository* handle = nullptr;
    git_oid oid{};
    std::string value;
    if (git_repository_open(&handle, repository.string().c_str()) == 0 && git_reference_name_to_id(&oid, handle, "HEAD") == 0) {
        char text[GIT_OID_HEXSZ + 1]{};
        git_oid_tostr(text, sizeof(text), &oid);
        value = text;
    }
    if (handle) git_repository_free(handle);
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
        return last;
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
        if (!remote_probe) remote_probe = remote_head_cli;
        std::vector<std::string> attempted;
        auto selection = select_git_remotes(sources, revision, ranking_cache, source_kind, remote_probe);
        while (true) {
            for (const auto& candidate : selection.candidates) {
                if (contains_source(attempted, candidate.source)) continue;
                attempted.push_back(candidate.source);
                const bool normalized_live = valid_live && depth_one_cli_repository(live_repository);
                if (normalized_live && local_head == candidate.commit) {
                    GitResult result{true, GitBackend::GitCli, candidate.source, candidate.commit, {}};
                    result.mode = RepositoryMode::Unchanged;
                    result.previous_commit = local_head;
                    return result;
                }
                if (valid_live && local_head != candidate.commit) {
                    const auto wanted = revision.empty() ? "HEAD" : revision;
                    if (visible_git({"git", "-C", live_repository.string(), "fetch", "--depth=1", "--no-tags",
                                     candidate.source, wanted}, observer) == 0) {
                        GitResult result{true, GitBackend::GitCli, candidate.source, candidate.commit, {}};
                        result.mode = RepositoryMode::Incremental;
                        result.previous_commit = local_head;
                        return result;
                    }
                    last = {false, GitBackend::GitCli, candidate.source, {}, "git fetch failed"};
                } else {
                    auto result = clone_with_cli(candidate.source, staging_directory, revision, candidate.commit, observer);
                    if (result.success) {
                        result.mode = RepositoryMode::Full;
                        result.commit = repository_head(staging_directory);
                        result.staging_path = staging_directory;
                        return result;
                    }
                    last = result;
                }
                mark_git_source_failure(ranking_cache, source_kind, sources, candidate.source);
            }
            if (!selection.cache_hit) break;
            selection = select_git_remotes(sources, revision, ranking_cache, source_kind, remote_probe,
                                           attempted, false);
        }
        if (attempted.empty()) last = {false, GitBackend::GitCli, {}, {},
                                       "every Git source failed its remote SHA check"};
        return last;
    }

#ifdef BAAS_INSTALLER_HAS_LIBGIT2
    if (!remote_probe) remote_probe = remote_head_libgit2;
    std::vector<std::string> attempted;
    auto selection = select_git_remotes(sources, revision, ranking_cache, source_kind, remote_probe);
    while (true) {
        for (const auto& candidate : selection.candidates) {
            if (contains_source(attempted, candidate.source)) continue;
            attempted.push_back(candidate.source);
            const bool normalized_live = valid_live && depth_one_libgit2_repository(live_repository);
            if (normalized_live && local_head == candidate.commit) {
                GitResult result{true, GitBackend::Libgit2, candidate.source, candidate.commit, {}};
                result.mode = RepositoryMode::Unchanged;
                result.previous_commit = local_head;
                return result;
            }
            auto result = clone_with_libgit2(candidate.source, staging_directory, revision, observer);
            if (result.success) {
                result.mode = RepositoryMode::Full;
                result.commit = repository_head(staging_directory);
                result.staging_path = staging_directory;
                return result;
            }
            last = result;
            mark_git_source_failure(ranking_cache, source_kind, sources, candidate.source);
        }
        if (!selection.cache_hit) break;
        selection = select_git_remotes(sources, revision, ranking_cache, source_kind, remote_probe,
                                       attempted, false);
    }
    if (attempted.empty()) last = {false, GitBackend::Libgit2, {}, {},
                                   "every Git source failed its remote SHA check"};
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
    ensure_libgit2();
    git_repository* repository = nullptr;
    git_object* object = nullptr;
    const int opened = git_repository_open(&repository, live_repository.string().c_str());
    const int resolved = opened == 0 ? git_revparse_single(&object, repository, prepared.commit.c_str()) : opened;
    const int reset = resolved == 0 ? git_reset(repository, object, GIT_RESET_HARD, nullptr) : resolved;
    std::string reset_error;
    if (reset != 0) {
        const auto* detail = git_error_last();
        reset_error = detail ? detail->message : "libgit2 hard reset failed";
    }
    if (object) git_object_free(object);
    if (repository) git_repository_free(repository);
    if (reset != 0) error = std::move(reset_error);
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
#ifdef BAAS_INSTALLER_HAS_LIBGIT2
        if (depth_one_libgit2_repository(repository)) return true;
        error = "libgit2 repository did not retain exactly one shallow commit at '" +
                repository.generic_string() + "'";
        return false;
#else
        error = "libgit2 is not available";
        return false;
#endif
    }
    const auto shallow = hidden_git({"git", "-C", repository.string(), "rev-parse", "--is-shallow-repository"});
    const auto count = hidden_git({"git", "-C", repository.string(), "rev-list", "--count", "HEAD"});
    if (shallow.exit_code != 0 || first_token(shallow.output) != "true" ||
        count.exit_code != 0 || first_token(count.output) != "1") {
        error = "Git repository at '" + repository.generic_string() +
                "' did not retain exactly one shallow commit (shallow='" + first_token(shallow.output) +
                "', count='" + first_token(count.output) + "')";
        return false;
    }
    return true;
}

bool compact_git_repository(const fs::path& repository, const GitBackend backend, std::string& error) noexcept {
    error.clear();
    try {
        if (backend != GitBackend::GitCli) {
#ifdef BAAS_INSTALLER_HAS_LIBGIT2
            if (depth_one_libgit2_repository(repository)) return true;
            error = "libgit2 repository maintenance validation failed";
#else
            error = "libgit2 is not available";
#endif
            return false;
        }
        if (hidden_git({"git", "-C", repository.string(), "checkout", "--detach", "--force", "HEAD"}).exit_code != 0) {
            error = "could not detach repository HEAD";
            return false;
        }
        const auto refs = hidden_git({"git", "-C", repository.string(), "for-each-ref", "--format=%(refname)"});
        if (refs.exit_code != 0) {
            error = "could not enumerate repository refs";
            return false;
        }
        std::istringstream input(refs.output);
        std::string reference;
        while (std::getline(input, reference)) {
            if (!reference.empty()) {
                const auto symbolic = hidden_git({"git", "-C", repository.string(), "symbolic-ref", "-q", reference});
                const auto removed = symbolic.exit_code == 0
                    ? hidden_git({"git", "-C", repository.string(), "symbolic-ref", "--delete", reference})
                    : hidden_git({"git", "-C", repository.string(), "update-ref", "-d", reference});
                if (removed.exit_code != 0) {
                    error = "could not remove repository ref " + reference;
                    return false;
                }
            }
        }
        if (hidden_git({"git", "-C", repository.string(), "reflog", "expire", "--expire=now", "--all"}).exit_code != 0 ||
            hidden_git({"git", "-C", repository.string(), "gc", "--prune=now"}).exit_code != 0) {
            error = "could not prune repository history";
            return false;
        }
        const auto remaining_refs = hidden_git(
            {"git", "-C", repository.string(), "for-each-ref", "--format=%(refname)"});
        const auto unreachable = hidden_git({"git", "-C", repository.string(), "fsck", "--unreachable"});
        if (!depth_one_cli_repository(repository) || remaining_refs.exit_code != 0 ||
            !first_token(remaining_refs.output).empty() || unreachable.exit_code != 0 ||
            !first_token(unreachable.output).empty()) {
            error = "repository still contains refs or unreachable history after pruning (refs='" +
                    first_token(remaining_refs.output) + "', unreachable='" + unreachable.output + "')";
            return false;
        }
        return true;
    } catch (const std::exception& exception) {
        error = exception.what();
        return false;
    } catch (...) {
        error = "unknown repository maintenance failure";
        return false;
    }
}

}  // namespace baas_installer
