#include "baas_installer/uv_environment.hpp"
#include "baas_installer/curl_runtime.hpp"
#include "baas_installer/dependency_state.hpp"
#include "baas_installer/mirrorchyan.hpp"
#include "baas_installer/process.hpp"
#include "baas_installer/sources.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <fstream>

#ifdef BAAS_INSTALLER_HAS_CURL
#include <curl/curl.h>
#endif

namespace fs = std::filesystem;

namespace baas_installer {
namespace {

std::string text(const fs::path& path) { return path.generic_string(); }

std::string uv_archive_name() {
#ifdef _WIN32
    return "uv-x86_64-pc-windows-msvc.zip";
#elif defined(__APPLE__) && (defined(__aarch64__) || defined(__arm64__))
    return "uv-aarch64-apple-darwin.tar.gz";
#elif defined(__APPLE__)
    return "uv-x86_64-apple-darwin.tar.gz";
#else
    return "uv-x86_64-unknown-linux-gnu.tar.gz";
#endif
}

std::filesystem::path virtualenv_python(const InstallPaths& paths) {
#ifdef _WIN32
    return paths.venv_dir / "Scripts" / "python.exe";
#else
    return paths.venv_dir / "bin" / "python";
#endif
}

bool managed_python_exists(const UvEnvironment& environment) {
    std::error_code error;
    if (!fs::is_directory(environment.python_dir, error)) return false;
    for (fs::recursive_directory_iterator item(environment.python_dir, error), end;
         !error && item != end; item.increment(error)) {
        if (!item->is_regular_file(error)) continue;
        auto name = item->path().filename().string();
        std::transform(name.begin(), name.end(), name.begin(), [](const unsigned char character) {
            return static_cast<char>(std::tolower(character));
        });
#ifdef _WIN32
        if (name == "python.exe") return true;
#else
        if (name == "python" || name == "python3") return true;
#endif
    }
    return false;
}

std::vector<std::string> unique_sources(std::vector<std::string> sources) {
    std::vector<std::string> result;
    for (auto& source : sources) {
        if (!source.empty() && std::find(result.begin(), result.end(), source) == result.end()) {
            result.push_back(std::move(source));
        }
    }
    return result;
}

std::string cpython_probe_url(std::string source) {
    while (source.ends_with('/')) source.pop_back();
    constexpr std::string_view suffix = "/releases/download";
    if (source.ends_with(suffix)) source.resize(source.size() - std::string(suffix).size());
    return source + "/releases";
}

#ifdef BAAS_INSTALLER_HAS_CURL
std::size_t discard_response(const char*, const std::size_t size, const std::size_t count, void*) {
    return size * count;
}

bool acceptable_http_status(const long status) { return status >= 200 && status < 400; }

struct HttpProbeResult {
    long long latency_ms{-1};
    CURLcode head_code{CURLE_OK};
    long head_status{};
    CURLcode range_code{CURLE_OK};
    long range_status{};
};

HttpProbeResult http_probe(const std::string& url) {
    HttpProbeResult result;
    const auto request = [&](const bool head, CURLcode& code, long& response) -> std::pair<bool, long long> {
        CURL* curl = curl_easy_init();
        if (curl == nullptr) return {false, -1};
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
        curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT, 5L);
        curl_easy_setopt(curl, CURLOPT_TIMEOUT, 5L);
        curl_easy_setopt(curl, CURLOPT_NOSIGNAL, 1L);
        curl_easy_setopt(curl, CURLOPT_USERAGENT, "BAAS-Installer/2.0");
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, discard_response);
        if (head) {
            curl_easy_setopt(curl, CURLOPT_NOBODY, 1L);
        } else {
            curl_easy_setopt(curl, CURLOPT_RANGE, "0-0");
            curl_easy_setopt(curl, CURLOPT_MAXFILESIZE_LARGE, static_cast<curl_off_t>(1024));
        }
        const auto started = std::chrono::steady_clock::now();
        code = curl_easy_perform(curl);
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - started).count();
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response);
        curl_easy_cleanup(curl);
        return {code == CURLE_OK && acceptable_http_status(response), elapsed};
    };
    if (const auto head = request(true, result.head_code, result.head_status); head.first) {
        result.latency_ms = head.second;
        return result;
    }
    if (const auto range = request(false, result.range_code, result.range_status); range.first) {
        result.latency_ms = range.second;
    }
    return result;
}

