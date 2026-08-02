#pragma once

#include "baas_installer/config.hpp"
#include "baas_installer/git.hpp"
#include "baas_installer/paths.hpp"
#include "baas_installer/process.hpp"

#include <filesystem>
#include <map>
#include <string>
#include <vector>

namespace baas_installer {

using UvProcessExecutor = std::function<ProcessResult(const ProcessSpec&)>;

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
std::filesystem::path dependency_requirements(const InstallPaths& paths);
std::string expected_uv_sha256();
std::vector<UvCommand> managed_uv_commands(
    const UvEnvironment& environment,
    const InstallerConfig& config,
    const std::filesystem::path& requirements);

bool ensure_portable_uv(const InstallPaths& paths, const InstallerConfig& config, std::string& error,
                        ProcessObserver observer = {}, UvProcessExecutor terminal_executor = {});
bool sync_portable_uv(const InstallPaths& paths, const InstallerConfig& config, std::string& error,
                      ProcessObserver observer = {}, UvProcessExecutor terminal_executor = {});

}  // namespace baas_installer
