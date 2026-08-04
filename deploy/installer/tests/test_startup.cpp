#include "baas_installer/startup.hpp"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>

namespace fs = std::filesystem;

namespace {

void write_file(const fs::path& path, const std::string& value) {
    fs::create_directories(path.parent_path());
    std::ofstream(path, std::ios::binary) << value;
}

int fail(const std::string& message) {
    std::cerr << message << '\n';
    return 1;
}

}  // namespace

int main() {
    const auto nonce = std::chrono::steady_clock::now().time_since_epoch().count();
    const auto fixture = fs::temp_directory_path() /
        ("baas-installer-startup-" + std::to_string(nonce));
    const auto source = fixture / "Downloads" / "BAAS-Installer.exe";
    write_file(source, "installer");

    const auto parsed = baas_installer::parse_startup_arguments(
        {"--install-dir", (fixture / "Custom BAAS").string(), "--auto-exit", "--no-launch"});
    if (!parsed.valid || !parsed.auto_exit || !parsed.no_launch ||
        parsed.install_dir != fixture / "Custom BAAS" ||
        parsed.forwarded_arguments != std::vector<std::string>{"--auto-exit", "--no-launch"}) {
        return fail("startup arguments were not parsed into safe forwarded state");
    }
    const auto selection = baas_installer::decide_startup(source, parsed);
    if (selection.mode != baas_installer::StartupMode::SelectInstallTarget ||
        selection.target_root != fs::absolute(fixture / "Custom BAAS").lexically_normal() ||
        selection.configured_root != (fixture / "Custom BAAS").string()) {
        return fail("an explicit absolute target was not retained and resolved");
    }

    const auto defaults = baas_installer::decide_startup(
        source, baas_installer::parse_startup_arguments({}));
    if (defaults.mode != baas_installer::StartupMode::SelectInstallTarget ||
        defaults.target_root != fs::absolute(source.parent_path()).lexically_normal() ||
        defaults.configured_root != ".") {
        return fail("first run did not default to the executable directory using dot: actual=" +
                    defaults.target_root.string() + " expected=" +
                    fs::absolute(source.parent_path()).lexically_normal().string() +
                    " configured=" + defaults.configured_root);
    }

    if (baas_installer::parse_startup_arguments({"--migration-target", "anything"}).valid) {
        return fail("the removed self-migration option was still accepted");
    }

    write_file(source.parent_path() / "setup.toml",
               "schema_version = 1\n[paths]\nbaas_root_path = \"BAAS\"\n");
    write_file(source.parent_path() / "BAAS" / ".baas-installer" / "installer.lock", "managed\n");
    const auto existing = baas_installer::decide_startup(
        source, baas_installer::parse_startup_arguments({}));
    if (existing.mode != baas_installer::StartupMode::ExistingInstallation ||
        existing.paths.root != fs::absolute(source.parent_path() / "BAAS").lexically_normal() ||
        existing.paths.setup_toml != source.parent_path() / "setup.toml" ||
        existing.paths.executable != fs::absolute(source).lexically_normal()) {
        return fail("installer-local setup did not resolve its relative BAAS root");
    }

    write_file(source.parent_path() / "setup.toml",
               "schema_version = 1\n[paths]\nbaas_root_path = \"蔚蓝档案\"\n");
    const auto chinese_config = baas_installer::decide_startup(
        source, baas_installer::parse_startup_arguments({}));
    if (chinese_config.mode != baas_installer::StartupMode::Invalid ||
        chinese_config.error.find("Qt") == std::string::npos ||
        fs::exists(source.parent_path() / fs::path(L"蔚蓝档案"))) {
        return fail("a configured Chinese installation path was not rejected without filesystem changes");
    }

    const auto malformed = baas_installer::parse_startup_arguments({"--install-dir"});
    if (malformed.valid) return fail("a missing --install-dir value was accepted");

    write_file(source.parent_path() / "setup.toml",
               "schema_version = 1\n[paths]\nbaas_root_path = \"../BAAS\"\n");
    const auto parent_config = baas_installer::decide_startup(
        source, baas_installer::parse_startup_arguments({}));
    if (parent_config.mode != baas_installer::StartupMode::Invalid ||
        parent_config.error.find("parent") == std::string::npos) {
        return fail("installer-local setup bypassed relative parent-path rejection");
    }

    std::error_code cleanup_error;
    fs::remove_all(fixture, cleanup_error);
    if (cleanup_error) return fail("could not remove isolated startup fixture");
    return 0;
}