std::string curl_probe_failure(const HttpProbeResult& probe) {
    return " probe failed (HEAD: " + std::string(curl_easy_strerror(probe.head_code)) + "/" +
           std::to_string(static_cast<int>(probe.head_code)) + ", HTTP " + std::to_string(probe.head_status) +
           "; range: " + std::string(curl_easy_strerror(probe.range_code)) + "/" +
           std::to_string(static_cast<int>(probe.range_code)) + ", HTTP " + std::to_string(probe.range_status) +
           "); retaining source for a real attempt\n";
}
#endif

std::vector<std::string> ranked_sources_for(
    const SourceKind kind, const std::vector<std::string>& candidates, const UvSourceProbe& source_probe,
    const ProcessObserver& observer, const bool test_executor, const fs::path& ranking_cache) {
    if (candidates.empty()) return {};
    if (!source_probe && test_executor) return candidates;
#ifdef BAAS_INSTALLER_HAS_CURL
    if (!source_probe && !ensure_curl_initialized()) {
        if (observer) observer("uv", "probe", "libcurl global initialization failed; retaining source order\n");
        return candidates;
    }
#endif
    const auto measure = [&](const std::string& source) {
        if (observer) observer("uv", "probe", "Testing source " + source + "\n");
        const auto probe_url = kind == SourceKind::Cpython ? cpython_probe_url(source) : source;
        long long latency = -1;
        std::string failure;
        if (source_probe) latency = source_probe(kind, probe_url);
#ifdef BAAS_INSTALLER_HAS_CURL
        else {
            const auto probe = http_probe(probe_url);
            latency = probe.latency_ms;
            if (latency < 0) failure = curl_probe_failure(probe);
        }
#endif
        if (observer) {
            observer("uv", "probe", source + (latency >= 0 ? " responded in " + std::to_string(latency) + " ms\n"
                                                               : failure.empty() ? " probe failed; retaining source for a real attempt\n"
                                                                                 : failure));
        }
        return latency;
    };
    auto cached = ranking_cache.empty()
        ? std::vector<RankedSource>{}
        : load_source_ranking(ranking_cache, kind, candidates);
    if (!cached.empty()) {
        const auto preferred = std::find_if(cached.begin(), cached.end(), [](const RankedSource& item) {
            return item.preferred;
        });
        if (preferred != cached.end()) {
            const auto latency = measure(preferred->url);
            if (latency >= 0) {
                preferred->latency_ms = latency;
                preferred->failures = 0;
                preferred->available = true;
                save_source_ranking(ranking_cache, kind, cached);
                std::vector<std::string> result{preferred->url};
                for (const auto& item : cached) if (item.url != preferred->url) result.push_back(item.url);
                return result;
            }
            ++preferred->failures;
            preferred->available = false;
            preferred->preferred = false;
        }
    }
    auto ranking = rank_sources(candidates, measure);
    const auto successful = std::find_if(ranking.begin(), ranking.end(), [](const RankedSource& item) {
        return item.latency_ms >= 0;
    });
    if (successful != ranking.end()) successful->preferred = true;
    if (!ranking_cache.empty()) save_source_ranking(ranking_cache, kind, ranking);
    std::vector<std::string> result;
    for (const auto& source : ranking) result.push_back(source.url);
    return result;
}

void record_runtime_source_result(const fs::path& cache, const SourceKind kind,
                                  const std::vector<std::string>& candidates, const std::string& url,
                                  const bool success) {
    if (cache.empty()) return;
    auto ranking = load_source_ranking(cache, kind, candidates);
    if (ranking.empty()) return;
    for (auto& item : ranking) {
        if (success) item.preferred = item.url == url;
        if (item.url != url) continue;
        item.available = success;
        if (success) item.failures = 0;
        else ++item.failures;
    }
    save_source_ranking(cache, kind, ranking);
}

