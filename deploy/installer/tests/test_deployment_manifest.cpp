#include "baas_installer/deployment_manifest.hpp"
#include "baas_installer/paths.hpp"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace fs = std::filesystem;

namespace {

int fail(const std::string& message) {
    std::cerr << message << '\n';
    return 1;
}

}  // namespace

int main() {
    const auto nonce = std::chrono::steady_clock::now().time_since_epoch().count();
    const auto fixture = fs::temp_directory_path() /
        ("baas-installer-manifest-" + std::to_string(nonce));
    const auto paths = baas_installer::InstallPaths::from_root(fixture, "BAAS-Installer.exe");

    const baas_installer::DeploymentFileSet main_files{
        fs::path("main.py"), fs::path("module") / "feature.py",
        baas_installer::path_from_utf8("资源") /
            baas_installer::path_from_utf8("中文文件.json")};
    baas_installer::save_deployment_manifest_atomic(
        paths, baas_installer::DeploymentTree::Main, main_files);
    const auto loaded = baas_installer::load_deployment_manifest(
        paths, baas_installer::DeploymentTree::Main);
    if (!loaded.exists || !loaded.valid || loaded.files != main_files) {
        return fail("a valid deployment manifest did not round-trip exactly");
    }

    for (const auto& unsafe : baas_installer::DeploymentFileSet{
             fs::path("../outside.txt"), fs::absolute(fixture / "absolute.txt"),
             fs::path("config") / "user.json", fs::path("setup.toml"),
             fs::path("core/ocr/baas_ocr_client/bin/server.exe")}) {
        bool rejected = false;
        try {
            baas_installer::save_deployment_manifest_atomic(
                paths, baas_installer::DeploymentTree::Main, {unsafe});
        } catch (const std::invalid_argument&) {
            rejected = true;
        }
        if (!rejected) return fail("an unsafe main-manifest path was accepted");
    }

    const auto manifest_path = baas_installer::deployment_manifest_path(
        paths, baas_installer::DeploymentTree::Main);
    std::ofstream(manifest_path, std::ios::binary | std::ios::trunc) << "not valid json";
    const auto corrupt = baas_installer::load_deployment_manifest(
        paths, baas_installer::DeploymentTree::Main);
    if (!corrupt.exists || corrupt.valid || !corrupt.files.empty()) {
        return fail("a corrupt manifest was trusted for deletion");
    }

    const baas_installer::DeploymentFileSet ocr_files{
        fs::path("BAAS_ocr_server.exe"), fs::path("models") / "ocr.bin"};
    baas_installer::save_deployment_manifest_atomic(
        paths, baas_installer::DeploymentTree::Ocr, ocr_files);
    const auto loaded_ocr = baas_installer::load_deployment_manifest(
        paths, baas_installer::DeploymentTree::Ocr);
    if (!loaded_ocr.valid || loaded_ocr.files != ocr_files) {
        return fail("OCR manifest did not use its own relative ownership root");
    }

    std::error_code cleanup_error;
    fs::remove_all(fixture, cleanup_error);
    if (cleanup_error) return fail("could not remove isolated manifest fixture");
    return 0;
}
