#include "baas_installer/paths.hpp"

#include <cassert>
#include <filesystem>

int main() {
    const auto paths = baas_installer::InstallPaths::from_executable(
        R"(E:\tmp\BAAS\BlueArchiveAutoScript.exe)");

    assert(paths.executable == std::filesystem::path(R"(E:\tmp\BAAS\BlueArchiveAutoScript.exe)"));
    assert(paths.root == std::filesystem::path(R"(E:\tmp\BAAS)"));
    assert(paths.setup_toml == paths.root / "setup.toml");
    assert(paths.tmp_dir == paths.root / "tmp");
    assert(paths.toolkit_dir == paths.root / "toolkit");
    assert(paths.uv_dir == paths.root / "toolkit" / "uv");
    assert(paths.venv_dir == paths.root / ".venv");
    assert(paths.logs_dir == paths.root / "log");
    assert(paths.state_dir == paths.root / ".baas-installer");
    return 0;
}
