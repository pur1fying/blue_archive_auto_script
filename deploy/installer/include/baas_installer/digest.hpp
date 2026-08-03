#pragma once

#include <filesystem>
#include <string>
#include <string_view>

namespace baas_installer {

bool is_sha256(std::string_view digest);
std::string sha256_bytes(std::string_view bytes);
std::string sha256_file(const std::filesystem::path& file);
bool verify_sha256(const std::filesystem::path& file, std::string_view expected_digest);

}  // namespace baas_installer
