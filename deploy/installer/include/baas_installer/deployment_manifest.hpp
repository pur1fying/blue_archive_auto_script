#pragma once

#include "baas_installer/paths.hpp"

#include <filesystem>
#include <set>
#include <string>

namespace baas_installer {

enum class DeploymentTree { Main, Ocr };
using DeploymentFileSet = std::set<std::filesystem::path>;

struct DeploymentManifestLoad {
    bool exists{};
    bool valid{};
    DeploymentFileSet files;
    std::string error;
};

std::filesystem::path deployment_manifest_path(const InstallPaths& paths, DeploymentTree tree);
bool deployment_relative_path_allowed(DeploymentTree tree, const std::filesystem::path& relative);
DeploymentManifestLoad load_deployment_manifest(const InstallPaths& paths, DeploymentTree tree);
void save_deployment_manifest_atomic(const InstallPaths& paths, DeploymentTree tree,
                                     const DeploymentFileSet& files);

}  // namespace baas_installer
