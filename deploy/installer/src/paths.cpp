#include "baas_installer/paths.hpp"

namespace baas_installer {

InstallPaths InstallPaths::from_executable(const std::filesystem::path& executable) {
    const auto root = executable.lexically_normal().parent_path();
    const auto toolkit_dir = root / "toolkit";
    return {
        .root = root,
        .setup_toml = root / "setup.toml",
        .tmp_dir = root / "tmp",
        .toolkit_dir = toolkit_dir,
        .uv_dir = toolkit_dir / "uv",
        .venv_dir = root / ".venv",
        .logs_dir = root / "log",
        .state_dir = root / ".baas-installer",
    };
}

}  // namespace baas_installer
