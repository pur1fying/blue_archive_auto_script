#pragma once

#include <filesystem>
#include <string>

namespace baas_installer {

struct TargetValidation {
    bool accepted{};
    bool existing_installation{};
    std::filesystem::path root;
    std::string error;
};

std::filesystem::path default_install_root(const std::filesystem::path& source_executable);
std::filesystem::path resolve_install_root(const std::filesystem::path& source_executable,
                                           const std::filesystem::path& configured_root);
bool is_recognized_installation(const std::filesystem::path& root);
TargetValidation validate_install_target(const std::filesystem::path& source_executable,
                                         const std::filesystem::path& requested_root);

}  // namespace baas_installer
