#pragma once

#include <filesystem>
#include <string>
#include <string_view>

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
    static InstallPaths from_root(const std::filesystem::path& root,
                                  const std::filesystem::path& executable_name);
    static InstallPaths from_install_root(const std::filesystem::path& root,
                                          const std::filesystem::path& executable);
};

std::filesystem::path current_executable_path();
std::string path_to_utf8(const std::filesystem::path& path);
std::filesystem::path path_from_utf8(std::string_view value);

}  // namespace baas_installer
