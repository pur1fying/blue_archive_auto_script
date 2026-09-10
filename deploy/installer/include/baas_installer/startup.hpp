#pragma once

#include "baas_installer/paths.hpp"

#include <filesystem>
#include <string>
#include <vector>

namespace baas_installer {

struct StartupOptions {
    bool valid{true};
    bool help{};
    bool print_root{};
    bool auto_exit{};
    bool no_launch{};
    std::filesystem::path install_dir;
    std::vector<std::string> forwarded_arguments;
    std::string error;
};

enum class StartupMode {
    ExistingInstallation,
    SelectInstallTarget,
    Invalid,
};

struct StartupDecision {
    StartupMode mode{StartupMode::Invalid};
    InstallPaths paths;
    std::filesystem::path target_root;
    std::string configured_root{"."};
    std::string error;
};

StartupOptions parse_startup_arguments(const std::vector<std::string>& arguments);
StartupDecision decide_startup(const std::filesystem::path& current_executable,
                               const StartupOptions& options);

}  // namespace baas_installer
