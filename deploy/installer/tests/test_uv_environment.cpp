#include "baas_installer/uv_environment.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>

int main() {
    const auto paths = baas_installer::InstallPaths::from_executable("E:/tmp/BAAS/BlueArchiveAutoScript.exe");
    baas_installer::InstallerConfig config;
    const auto environment = baas_installer::make_uv_environment(paths, config);
    for (const auto& [name, value] : environment.variables) {
        if (name.rfind("UV_", 0) == 0 || name.rfind("XDG_", 0) == 0 || name == "TMPDIR" || name == "TMP" || name == "TEMP") {
            if (value != "1" && value != "0" && value.rfind("E:/tmp/BAAS", 0) != 0) {
                std::cerr << name << " escaped portable root: " << value << '\n'; return 1;
            }
        }
    }
    if (!environment.managed || environment.variables.at("UV_VENV_RELOCATABLE") != "1" ||
        environment.variables.at("UV_NO_CONFIG") != "1" || environment.variables.at("UV_PYTHON_INSTALL_REGISTRY") != "0") {
        std::cerr << "managed uv flags missing\n"; return 1;
    }
    config.runtime_path = "D:/Python";
    if (baas_installer::make_uv_environment(paths, config).managed) { std::cerr << "custom runtime not respected\n"; return 1; }
    config.runtime_path = "default";
    const auto commands = baas_installer::managed_uv_commands(environment, config, paths.root / "requirements.txt");
    if (commands.size() != 4 || commands[1].arguments[1] != "--relocatable" ||
        commands[3].arguments[2] != "--link-mode" || commands[3].arguments[3] != "copy") {
        std::cerr << "relocatable uv commands missing\n"; return 1;
    }

    const auto test_root = std::filesystem::temp_directory_path() / "baas-installer-uv-pty-test";
    std::error_code ignored;
    std::filesystem::remove_all(test_root, ignored);
    const auto test_paths = baas_installer::InstallPaths::from_executable(test_root / "BlueArchiveAutoScript.exe");
    const auto test_environment = baas_installer::make_uv_environment(test_paths, config);
    std::filesystem::create_directories(test_environment.executable.parent_path());
    std::ofstream(test_environment.executable) << "fake";
    std::ofstream(test_paths.root / "requirements.txt") << "example==1\n";
    std::vector<baas_installer::ProcessSpec> visible;
    int chunks = 0;
    const auto fake_terminal = [&](const baas_installer::ProcessSpec& spec) {
        visible.push_back(spec);
        if (spec.arguments.size() > 1 && spec.arguments[1] == "venv") {
            std::filesystem::create_directories(test_paths.venv_dir);
            std::ofstream(test_paths.venv_dir / "pyvenv.cfg") << "version = 3.9.0\n";
        }
        if (spec.on_chunk) spec.on_chunk("pty chunk\r");
        return baas_installer::ProcessResult{0, {}};
    };
    std::string sync_error;
    const bool synced = baas_installer::sync_portable_uv(
        test_paths, config, sync_error,
        [&](std::string_view task, std::string_view backend, std::string_view chunk) {
            if (task == "uv" && backend == "uv" && !chunk.empty()) ++chunks;
        }, fake_terminal);
    if (!synced || visible.size() != 5 || chunks != 5) {
        std::cerr << "visible uv commands did not use the shared PTY observer\n"; return 1;
    }
    for (const auto& spec : visible) {
        if (!spec.use_pty || spec.working_directory != test_paths.root || spec.environment.empty() ||
            spec.arguments.size() < 2 || spec.arguments[1] == "--no-progress") {
            std::cerr << "uv PTY specification is incomplete\n"; return 1;
        }
        for (const auto& [name, value] : spec.environment) {
            const bool remote_setting = name.find("INDEX") != std::string::npos || name.find("MIRROR") != std::string::npos;
            if (!remote_setting && (name.rfind("UV_", 0) == 0 || name.rfind("XDG_", 0) == 0 || name == "TMP" ||
                 name == "TEMP" || name == "TMPDIR") && value != "1" && value != "0" &&
                value.rfind(test_root.generic_string(), 0) != 0) {
                std::cerr << name << " escaped the disposable installation root\n"; return 1;
            }
        }
    }
    visible.clear();
    chunks = 0;
    if (!baas_installer::sync_portable_uv(test_paths, config, sync_error,
            [&](std::string_view, std::string_view, std::string_view) { ++chunks; }, fake_terminal) ||
        visible.size() != 4) {
        std::cerr << "an existing managed environment should be synchronized without destructive recreation\n";
        return 1;
    }
    for (const auto& spec : visible) {
        if (spec.arguments.size() > 1 && spec.arguments[1] == "venv") {
            std::cerr << "existing managed environment was recreated\n";
            return 1;
        }
    }
    std::filesystem::remove_all(test_root, ignored);
    return 0;
}
