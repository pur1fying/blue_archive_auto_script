#include "baas_installer/uv_environment.hpp"
#include "baas_installer/dependency_state.hpp"
#include "baas_installer/mirrorchyan.hpp"
#include "baas_installer/process.hpp"
#include "baas_installer/sources.hpp"

#include <algorithm>
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

long long http_probe_latency(const std::string& url) {
    const auto request = [&](const bool head) -> std::pair<bool, long long> {
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
        const auto status = curl_easy_perform(curl);
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - started).count();
        long response = 0;
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response);
        curl_easy_cleanup(curl);
        return {status == CURLE_OK && acceptable_http_status(response), elapsed};
    };
    if (const auto head = request(true); head.first) return head.second;
    if (const auto range = request(false); range.first) return range.second;
    return -1;
}
#endif

std::vector<std::string> ranked_sources_for(
    const SourceKind kind, const std::vector<std::string>& candidates, const UvSourceProbe& source_probe,
    const ProcessObserver& observer, const bool test_executor) {
    if (candidates.empty()) return {};
    if (!source_probe && test_executor) return candidates;
    const auto ranking = rank_sources(candidates, [&](const std::string& source) {
        if (observer) observer("uv", "probe", "Testing source " + source + "\n");
        const auto probe_url = kind == SourceKind::Cpython ? cpython_probe_url(source) : source;
        long long latency = -1;
        if (source_probe) latency = source_probe(kind, probe_url);
#ifdef BAAS_INSTALLER_HAS_CURL
        else latency = http_probe_latency(probe_url);
#endif
        if (observer) {
            observer("uv", "probe", source + (latency >= 0 ? " responded in " + std::to_string(latency) + " ms\n"
                                                               : " probe failed\n"));
        }
        return latency;
    });
    std::vector<std::string> result;
    for (const auto& source : ranking) result.push_back(source.url);
    return result;
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

std::string expected_uv_sha256() {
#ifdef _WIN32
    return "3e8203e6434b45427f20824419f8d8d53f970a76d94ccdcad07f8498fa01a9d0";
#elif defined(__APPLE__) && (defined(__aarch64__) || defined(__arm64__))
    return "695f3640d5b1a4e28de7e36e3a2e14072852dcc6c70bf9e4deec6ada00d516b4";
#elif defined(__APPLE__)
    return "7e23d1d892c23f9e74245c4fd3d3e246438ce9b34460f85eee61f784de137b0b";
#else
    return "14411de26cdea5f5139fafaf2b675b1c633e744dd49c6d6a9fc8817ec065158b";
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
    sources = ranked_sources_for(SourceKind::Uv, unique_sources(std::move(sources)), source_probe, observer,
                                 static_cast<bool>(terminal_executor));
    if (sources.empty()) {
        error = "every portable uv source failed its download probe";
        return false;
    }
    for (const auto& source : sources) {
        if (run_visible({"curl", "--fail", "--location", "--connect-timeout", "5", "--retry", "2", "--output",
                         archive.string(), source}, environment.variables, paths.root, "curl", observer,
                        terminal_executor).exit_code != 0) continue;
        if (!verify_sha256(archive, expected_uv_sha256())) {
            if (observer) observer("uv", "curl", "Downloaded uv archive failed pinned SHA-256 verification\r");
            std::error_code ignored;
            fs::remove(archive, ignored);
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
            if (fs::exists(environment.executable)) return true;
        }
    }
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
            cpython_mirrors = ranked_sources_for(SourceKind::Cpython, unique_sources(std::move(cpython_mirrors)),
                                                 source_probe, observer, static_cast<bool>(terminal_executor));
            bool python_installed = false;
            for (const auto& mirror : cpython_mirrors) {
                auto variables = environment.variables;
                variables["UV_PYTHON_INSTALL_MIRROR"] = mirror;
                if (run_uv({"python", "install", config.python_version}, variables)) {
                    python_installed = true;
                    break;
                }
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
    const auto pypi_sources = ranked_sources_for(SourceKind::Pypi, default_sources(SourceKind::Pypi, config),
                                                  source_probe, observer, static_cast<bool>(terminal_executor));
    for (const auto& index : pypi_sources) {
        auto variables = environment.variables;
        variables["UV_INDEX"] = index;
        variables["UV_DEFAULT_INDEX"] = index;
        if (environment.managed) variables["VIRTUAL_ENV"] = environment.venv_dir.generic_string();
        if (!run_uv({"pip", "compile", requirements.generic_string(), "--output-file", compiled.generic_string()}, variables)) continue;
        std::vector<std::string> sync{"pip", "sync", "--link-mode", "copy"};
        if (!environment.managed) {
            sync.push_back("--python");
            sync.push_back(config.runtime_path);
        }
        sync.push_back(compiled.generic_string());
        if (!run_uv(sync, variables)) continue;
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
    try {
        save_dependency_stamp_atomic(make_dependency_stamp(paths, config, requirements, compiled), paths);
    } catch (const std::exception& exception) {
        error = std::string("dependency synchronization succeeded but its SHA stamp could not be written: ") +
                exception.what();
        return false;
    }
    return true;
}

}  // namespace baas_installer
