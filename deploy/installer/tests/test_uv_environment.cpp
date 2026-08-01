#include "baas_installer/uv_environment.hpp"

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
    return 0;
}
