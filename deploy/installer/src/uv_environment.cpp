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
        {{"venv", "--python", config.python_version, environment.venv_dir.generic_string()}},
        {{"pip", "compile", requirements.generic_string(), "--output-file", compiled.generic_string()}},
        {{"pip", "sync", compiled.generic_string()}},
    };
}

bool ensure_portable_uv(const InstallPaths& paths, const InstallerConfig& config, std::string& error) {
    const auto environment = make_uv_environment(paths, config);
    if (!environment.managed || fs::exists(environment.executable)) return true;
    fs::create_directories(paths.tmp_dir / "uv");
    const auto archive = paths.tmp_dir / "uv" / uv_archive_name();
    const auto filename = uv_archive_name();
    std::vector<std::string> sources{"https://github.com/astral-sh/uv/releases/download/0.5.11/" + filename};
    for (const auto& source : default_sources(SourceKind::Uv, config)) if (!source.empty()) sources.push_back(source + "/" + filename);
    for (const auto& source : sources) {
        if (run_process({"curl", "--fail", "--location", "--connect-timeout", "5", "--retry", "2", "--output", archive.string(), source}) != 0) continue;
        std::error_code ignored; fs::remove_all(paths.uv_dir, ignored); fs::create_directories(paths.uv_dir);
        // Windows bsdtar accepts ZIP archives but not every GNU tar option.
        // Keep the archive's top-level directory and locate uv recursively.
        if (run_process({"tar", "-xf", archive.string(), "-C", paths.uv_dir.string()}) != 0) continue;
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

bool sync_portable_uv(const InstallPaths& paths, const InstallerConfig& config, std::string& error) {
    const auto environment = make_uv_environment(paths, config);
    if (!environment.managed) return true;
    if (!ensure_portable_uv(paths, config, error)) return false;
    const auto requirements = paths.root / "requirements.txt";
    if (!fs::exists(requirements)) { error = "requirements.txt is missing after main deployment"; return false; }
    for (const auto& command : managed_uv_commands(environment, config, requirements)) {
        std::vector<std::string> arguments{environment.executable.string()};
        arguments.insert(arguments.end(), command.arguments.begin(), command.arguments.end());
        if (run_process(arguments, environment.variables) != 0) { error = "uv command failed: " + command.arguments.front(); return false; }
    }
    return true;
}

}  // namespace baas_installer
