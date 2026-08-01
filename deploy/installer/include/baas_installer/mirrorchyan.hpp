#pragma once

#include <filesystem>
#include <string>

namespace baas_installer {

enum class CdkStatus { Valid, Invalid, Expired, Exhausted, Mismatched, Blocked, ServerError, Malformed };

struct MirrorRelease {
    CdkStatus status{CdkStatus::Malformed};
    std::string message;
    std::string version;
    std::string download_url;
    std::string sha256;
    std::string update_type;
};

MirrorRelease parse_mirror_response(const std::string& json);
std::string mirror_latest_url(const std::string& cdk, const std::string& current_sha, const std::string& channel = "stable");
bool is_sha256(const std::string& digest);
bool verify_sha256(const std::filesystem::path& file, const std::string& expected_digest);

// Downloads only into the supplied staging location. Production builds use
// libcurl; callers must not deploy the archive before verify_sha256 succeeds.
bool download_mirror_package(const MirrorRelease& release, const std::filesystem::path& archive, std::string& error);

}  // namespace baas_installer