ProcessResult run_visible(const std::vector<std::string>& arguments,
                          const std::map<std::string, std::string>& environment,
                          const fs::path& working_directory, const std::string& backend,
                          const ProcessObserver& observer, const UvProcessExecutor& executor) {
    ProcessSpec spec;
    spec.arguments = arguments;
    spec.environment = environment;
    spec.working_directory = working_directory;
    spec.use_pty = true;
    spec.on_chunk = [observer, backend](const std::string_view chunk) {
        if (observer) observer("uv", backend, chunk);
    };
    return executor ? executor(spec) : run_terminal_process(spec);
}

bool clear_uv_download_caches(const InstallPaths& paths, const UvEnvironment& environment,
                              std::string& error) {
    const std::array directories{
        environment.cache_dir,
        paths.toolkit_dir / "uv" / "python-cache",
        paths.toolkit_dir / "uv" / "xdg" / "cache",
        paths.tmp_dir / "uv",
    };
    for (const auto& directory : directories) {
        std::error_code remove_error;
        fs::remove_all(directory, remove_error);
        if (remove_error) {
            error = "dependency synchronization succeeded but UV cache cleanup failed for '" +
                    directory.generic_string() + "': " + remove_error.message();
            return false;
        }
    }
    return true;
}

fs::path uv_cache_cleanup_marker(const InstallPaths& paths) {
    return paths.state_dir / "uv-cache-cleanup-v1.pending";
}

bool persist_uv_cache_cleanup_marker(const InstallPaths& paths, std::string& error) {
    std::error_code create_error;
    fs::create_directories(paths.state_dir, create_error);
    if (create_error) {
        error = "dependency synchronization succeeded but UV cache cleanup could not be scheduled: " +
                create_error.message();
        return false;
    }
    std::ofstream marker(uv_cache_cleanup_marker(paths), std::ios::binary | std::ios::trunc);
    marker << "pending\n";
    marker.close();
    if (!marker) {
        error = "dependency synchronization succeeded but UV cache cleanup marker could not be written";
        return false;
    }
    return true;
}

bool remove_uv_cache_cleanup_marker(const InstallPaths& paths, std::string& error) {
    std::error_code remove_error;
    fs::remove(uv_cache_cleanup_marker(paths), remove_error);
    if (remove_error) {
        error = "UV cache cleanup marker could not be removed: " + remove_error.message();
        return false;
    }
    return true;
}

bool complete_uv_cache_cleanup(const InstallPaths& paths, const UvEnvironment& environment,
                               std::string& error) {
    if (!clear_uv_download_caches(paths, environment, error)) return false;
    return remove_uv_cache_cleanup_marker(paths, error);
}

}  // namespace

UvEnvironment make_uv_environment(const InstallPaths& paths, const InstallerConfig& config) {
    const auto uv_root = paths.toolkit_dir / "uv";
    const auto cache = uv_root / "cache";
    const auto python = uv_root / "cpython";
    const auto tmp = paths.tmp_dir / "uv";
    const bool managed = config.uses_portable_runtime();
    UvEnvironment result{
#ifdef _WIN32
        .executable = uv_root / "uv.exe",
#else
        .executable = uv_root / "uv",
#endif
        .cache_dir = cache,
        .python_dir = python,
        .venv_dir = managed ? paths.venv_dir : fs::path{},
        .managed = managed,
    };
    result.variables = {
        {"UV_CACHE_DIR", text(cache)},
        {"UV_PYTHON_INSTALL_DIR", text(python)},
        {"UV_PYTHON_CACHE_DIR", text(uv_root / "python-cache")},
        {"UV_PYTHON_BIN_DIR", text(uv_root / "python-bin")},
        {"UV_TOOL_DIR", text(uv_root / "tools")},
        {"UV_TOOL_BIN_DIR", text(uv_root / "tool-bin")},
        {"UV_CREDENTIALS_DIR", text(uv_root / "credentials")},
        {"UV_NO_CONFIG", "1"},
        {"UV_PYTHON_INSTALL_REGISTRY", "0"},
        {"XDG_CACHE_HOME", text(uv_root / "xdg" / "cache")},
        {"XDG_CONFIG_HOME", text(uv_root / "xdg" / "config")},
        {"XDG_DATA_HOME", text(uv_root / "xdg" / "data")},
        {"TMPDIR", text(tmp)},
        {"TMP", text(tmp)},
        {"TEMP", text(tmp)},
    };
    if (managed) {
        result.variables["UV_PROJECT_ENVIRONMENT"] = text(result.venv_dir);
        result.variables["UV_VENV_RELOCATABLE"] = "1";
    }
    return result;
}

