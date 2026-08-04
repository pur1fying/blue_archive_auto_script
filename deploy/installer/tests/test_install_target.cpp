#include "baas_installer/install_target.hpp"
#include "baas_installer/paths.hpp"

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
                         ("baas-installer-target-" + std::to_string(nonce));
    const auto launcher = fixture / "launcher";
    const auto source = launcher / "BAAS-Installer.exe";
    fs::create_directories(launcher);
    write_file(source, "installer");

    const auto default_root = baas_installer::default_install_root(source);
    if (default_root != launcher) return fail("first-run default is not the executable directory");

    const auto absent = baas_installer::validate_install_target(source, default_root);
    if (!absent.accepted || absent.root != fs::absolute(default_root).lexically_normal() ||
        absent.existing_installation) {
        return fail("an executable-only directory was rejected for dot installation");
    }

    write_file(launcher / "family-photo.jpg", "irreplaceable-user-data");
    const auto unsafe_dot = baas_installer::validate_install_target(source, launcher);
    if (unsafe_dot.accepted || !fs::is_regular_file(launcher / "family-photo.jpg")) {
        return fail("dot installation accepted or modified an unrelated sibling file");
    }
    fs::remove(launcher / "family-photo.jpg");

    write_file(launcher / "setup.toml", "[paths]\nbaas_root_path = \".\"\n");
    write_file(launcher / ".baas-installer" / "installer.lock", "managed\n");
    write_file(launcher / "main.py", "# installed BAAS\n");
    write_file(launcher / "normal-installed-file.dat", "managed BAAS content");
    const auto installed_dot = baas_installer::validate_install_target(source, launcher);
    if (!installed_dot.accepted || !installed_dot.existing_installation) {
        return fail("an existing dot installation was subjected to first-install cleanliness checks");
    }
    fs::remove(launcher / "normal-installed-file.dat");
    fs::remove(launcher / "main.py");
    fs::remove_all(launcher / ".baas-installer");
    fs::remove(launcher / "setup.toml");

    const auto empty = launcher / "empty-target";
    fs::create_directories(empty);
    write_file(launcher / "unrelated-launcher-file.txt", "must not affect a separate target");
    if (!baas_installer::validate_install_target(source, empty).accepted ||
        !fs::is_regular_file(launcher / "unrelated-launcher-file.txt")) {
        return fail("an unrelated launcher-directory file blocked or was modified for a separate target");
    }
    fs::remove(launcher / "unrelated-launcher-file.txt");

    const auto unknown = launcher / "unknown-target";
    write_file(unknown / "tax-records.txt", "user-owned");
    const auto unknown_result = baas_installer::validate_install_target(source, unknown);
    if (unknown_result.accepted || !fs::is_regular_file(unknown / "tax-records.txt")) {
        return fail("a populated unknown directory was accepted or modified");
    }

    const auto recognized = launcher / "existing-baas";
    fs::remove_all(empty);
    fs::remove_all(unknown);
    write_file(recognized / "main.py", "# BAAS\n");
    write_file(recognized / "requirements.txt", "requests\n");
    const auto recognized_result = baas_installer::validate_install_target(source, recognized);
    if (!recognized_result.accepted || !recognized_result.existing_installation) {
        return fail("a recognized BAAS installation was rejected");
    }
    fs::remove_all(recognized);

    const auto ambiguous_state = launcher / "ambiguous-state";
    fs::create_directories(ambiguous_state / ".baas-installer");
    if (baas_installer::validate_install_target(source, ambiguous_state).accepted) {
        return fail("an empty state-directory name alone established installer ownership");
    }
    fs::remove_all(ambiguous_state);

    const auto nested = launcher / "nested" / "deeper" / "BAAS";
    fs::create_directories(nested);
    if (!baas_installer::validate_install_target(source, nested).accepted) {
        return fail("a clean descendant corridor was rejected");
    }
    write_file(launcher / "nested" / "unrelated.txt", "preserve");
    if (!baas_installer::validate_install_target(source, nested).accepted ||
        !fs::is_regular_file(launcher / "nested" / "unrelated.txt")) {
        return fail("an unrelated ancestor sibling blocked or was modified for a dedicated target");
    }

    const auto root_result = baas_installer::validate_install_target(source, launcher.root_path());
    if (root_result.accepted) return fail("a filesystem root was accepted");

    for (const auto& parent_relative : {fs::path(".."), fs::path("../BAAS"),
                                        fs::path("child/../BAAS")}) {
        const auto parent_result = baas_installer::validate_install_target(source, parent_relative);
        if (parent_result.accepted || parent_result.error.find("parent") == std::string::npos) {
            return fail("a relative installation path containing a parent component was accepted");
        }
    }

    fs::remove_all(launcher / "nested");
    const auto unicode_target = launcher / fs::path(L"蔚蓝档案") / fs::path(L"安装目录");
    const auto unicode_result = baas_installer::validate_install_target(source, unicode_target);
    if (unicode_result.accepted || unicode_result.error.find("Qt") == std::string::npos ||
        fs::exists(unicode_target)) {
        return fail("a Chinese target was not rejected before creating files with a Qt explanation");
    }

    const auto target_paths = baas_installer::InstallPaths::from_install_root(
        unicode_target, source);
    if (target_paths.root != fs::absolute(unicode_target).lexically_normal() ||
        target_paths.executable != fs::absolute(source).lexically_normal() ||
        target_paths.setup_toml != fs::absolute(source.parent_path() / "setup.toml").lexically_normal()) {
        return fail("split install paths did not keep setup beside the executable");
    }

    const auto link_target = fixture / "linked-storage";
    const auto link = fixture / "target-link";
    fs::create_directories(link_target);
    std::error_code link_error;
    fs::create_directory_symlink(link_target, link, link_error);
    if (!link_error && baas_installer::validate_install_target(source, link / "BAAS").accepted) {
        return fail("a target crossing a symlink was accepted");
    }

    const auto linked_launcher = fixture / "linked-launcher";
    fs::create_directories(linked_launcher);
    const auto linked_executable = linked_launcher / source.filename();
    std::error_code executable_link_error;
    fs::create_symlink(source, linked_executable, executable_link_error);
    if (!executable_link_error &&
        baas_installer::validate_install_target(linked_executable, linked_launcher).accepted) {
        return fail("an installer executable reached through a symbolic link was accepted");
    }

    std::error_code cleanup_error;
    fs::remove_all(fixture, cleanup_error);
    if (cleanup_error) return fail("could not remove isolated target test fixture");
    return 0;
}
