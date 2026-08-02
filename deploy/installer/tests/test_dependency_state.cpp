#include "baas_installer/dependency_state.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>

namespace fs = std::filesystem;

namespace {

void write(const fs::path& path, const std::string& value) {
    fs::create_directories(path.parent_path());
    std::ofstream(path, std::ios::binary | std::ios::trunc) << value;
}

fs::path venv_python(const baas_installer::InstallPaths& paths) {
#ifdef _WIN32
    return paths.venv_dir / "Scripts" / "python.exe";
#else
    return paths.venv_dir / "bin" / "python";
#endif
}

std::string managed_home_suffix() {
#ifdef _WIN32
    return "cpython-3.9.0-windows-x86_64-none";
#else
    return "cpython-3.9.0-linux-x86_64-none/bin";
#endif
}

std::string old_managed_home() {
#ifdef _WIN32
    return "D:\\Old\\BAAS\\toolkit\\uv\\cpython\\" + managed_home_suffix();
#else
    return "/old/BAAS/toolkit/uv/cpython/" + managed_home_suffix();
#endif
}

}  // namespace

int main() {
    const auto fixture = fs::temp_directory_path() / "baas-installer-dependency-state-test";
    std::error_code ignored;
    fs::remove_all(fixture, ignored);
    const auto paths = baas_installer::InstallPaths::from_executable(fixture / "new-root" / "BlueArchiveAutoScript.exe");
    const auto other_paths = baas_installer::InstallPaths::from_executable(fixture / "another-root" / "BlueArchiveAutoScript.exe");
    baas_installer::InstallerConfig config;
    const auto requirements = paths.root / "requirements.txt";
    const auto lock = paths.root / ".baas-installer-requirements.txt";
    const auto other_requirements = other_paths.root / "requirements.txt";
    const auto other_lock = other_paths.root / ".baas-installer-requirements.txt";
    write(requirements, "example==1\n");
    write(lock, "example==1.2.3\n");
    write(other_requirements, "example==1\n");
    write(other_lock, "example==1.2.3\n");

    const auto first = baas_installer::make_dependency_stamp(paths, config, requirements, lock);
    const auto moved = baas_installer::make_dependency_stamp(other_paths, config, other_requirements, other_lock);
    if (first.input_sha256.empty() || first.input_sha256 != moved.input_sha256 ||
        first.lock_sha256 != moved.lock_sha256) {
        std::cerr << "portable dependency fingerprint depends on the installation root\n";
        return 1;
    }
    write(other_requirements, "example==2\n");
    if (baas_installer::make_dependency_stamp(other_paths, config, other_requirements, other_lock).input_sha256 ==
        first.input_sha256) {
        std::cerr << "requirements mutation did not invalidate the input digest\n";
        return 1;
    }

    write(paths.venv_dir / ".baas-installer-managed", "python=3.9.0\n");
#ifdef _WIN32
    write(venv_python(paths), "python placeholder");
#else
    fs::create_directories(venv_python(paths).parent_path());
    fs::create_symlink(fs::path(old_managed_home()) / "python3.9", venv_python(paths));
#endif
    const auto managed_home = paths.toolkit_dir / "uv" / "cpython" / fs::path(managed_home_suffix());
    fs::create_directories(managed_home);
#ifdef _WIN32
    write(managed_home / "python.exe", "managed python placeholder");
#else
    write(managed_home / "python3", "managed python placeholder");
    write(managed_home / "python3.9", "managed python placeholder");
#endif
    write(paths.venv_dir / "pyvenv.cfg", "home = " + old_managed_home() + "\nversion_info = 3.9.0\n");
    auto obsolete = first;
    obsolete.input_sha256 = std::string(64, '0');
    baas_installer::save_dependency_stamp_atomic(obsolete, paths);
    baas_installer::save_dependency_stamp_atomic(first, paths);

    std::string repair_error;
    if (!baas_installer::repair_managed_venv_after_move(paths, config, repair_error)) {
        std::cerr << "managed relocation repair failed: " << repair_error << '\n';
        return 1;
    }
    std::ifstream repaired_input(paths.venv_dir / "pyvenv.cfg", std::ios::binary);
    const std::string repaired{std::istreambuf_iterator<char>(repaired_input), {}};
    if (repaired.find(paths.toolkit_dir.string()) == std::string::npos ||
        repaired.find(old_managed_home()) != std::string::npos) {
        std::cerr << "managed pyvenv.cfg retained its old root\n";
        return 1;
    }
#ifndef _WIN32
    const auto repaired_link = fs::read_symlink(venv_python(paths));
    if (repaired_link.string().find(paths.toolkit_dir.string()) == std::string::npos ||
        repaired_link.string().find(old_managed_home()) != std::string::npos) {
        std::cerr << "managed virtualenv interpreter symlink retained its old root\n";
        return 1;
    }
#endif
    const auto state = baas_installer::inspect_dependency_state(paths, config, requirements, lock);
    if (!state.cache_hit) {
        std::cerr << "complete matching managed environment did not hit dependency cache: " << state.reason << '\n';
        return 1;
    }

    fs::remove(venv_python(paths), ignored);
    if (baas_installer::inspect_dependency_state(paths, config, requirements, lock).cache_hit) {
        std::cerr << "missing virtualenv interpreter incorrectly hit dependency cache\n";
        return 1;
    }
    write(venv_python(paths), "python placeholder");

    write(requirements, "example==changed\n");
    if (baas_installer::inspect_dependency_state(paths, config, requirements, lock).cache_hit) {
        std::cerr << "changed requirements incorrectly hit dependency cache\n";
        return 1;
    }
    write(requirements, "example==1\n");
    fs::remove(lock, ignored);
    if (baas_installer::inspect_dependency_state(paths, config, requirements, lock).cache_hit) {
        std::cerr << "missing lock incorrectly hit dependency cache\n";
        return 1;
    }

    const auto external_paths = baas_installer::InstallPaths::from_executable(
        fixture / "external" / "BlueArchiveAutoScript.exe");
    write(external_paths.venv_dir / "pyvenv.cfg", "home = C:\\ExternalPython\n");
    write(external_paths.venv_dir / ".baas-installer-managed", "python=3.9.0\n");
    if (!baas_installer::repair_managed_venv_after_move(external_paths, config, repair_error)) return 1;
    std::ifstream external_input(external_paths.venv_dir / "pyvenv.cfg", std::ios::binary);
    const std::string external{std::istreambuf_iterator<char>(external_input), {}};
    if (external.find("C:\\ExternalPython") == std::string::npos) {
        std::cerr << "relocation repair rewrote an unrelated external interpreter\n";
        return 1;
    }

    fs::remove_all(fixture, ignored);
    return 0;
}
