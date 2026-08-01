#pragma once

#include "baas_installer/config.hpp"
#include "baas_installer/paths.hpp"

#include <filesystem>
#include <map>
#include <string>
#include <vector>

namespace baas_installer {

struct UvCommand {
    std::vector<std::string> arguments;
};

struct UvEnvironment {
    std::filesystem::path executable;
    std::filesystem::path cache_dir;
    std::filesystem::path python_dir;
    std::filesystem::path venv_dir;
    std::map<std::string, std::string> variables;
    bool managed{};
};

UvEnvironment make_uv_environment(const InstallPaths& paths, const InstallerConfig& config);
std::vector<UvCommand> managed_uv_commands(
    const UvEnvironment& environment,
    const InstallerConfig& config,
    const std::filesystem::path& requirements);

}  // namespace baas_installer
