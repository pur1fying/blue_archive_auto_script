#include "baas_installer/uv_environment.hpp"

#include <algorithm>
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
    const auto custom_environment = baas_installer::make_uv_environment(paths, config);
    if (custom_environment.managed || custom_environment.variables.contains("UV_PROJECT_ENVIRONMENT")) {
        std::cerr << "custom runtime not respected\n"; return 1;
    }
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
    std::ofstream(baas_installer::dependency_requirements(test_paths)) << "example==1\n";
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

    const auto custom_root = std::filesystem::temp_directory_path() / "baas-installer-uv-custom-test";
    std::filesystem::remove_all(custom_root, ignored);
    const auto custom_paths = baas_installer::InstallPaths::from_executable(custom_root / "BlueArchiveAutoScript.exe");
    baas_installer::InstallerConfig custom_config;
    custom_config.runtime_path = "D:/Custom Python/python.exe";
    const auto custom_uv = baas_installer::make_uv_environment(custom_paths, custom_config);
    std::filesystem::create_directories(custom_uv.executable.parent_path());
    std::ofstream(custom_uv.executable) << "fake";
    std::filesystem::create_directories(custom_paths.root);
    std::ofstream(baas_installer::dependency_requirements(custom_paths)) << "example==1\n";
    std::vector<baas_installer::ProcessSpec> custom_commands;
    const auto custom_executor = [&](const baas_installer::ProcessSpec& spec) {
        custom_commands.push_back(spec);
        return baas_installer::ProcessResult{0, {}};
    };
    if (!baas_installer::sync_portable_uv(custom_paths, custom_config, sync_error, {}, custom_executor) ||
        custom_commands.size() != 3) {
        std::cerr << "custom Python dependencies were not synchronized through uv\n"; return 1;
    }
    for (const auto& spec : custom_commands) {
        if (std::find(spec.arguments.begin(), spec.arguments.end(), "install") != spec.arguments.end() ||
            std::find(spec.arguments.begin(), spec.arguments.end(), "venv") != spec.arguments.end()) {
            std::cerr << "custom runtime attempted portable Python creation\n"; return 1;
        }
    }
    const auto& sync_arguments = custom_commands[1].arguments;
    const auto python = std::find(sync_arguments.begin(), sync_arguments.end(), "--python");
    if (python == sync_arguments.end() || std::next(python) == sync_arguments.end() ||
        *std::next(python) != custom_config.runtime_path) {
        std::cerr << "custom runtime was not passed to uv pip sync\n"; return 1;
    }
#ifdef _WIN32
    if (baas_installer::dependency_requirements(custom_paths).filename() != "requirements.txt") return 1;
#else
    if (baas_installer::dependency_requirements(custom_paths).filename() != "requirements-linux.txt") return 1;
#endif
    if (baas_installer::expected_uv_sha256().size() != 64) {
        std::cerr << "pinned uv digest missing\n"; return 1;
    }
    std::filesystem::remove_all(custom_root, ignored);
    return 0;
}
