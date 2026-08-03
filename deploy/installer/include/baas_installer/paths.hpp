#pragma once

#include <filesystem>

namespace baas_installer {

struct InstallPaths {
    std::filesystem::path executable;
    std::filesystem::path root;
    std::filesystem::path setup_toml;
    std::filesystem::path tmp_dir;
    std::filesystem::path toolkit_dir;
    std::filesystem::path uv_dir;
    std::filesystem::path venv_dir;
    std::filesystem::path logs_dir;
    std::filesystem::path state_dir;

    static InstallPaths from_executable(const std::filesystem::path& executable);
};

std::filesystem::path current_executable_path();

}  // namespace baas_installer
