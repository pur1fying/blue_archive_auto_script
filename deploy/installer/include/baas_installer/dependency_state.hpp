#pragma once

#include "baas_installer/config.hpp"
#include "baas_installer/paths.hpp"

#include <filesystem>
#include <string>

namespace baas_installer {

struct DependencyStamp {
    int schema{1};
    std::string input_sha256;
    std::string lock_sha256;
    std::string python_version;
    std::string runtime;
};

struct DependencyState {
    DependencyStamp current;
    bool cache_hit{};
    std::string reason;
};

std::filesystem::path dependency_stamp_path(const InstallPaths& paths);
DependencyStamp make_dependency_stamp(const InstallPaths& paths, const InstallerConfig& config,
                                      const std::filesystem::path& requirements,
                                      const std::filesystem::path& compiled_lock);
DependencyState inspect_dependency_state(const InstallPaths& paths, const InstallerConfig& config,
                                         const std::filesystem::path& requirements,
                                         const std::filesystem::path& compiled_lock);
void save_dependency_stamp_atomic(const DependencyStamp& stamp, const InstallPaths& paths);
bool repair_managed_venv_after_move(const InstallPaths& paths, const InstallerConfig& config,
                                    std::string& error);

}  // namespace baas_installer
