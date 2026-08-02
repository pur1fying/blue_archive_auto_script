#pragma once

#include "baas_installer/paths.hpp"

#include <string>
#include <vector>

namespace baas_installer {

struct InstallerConfig {
    std::string mirrorc_cdk;
    std::string main_sha;
    std::string ocr_sha;
    std::string runtime_path{"default"};
    std::string python_version{"3.9.0"};
    std::string channel{"stable"};
    std::string git_backend{"auto"};
    std::vector<std::string> main_sources;
    std::vector<std::string> ocr_sources;
    std::vector<std::string> pypi_sources;
    std::string source_toml;

    bool uses_portable_runtime() const;
};

InstallerConfig parse_config(const std::string& content);
std::string render_config(const InstallerConfig& config);
InstallerConfig load_config(const InstallPaths& paths);
void save_config_atomic(const InstallerConfig& config, const InstallPaths& paths);

}  // namespace baas_installer