fs::path dependency_requirements(const InstallPaths& paths) {
#ifdef _WIN32
    return paths.root / "requirements.txt";
#else
    return paths.root / "requirements-linux.txt";
#endif
}

std::vector<UvCommand> managed_uv_commands(
    const UvEnvironment& environment, const InstallerConfig& config, const fs::path& requirements) {
    if (!environment.managed) return {};
    const auto compiled = requirements.parent_path() / ".baas-installer-requirements.txt";
    return {
        {{"python", "install", config.python_version}},
        {{"venv", "--relocatable", "--python", config.python_version, environment.venv_dir.generic_string()}},
        {{"pip", "compile", requirements.generic_string(), "--output-file", compiled.generic_string()}},
        {{"pip", "sync", "--link-mode", "copy", compiled.generic_string()}},
    };
}

bool ensure_portable_uv(const InstallPaths& paths, const InstallerConfig& config, std::string& error,
                        ProcessObserver observer, UvProcessExecutor terminal_executor,
                        UvSourceProbe source_probe) {
    const auto environment = make_uv_environment(paths, config);
    if (fs::exists(environment.executable)) return true;
    fs::create_directories(paths.tmp_dir / "uv");
    const auto archive = paths.tmp_dir / "uv" / uv_archive_name();
    const auto filename = uv_archive_name();
    std::vector<std::string> sources;
    for (const auto& source : default_sources(SourceKind::Uv, config)) {
        if (!source.empty()) sources.push_back(source + "/" + filename);
    }
    sources.push_back("https://github.com/astral-sh/uv/releases/download/0.5.11/" + filename);
    sources = unique_sources(std::move(sources));
    const auto uv_candidates = sources;
    const auto ranking_cache = paths.state_dir / "source-ranking-v1.json";
    sources = ranked_sources_for(SourceKind::Uv, sources, source_probe, observer,
                                 static_cast<bool>(terminal_executor), ranking_cache);
    for (const auto& source : sources) {
        if (run_visible({"curl", "--fail", "--location", "--connect-timeout", "5", "--retry", "2", "--output",
                         archive.string(), source}, environment.variables, paths.root, "curl", observer,
                        terminal_executor).exit_code != 0) {
            record_runtime_source_result(ranking_cache, SourceKind::Uv, uv_candidates, source, false);
            continue;
        }
        std::error_code ignored; fs::remove_all(paths.uv_dir, ignored); fs::create_directories(paths.uv_dir);
        // Windows bsdtar accepts ZIP archives but not every GNU tar option.
        // Keep the archive's top-level directory and locate uv recursively.
        if (run_visible({"tar", "-xf", archive.string(), "-C", paths.uv_dir.string()}, environment.variables,
                        paths.root, "tar", observer, terminal_executor).exit_code != 0) continue;
        for (const auto& item : fs::recursive_directory_iterator(paths.uv_dir)) {
            if (item.path().filename() != environment.executable.filename()) continue;
            fs::copy_file(item.path(), environment.executable, fs::copy_options::overwrite_existing, ignored);
            fs::permissions(environment.executable, fs::perms::owner_exec | fs::perms::group_exec | fs::perms::others_exec, fs::perm_options::add, ignored);
            if (!fs::exists(environment.executable)) continue;
            if (run_visible({environment.executable.string(), "--version"}, environment.variables, paths.root,
                            "uv", observer, terminal_executor).exit_code == 0) {
                fs::remove(archive, ignored);
                record_runtime_source_result(ranking_cache, SourceKind::Uv, uv_candidates, source, true);
                return true;
            }
            if (observer) observer("uv", "uv", "Extracted uv executable failed --version; trying next source\r");
            break;
        }
    }
    std::error_code ignored;
    fs::remove_all(paths.uv_dir, ignored);
    fs::remove(archive, ignored);
    error = "could not download or unpack portable uv from every configured source";
    return false;
}

