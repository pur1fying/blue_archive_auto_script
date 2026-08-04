#include "baas_installer/paths.hpp"

#include <cassert>
#include <filesystem>

int main() {
#ifdef _WIN32
    const auto executable = std::filesystem::path(R"(E:\tmp\BAAS\BlueArchiveAutoScript.exe)");
    const auto launcher = std::filesystem::path(R"(E:\tmp\Launcher)");
#else
    const auto executable = std::filesystem::path("/tmp/BAAS/BlueArchiveAutoScript");
    const auto launcher = std::filesystem::path("/tmp/Launcher");
#endif
    const auto paths = baas_installer::InstallPaths::from_executable(
        executable);

    assert(paths.executable == executable);
    assert(paths.root == executable.parent_path());
    assert(paths.setup_toml == paths.root / "setup.toml");
    assert(paths.tmp_dir == paths.root / "tmp");
    assert(paths.toolkit_dir == paths.root / "toolkit");
    assert(paths.uv_dir == paths.root / "toolkit" / "uv");
    assert(paths.venv_dir == paths.root / ".venv");
    assert(paths.logs_dir == paths.root / "log");
    assert(paths.state_dir == paths.root / ".baas-installer");

    const auto split = baas_installer::InstallPaths::from_install_root(
        launcher / "BAAS", launcher / "BAAS-Installer.exe");
    assert(split.executable == launcher / "BAAS-Installer.exe");
    assert(split.root == launcher / "BAAS");
    assert(split.setup_toml == launcher / "setup.toml");
    assert(split.tmp_dir == split.root / "tmp");
    const auto unicode = launcher / std::filesystem::path(L"蔚蓝档案") /
                         std::filesystem::path(L"安装目录");
    assert(baas_installer::path_from_utf8(baas_installer::path_to_utf8(unicode)) == unicode);
    return 0;
}
