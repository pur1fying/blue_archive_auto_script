#include "baas_installer/startup.hpp"

#include "baas_installer/config.hpp"
#include "baas_installer/install_target.hpp"

namespace fs = std::filesystem;

namespace baas_installer {

StartupOptions parse_startup_arguments(const std::vector<std::string>& arguments) {
    StartupOptions result;
    for (std::size_t index = 0; index < arguments.size(); ++index) {
        const auto& argument = arguments[index];
        if (argument == "--help") {
            result.help = true;
        } else if (argument == "--print-root") {
            result.print_root = true;
        } else if (argument == "--auto-exit") {
            result.auto_exit = true;
            result.forwarded_arguments.push_back(argument);
        } else if (argument == "--no-launch") {
            result.no_launch = true;
            result.forwarded_arguments.push_back(argument);
        } else if (argument == "--install-dir") {
            if (++index >= arguments.size() || arguments[index].empty()) {
                result.valid = false;
                result.error = argument + " requires a directory value";
                return result;
            }
            result.install_dir = path_from_utf8(arguments[index]);
        } else {
            result.valid = false;
            result.error = "unknown installer option: " + argument;
            return result;
        }
    }
    return result;
}

StartupDecision decide_startup(const fs::path& current_executable,
                               const StartupOptions& options) {
    StartupDecision result;
    if (!options.valid || current_executable.empty() ||
        !fs::is_regular_file(current_executable)) {
        result.error = options.error.empty() ? "running installer path is invalid" : options.error;
        return result;
    }
    const auto executable = fs::absolute(current_executable).lexically_normal();
    const auto setup_paths = InstallPaths::from_executable(executable);
    if (options.install_dir.empty() && fs::is_regular_file(setup_paths.setup_toml)) {
        const auto config = load_config(setup_paths);
        result.configured_root = config.baas_root_path.empty() ? "." : config.baas_root_path;
        const auto configured_path = path_from_utf8(result.configured_root);
        const auto validation = validate_install_target(executable, configured_path);
        if (!validation.accepted) {
            result.error = validation.error;
            return result;
        }
        result.target_root = validation.root;
        result.mode = StartupMode::ExistingInstallation;
        result.paths = InstallPaths::from_install_root(result.target_root, executable);
        return result;
    }

    result.mode = StartupMode::SelectInstallTarget;
    result.configured_root = options.install_dir.empty() ? "." : path_to_utf8(options.install_dir);
    result.target_root = resolve_install_root(executable, result.configured_root);
    return result;
}

}  // namespace baas_installer