bool sync_portable_uv(const InstallPaths& paths, const InstallerConfig& config, std::string& error,
                      ProcessObserver observer, UvProcessExecutor terminal_executor,
                      UvSourceProbe source_probe) {
    const auto environment = make_uv_environment(paths, config);
    const auto requirements = dependency_requirements(paths);
    if (!fs::exists(requirements)) { error = requirements.filename().string() + " is missing after main deployment"; return false; }
    const auto compiled = requirements.parent_path() / ".baas-installer-requirements.txt";
    if (!repair_managed_venv_after_move(paths, config, error)) return false;
    const auto dependency_state = inspect_dependency_state(paths, config, requirements, compiled);
    if (fs::exists(uv_cache_cleanup_marker(paths))) {
        if (dependency_state.cache_hit) {
            if (!complete_uv_cache_cleanup(paths, environment, error)) return false;
            if (observer) observer("uv", "cache", "Pending UV cache cleanup completed\n");
        } else {
            if (!remove_uv_cache_cleanup_marker(paths, error)) return false;
            if (observer) observer("uv", "cache", "Stale UV cache cleanup marker cleared; retry cache retained\n");
        }
    }
    if (dependency_state.cache_hit) {
        if (observer) observer("uv", "cache", "Dependency SHA unchanged; uv skipped\n");
        return true;
    }
    if (!ensure_portable_uv(paths, config, error, observer, terminal_executor, source_probe)) return false;

    for (const auto& directory : {environment.cache_dir, environment.python_dir, paths.tmp_dir / "uv",
                                  paths.toolkit_dir / "uv" / "python-cache", paths.toolkit_dir / "uv" / "python-bin",
                                  paths.toolkit_dir / "uv" / "tools", paths.toolkit_dir / "uv" / "tool-bin",
                                  paths.toolkit_dir / "uv" / "credentials", paths.toolkit_dir / "uv" / "xdg" / "cache",
                                  paths.toolkit_dir / "uv" / "xdg" / "config", paths.toolkit_dir / "uv" / "xdg" / "data"}) {
        std::error_code ignored;
        fs::create_directories(directory, ignored);
    }

    const auto run_uv = [&](const std::vector<std::string>& command, const std::map<std::string, std::string>& variables) {
        std::vector<std::string> arguments{environment.executable.string()};
        arguments.insert(arguments.end(), command.begin(), command.end());
        return run_visible(arguments, variables, paths.root, "uv", observer, terminal_executor).exit_code == 0;
    };

    const auto managed_marker = environment.venv_dir / ".baas-installer-managed";
    if (environment.managed) {
        if (!managed_python_exists(environment)) {
            auto cpython_mirrors = default_sources(SourceKind::Cpython, config);
            cpython_mirrors.push_back("https://github.com/astral-sh/python-build-standalone/releases/download");
            cpython_mirrors = unique_sources(std::move(cpython_mirrors));
            const auto cpython_candidates = cpython_mirrors;
            cpython_mirrors = ranked_sources_for(SourceKind::Cpython, cpython_mirrors,
                                                 source_probe, observer, static_cast<bool>(terminal_executor),
                                                 paths.state_dir / "source-ranking-v1.json");
            bool python_installed = false;
            for (const auto& mirror : cpython_mirrors) {
                auto variables = environment.variables;
                variables["UV_PYTHON_INSTALL_MIRROR"] = mirror;
                if (run_uv({"python", "install", config.python_version}, variables)) {
                    record_runtime_source_result(paths.state_dir / "source-ranking-v1.json", SourceKind::Cpython,
                                                 cpython_candidates, mirror, true);
                    python_installed = true;
                    break;
                }
                record_runtime_source_result(paths.state_dir / "source-ranking-v1.json", SourceKind::Cpython,
                                             cpython_candidates, mirror, false);
            }
            if (!python_installed) {
                error = "uv could not install Python from any ranked source";
                return false;
            }
        }
        std::string marker_value;
        if (fs::exists(managed_marker)) {
            std::ifstream marker(managed_marker, std::ios::binary);
            marker_value.assign(std::istreambuf_iterator<char>(marker), {});
        }
        const bool reusable_environment = fs::exists(environment.venv_dir / "pyvenv.cfg") &&
                                           fs::is_regular_file(virtualenv_python(paths)) &&
                                           marker_value == "python=" + config.python_version + "\n";
        if (!reusable_environment) {
            if (!run_uv({"venv", "--relocatable", "--python", config.python_version, environment.venv_dir.generic_string()},
                        environment.variables)) {
                error = "uv could not create the relocatable virtual environment";
                return false;
            }
        }
    }

    bool dependencies_installed = false;
    const auto pypi_candidates = default_sources(SourceKind::Pypi, config);
    const auto pypi_sources = ranked_sources_for(SourceKind::Pypi, pypi_candidates,
                                                  source_probe, observer, static_cast<bool>(terminal_executor),
                                                  paths.state_dir / "source-ranking-v1.json");
    for (const auto& index : pypi_sources) {
        auto variables = environment.variables;
        variables["UV_INDEX"] = index;
        variables["UV_DEFAULT_INDEX"] = index;
        if (environment.managed) variables["VIRTUAL_ENV"] = environment.venv_dir.generic_string();
        if (!run_uv({"pip", "compile", requirements.generic_string(), "--output-file", compiled.generic_string()}, variables)) {
            record_runtime_source_result(paths.state_dir / "source-ranking-v1.json", SourceKind::Pypi,
                                         pypi_candidates, index, false);
            continue;
        }
        std::vector<std::string> sync{"pip", "sync", "--link-mode", "copy"};
        if (!environment.managed) {
            sync.push_back("--python");
            sync.push_back(config.runtime_path);
        }
        sync.push_back(compiled.generic_string());
        if (!run_uv(sync, variables)) {
            record_runtime_source_result(paths.state_dir / "source-ranking-v1.json", SourceKind::Pypi,
                                         pypi_candidates, index, false);
            continue;
        }
        record_runtime_source_result(paths.state_dir / "source-ranking-v1.json", SourceKind::Pypi,
                                     pypi_candidates, index, true);
        dependencies_installed = true;
        break;
    }
    if (!dependencies_installed) {
        error = "uv dependency synchronization failed for every configured PyPI index";
        return false;
    }
    if (environment.managed) {
        std::ofstream marker(managed_marker, std::ios::binary | std::ios::trunc);
        marker << "python=" << config.python_version << '\n';
        if (!marker) {
            error = "uv environment synchronization succeeded but its managed marker could not be written";
            return false;
        }
    }
    if (!persist_uv_cache_cleanup_marker(paths, error)) return false;
    try {
        save_dependency_stamp_atomic(make_dependency_stamp(paths, config, requirements, compiled), paths);
    } catch (const std::exception& exception) {
        error = std::string("dependency synchronization succeeded but its SHA stamp could not be written: ") +
                exception.what();
        return false;
    }
    if (!complete_uv_cache_cleanup(paths, environment, error)) return false;
    if (observer) observer("uv", "cache", "Disposable UV caches cleared\n");
    return true;
}

}  // namespace baas_installer
