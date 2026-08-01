#include "baas_installer/uv_environment.hpp"

namespace fs = std::filesystem;

namespace baas_installer {
namespace {

std::string text(const fs::path& path) { return path.generic_string(); }

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

}  // namespace baas_installer
