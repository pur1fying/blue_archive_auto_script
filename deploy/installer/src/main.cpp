#include "baas_installer/config.hpp"
#include "baas_installer/paths.hpp"
#include "baas_installer/tui.hpp"

#include <filesystem>
#include <iostream>

int main(int argc, char* argv[]) {
    const auto executable = argc > 0 ? std::filesystem::absolute(std::filesystem::path(argv[0])) : std::filesystem::path{};
    const auto paths = baas_installer::InstallPaths::from_executable(executable);
    if (argc > 1 && std::string(argv[1]) == "--help") {
        std::cout << "BAAS portable installer\n\nOptions:\n  --help       show this help\n  --print-root print the executable-relative install root\n";
        return 0;
    }
    if (argc > 1 && std::string(argv[1]) == "--print-root") { std::cout << paths.root.string() << '\n'; return 0; }
    const bool first_start = !std::filesystem::exists(paths.setup_toml);
    auto config = baas_installer::load_config(paths);
    baas_installer::print_tui_banner();
    baas_installer::print_progress("root", "ready", paths.root.string());
    if (first_start) {
        if (baas_installer::ask_yes_no("Do you have a MirrorChyan CDK?")) {
            config.mirrorc_cdk = baas_installer::ask_secret("MirrorChyan CDK (masked): ");
            baas_installer::print_progress("MirrorChyan", "configured", baas_installer::redact_cdk(config.mirrorc_cdk));
        } else baas_installer::print_progress("MirrorChyan", "not selected", "Git source fallback will be used");
        // The install workflow will make the final atomic write after all
        // staged work is successful; retaining this in-memory answer prevents
        // a cancelled first run from creating a half-configured installation.
    }
    baas_installer::print_progress("installer", "ready", "use the release build to start installation");
    return 0;
}
