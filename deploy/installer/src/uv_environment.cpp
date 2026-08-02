#include "baas_installer/uv_environment.hpp"
#include "baas_installer/process.hpp"
#include "baas_installer/sources.hpp"

#include <fstream>

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
        .venv_dir = managed ? paths.venv_dir : fs::path(config.runtime_path),
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
        {"UV_PROJECT_ENVIRONMENT", text(result.venv_dir)},
        {"UV_VENV_RELOCATABLE", "1"},
        {"UV_NO_CONFIG", "1"},
        {"UV_PYTHON_INSTALL_REGISTRY", "0"},
        {"XDG_CACHE_HOME", text(uv_root / "xdg" / "cache")},
        {"XDG_CONFIG_HOME", text(uv_root / "xdg" / "config")},
        {"XDG_DATA_HOME", text(uv_root / "xdg" / "data")},
        {"TMPDIR", text(tmp)},
        {"TMP", text(tmp)},
        {"TEMP", text(tmp)},
    };
    return result;
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
                        ProcessObserver observer, UvProcessExecutor terminal_executor) {
    const auto environment = make_uv_environment(paths, config);
    if (!environment.managed || fs::exists(environment.executable)) return true;
    fs::create_directories(paths.tmp_dir / "uv");
    const auto archive = paths.tmp_dir / "uv" / uv_archive_name();
    const auto filename = uv_archive_name();
    std::vector<std::string> sources{"https://github.com/astral-sh/uv/releases/download/0.5.11/" + filename};
    for (const auto& source : default_sources(SourceKind::Uv, config)) if (!source.empty()) sources.push_back(source + "/" + filename);
    for (const auto& source : sources) {
        if (run_visible({"curl", "--fail", "--location", "--connect-timeout", "5", "--retry", "2", "--output",
                         archive.string(), source}, environment.variables, paths.root, "curl", observer,
                        terminal_executor).exit_code != 0) continue;
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
                      ProcessObserver observer, UvProcessExecutor terminal_executor) {
    const auto environment = make_uv_environment(paths, config);
    if (!environment.managed) return true;
    if (!ensure_portable_uv(paths, config, error, observer, terminal_executor)) return false;
    const auto requirements = paths.root / "requirements.txt";
    if (!fs::exists(requirements)) { error = "requirements.txt is missing after main deployment"; return false; }

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

    bool python_installed = false;
    std::vector<std::string> cpython_mirrors{""};
    const auto configured_mirrors = default_sources(SourceKind::Cpython, config);
    cpython_mirrors.insert(cpython_mirrors.end(), configured_mirrors.begin(), configured_mirrors.end());
    for (const auto& mirror : cpython_mirrors) {
        auto variables = environment.variables;
        if (!mirror.empty()) variables["UV_PYTHON_INSTALL_MIRROR"] = mirror;
        if (run_uv({"python", "install", config.python_version}, variables)) {
            python_installed = true;
            break;
        }
    }
    if (!python_installed) {
        error = "uv could not install Python from the official source or any configured fallback";
        return false;
    }
    const auto managed_marker = environment.venv_dir / ".baas-installer-managed";
    std::string marker_value;
    if (fs::exists(managed_marker)) {
        std::ifstream marker(managed_marker, std::ios::binary);
        marker_value.assign(std::istreambuf_iterator<char>(marker), {});
    }
    const bool reusable_environment = fs::exists(environment.venv_dir / "pyvenv.cfg") &&
                                      marker_value == "python=" + config.python_version + "\n";
    if (!reusable_environment) {
        if (!run_uv({"venv", "--relocatable", "--python", config.python_version, environment.venv_dir.generic_string()},
                    environment.variables)) {
            error = "uv could not create the relocatable virtual environment";
            return false;
        }
    }

    const auto compiled = requirements.parent_path() / ".baas-installer-requirements.txt";
    bool dependencies_installed = false;
    for (const auto& index : default_sources(SourceKind::Pypi, config)) {
        auto variables = environment.variables;
        variables["UV_INDEX"] = index;
        variables["UV_DEFAULT_INDEX"] = index;
        variables["VIRTUAL_ENV"] = environment.venv_dir.generic_string();
        if (!run_uv({"pip", "compile", requirements.generic_string(), "--output-file", compiled.generic_string()}, variables)) continue;
        if (!run_uv({"pip", "sync", "--link-mode", "copy", compiled.generic_string()}, variables)) continue;
        dependencies_installed = true;
        break;
    }
    if (!dependencies_installed) {
        error = "uv dependency synchronization failed for every configured PyPI index";
        return false;
    }
    {
        std::ofstream marker(managed_marker, std::ios::binary | std::ios::trunc);
        marker << "python=" << config.python_version << '\n';
        if (!marker) {
            error = "uv environment synchronization succeeded but its managed marker could not be written";
            return false;
        }
    }
    run_uv({"cache", "clean"}, environment.variables);
    return true;
}

}  // namespace baas_installer
