#pragma once

#include "baas_installer/digest.hpp"

#include <filesystem>
#include <functional>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace baas_installer {

enum class CdkStatus { Valid, UpToDate, Invalid, Expired, Exhausted, Mismatched, Blocked, ServerError, Malformed };
enum class MirrorResource { Main, Ocr };
enum class MirrorPackageMode { UpToDate, Full, Incremental };

struct MirrorChanges {
    std::vector<std::filesystem::path> added;
    std::vector<std::filesystem::path> modified;
    std::vector<std::filesystem::path> deleted;
};

struct MirrorPackage {
    MirrorPackageMode mode{MirrorPackageMode::UpToDate};
    std::string version;
    std::filesystem::path content_root;
    MirrorChanges changes;
};

struct MirrorPlatform { std::string os; std::string arch; };

struct MirrorRelease {
    CdkStatus status{CdkStatus::Malformed};
    std::string message;
    std::string version;
    std::string download_url;
    std::string sha256;
    std::string update_type;
};

MirrorRelease parse_mirror_response(const std::string& json);
MirrorRelease request_mirror_release(const std::string& request_url, std::string& error, long timeout_seconds = 5);
std::string mirror_latest_url(const std::string& cdk, const std::string& current_sha, const std::string& channel = "stable");
std::string mirror_latest_url(MirrorResource resource, const std::string& os, const std::string& arch,
                              const std::string& cdk, const std::string& current_version,
                              const std::string& channel = "stable");
MirrorChanges parse_mirror_changes(const std::string& json, const std::filesystem::path& source_root,
                                   std::string& error);
MirrorPackage inspect_mirror_staging(const MirrorRelease& release, const std::filesystem::path& extracted_root,
                                     std::string& error);
MirrorPlatform current_mirror_platform();
bool validate_archive_entries(const std::vector<std::string>& entries, std::string& error);
bool extract_mirror_archive(const std::filesystem::path& archive, const std::filesystem::path& destination,
                            std::string& error, const std::function<void(std::string_view)>& on_chunk = {});
MirrorRelease wait_for_incremental_release(MirrorRelease initial,
                                           const std::function<MirrorRelease()>& refresh,
                                           const std::function<void()>& wait,
                                           int maximum_attempts = 10);
using MirrorDownloadProgress = std::function<void(std::uint64_t downloaded, std::uint64_t total)>;

// Downloads only into the supplied staging location. Production builds use
// libcurl; callers must not deploy the archive before verify_sha256 succeeds.
bool download_mirror_package(const MirrorRelease& release, const std::filesystem::path& archive, std::string& error,
                             MirrorDownloadProgress on_progress = {});

}  // namespace baas_installer
