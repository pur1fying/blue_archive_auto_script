#include "baas_installer/mirrorchyan.hpp"
#include "baas_installer/process.hpp"

#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

int main() {
    const auto platform = baas_installer::current_mirror_platform();
#ifdef _WIN32
    if (platform.os != "windows" || platform.arch != "amd64") {
#elif defined(__APPLE__) && (defined(__aarch64__) || defined(__arm64__))
    if (platform.os != "darwin" || platform.arch != "arm64") {
#elif defined(__APPLE__)
    if (platform.os != "darwin" || platform.arch != "amd64") {
#elif defined(__aarch64__) || defined(__arm64__)
    if (platform.os != "linux" || platform.arch != "arm64") {
#else
    if (platform.os != "linux" || platform.arch != "amd64") {
#endif
        std::cerr << "MirrorChyan platform mapping failed\n";
        return 1;
    }
    std::string archive_error;
    if (!baas_installer::validate_archive_entries({"root/", "root/main.py", "root/nested/file", "root/中文路径.json"}, archive_error)) {
        std::cerr << "safe archive entries were rejected\n";
        return 1;
    }
    for (const auto& unsafe_entries : {std::vector<std::string>{"../escape"},
                                      std::vector<std::string>{"root/../../escape"},
                                      std::vector<std::string>{"C:/absolute"},
                                      std::vector<std::string>{"/absolute"}}) {
        archive_error.clear();
        if (baas_installer::validate_archive_entries(unsafe_entries, archive_error) || archive_error.empty()) {
            std::cerr << "unsafe archive entry was accepted\n";
            return 1;
        }
    }
    const auto release = baas_installer::parse_mirror_response(R"({"code":0,"msg":"ok","data":{"version_name":"abc","url":"https://example.invalid/a.zip","sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","update_type":"full"}})");
    if (release.status != baas_installer::CdkStatus::Valid || release.version != "abc") { std::cerr << "valid response failed\n"; return 1; }
    const auto malformed = baas_installer::parse_mirror_response(R"({"code":0,"data":{"url":"https://x","sha256":"bad"}})");
    if (malformed.status != baas_installer::CdkStatus::Malformed || baas_installer::is_sha256("bad")) { std::cerr << "invalid digest accepted\n"; return 1; }
    const auto file = std::filesystem::temp_directory_path() / "baas-installer-sha-test";
    std::ofstream(file, std::ios::binary) << "abc";
    const auto good = baas_installer::verify_sha256(file, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    std::error_code ignored;
    if (!good) { std::cerr << "sha256 verification failed\n"; return 1; }
#ifdef BAAS_INSTALLER_TEST_HAS_CURL
    auto local_release = baas_installer::MirrorRelease{
        .status = baas_installer::CdkStatus::Valid,
        .download_url = "file:///" + file.generic_string(),
        .sha256 = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        .update_type = "full",
    };
    const auto downloaded_file = file.string() + ".downloaded";
    std::vector<std::pair<std::uint64_t, std::uint64_t>> download_progress;
    std::string download_error;
    if (!baas_installer::download_mirror_package(
            local_release, downloaded_file, download_error,
            [&](const std::uint64_t downloaded, const std::uint64_t total) {
                download_progress.emplace_back(downloaded, total);
            }) ||
        download_progress.empty() || download_progress.back().first != 3 ||
        !std::filesystem::is_regular_file(downloaded_file)) {
        std::cerr << "Mirror package download did not expose live transfer progress\n";
        return 1;
    }
    std::filesystem::remove(downloaded_file, ignored);
#endif
    std::filesystem::remove(file, ignored);
    if (baas_installer::mirror_latest_url("a b", "", "stable").find("cdk=a%20b") == std::string::npos) { std::cerr << "CDK escaping failed\n"; return 1; }

    const auto main_url = baas_installer::mirror_latest_url(
        baas_installer::MirrorResource::Main, {}, {}, "secret value", "old", "stable");
    const auto ocr_url = baas_installer::mirror_latest_url(
        baas_installer::MirrorResource::Ocr, "windows", "x64", "secret value", "old", "stable");
    if (main_url.find("/BAAS_repo/latest") == std::string::npos || main_url.find("os=") != std::string::npos ||
        ocr_url.find("/BAAS_Cpp/latest") == std::string::npos || ocr_url.find("os=windows") == std::string::npos ||
        ocr_url.find("arch=x64") == std::string::npos || ocr_url.find("cdk=secret%20value") == std::string::npos) {
        std::cerr << "MirrorChyan main/OCR resource URL generation failed\n";
        return 1;
    }
    std::string request_error;
    const auto failed_request = baas_installer::request_mirror_release(
        "https://example.invalid/latest?cdk=must-not-leak", request_error, 1);
    if (failed_request.status != baas_installer::CdkStatus::ServerError || request_error.empty() ||
        request_error.find("must-not-leak") != std::string::npos) {
        std::cerr << "MirrorChyan request failure was not sanitized\n";
        return 1;
    }

    const auto current = baas_installer::parse_mirror_response(
        R"({"code":0,"msg":"already current","data":{"version_name":"abc"}})");
    if (current.status != baas_installer::CdkStatus::UpToDate || current.version != "abc") {
        std::cerr << "MirrorChyan no-download response must be treated as up to date\n";
        return 1;
    }

    const auto root = std::filesystem::temp_directory_path() / "baas-installer-mirror-manifest-test";
    std::filesystem::remove_all(root, ignored);
    std::filesystem::create_directories(root / "archive-root" / "nested");
    std::ofstream(root / "archive-root" / "new.txt") << "new";
    std::ofstream(root / "archive-root" / "nested" / "changed.txt") << "changed";
    std::string changes_error;
    const auto changes = baas_installer::parse_mirror_changes(
        R"({"deleted":["archive-root/old.txt"],"added":["archive-root/new.txt"],"modified":["archive-root/nested/changed.txt"]})",
        root, changes_error);
    if (!changes_error.empty() || changes.deleted != std::vector<std::filesystem::path>{"old.txt"} ||
        changes.added != std::vector<std::filesystem::path>{"new.txt"} ||
        changes.modified != std::vector<std::filesystem::path>{std::filesystem::path("nested") / "changed.txt"}) {
        std::cerr << "valid incremental manifest was not normalized\n";
        std::filesystem::remove_all(root, ignored);
        return 1;
    }
    std::ofstream(root / "changes.json")
        << R"({"deleted":["archive-root/old.txt"],"added":["archive-root/new.txt"],"modified":["archive-root/nested/changed.txt"]})";
    auto incremental_release = release;
    incremental_release.update_type = "incremental";
    incremental_release.version = "next";
    const auto incremental_package = baas_installer::inspect_mirror_staging(incremental_release, root, changes_error);
    if (!changes_error.empty() || incremental_package.mode != baas_installer::MirrorPackageMode::Incremental ||
        incremental_package.version != "next" || incremental_package.changes.added.size() != 1) {
        std::cerr << "incremental MirrorChyan staging inspection failed\n";
        std::filesystem::remove_all(root, ignored);
        return 1;
    }

    const auto full_root = root / "full";
    std::filesystem::create_directories(full_root / "blue_archive_auto_script");
    std::ofstream(full_root / "blue_archive_auto_script" / "main.py") << "print('ok')";
    auto full_release = release;
    full_release.update_type = "full";
    full_release.version = "full-next";
    const auto full_package = baas_installer::inspect_mirror_staging(full_release, full_root, changes_error);
    if (!changes_error.empty() || full_package.mode != baas_installer::MirrorPackageMode::Full ||
        full_package.content_root.filename() != "blue_archive_auto_script") {
        std::cerr << "full MirrorChyan staging inspection failed\n";
        std::filesystem::remove_all(root, ignored);
        return 1;
    }
    int retry_attempts = 0;
    const auto retried = baas_installer::wait_for_incremental_release(
        full_release,
        [&] {
            ++retry_attempts;
            auto next = full_release;
            if (retry_attempts == 3) next.update_type = "incremental";
            return next;
        },
        [] {}, 10);
    if (retried.update_type != "incremental" || retry_attempts != 3) {
        std::cerr << "incremental MirrorChyan package retry did not stop on success\n";
        return 1;
    }
    retry_attempts = 0;
    const auto fallback_full = baas_installer::wait_for_incremental_release(
        full_release, [&] { ++retry_attempts; return full_release; }, [] {}, 10);
    if (fallback_full.update_type != "full" || retry_attempts != 10) {
        std::cerr << "full MirrorChyan package fallback did not use the bounded retry count\n";
        return 1;
    }
    for (const auto& unsafe : {
             R"({"deleted":["archive-root/../escape"],"added":[],"modified":[]})",
             R"({"deleted":["C:/absolute"],"added":[],"modified":[]})",
             R"({"deleted":[],"added":["archive-root/missing.txt"],"modified":[]})",
             R"({"deleted":"not-an-array","added":[],"modified":[]})"}) {
        changes_error.clear();
        (void)baas_installer::parse_mirror_changes(unsafe, root, changes_error);
        if (changes_error.empty()) {
            std::cerr << "unsafe or malformed incremental manifest was accepted\n";
            std::filesystem::remove_all(root, ignored);
            return 1;
        }
    }
    std::filesystem::remove_all(root, ignored);
#ifdef _WIN32
    const auto archive_fixture = std::filesystem::temp_directory_path() / "baas-installer-mirror-archive-fixture";
    const auto archive_path = std::filesystem::temp_directory_path() / "baas-installer-mirror-archive.zip";
    const auto extracted = std::filesystem::temp_directory_path() / "baas-installer-mirror-archive-output";
    std::filesystem::remove_all(archive_fixture, ignored);
    std::filesystem::remove_all(extracted, ignored);
    std::filesystem::remove(archive_path, ignored);
    std::filesystem::create_directories(archive_fixture / "package");
    std::ofstream(archive_fixture / "package" / "main.py") << "print('archive')";
    if (baas_installer::run_process({"tar", "-a", "-cf", archive_path.string(), "-C", archive_fixture.string(), "package"}) != 0) {
        std::cerr << "could not create ZIP extraction fixture\n";
        return 1;
    }
    std::string extraction_chunks;
    if (!baas_installer::extract_mirror_archive(
            archive_path, extracted, archive_error,
            [&](const std::string_view chunk) { extraction_chunks.append(chunk); }) ||
        !std::filesystem::is_regular_file(extracted / "package" / "main.py")) {
        std::cerr << "safe MirrorChyan ZIP extraction failed: " << archive_error << '\n';
        return 1;
    }
    std::filesystem::remove_all(archive_fixture, ignored);
    std::filesystem::remove_all(extracted, ignored);
    std::filesystem::remove(archive_path, ignored);
#endif
    return 0;
}
