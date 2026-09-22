#include "baas_installer/deployment_manifest.hpp"

#include <array>
#include <chrono>
#include <fstream>
#include <stdexcept>

#include <nlohmann/json.hpp>

#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#endif

namespace fs = std::filesystem;

namespace baas_installer {
namespace {

const char* tree_name(const DeploymentTree tree) {
    return tree == DeploymentTree::Main ? "main" : "ocr";
}

bool has_parent_component(const fs::path& path) {
    for (const auto& component : path) {
        if (component == fs::path("..")) return true;
    }
    return false;
}

bool protected_first_component(const fs::path& first) {
    static const std::array<fs::path, 14> protected_paths{
        "BlueArchiveAutoScript.exe", "BAAS-Installer.exe", "setup.toml", "config", "output",
        "screenshot", "screenshots", "data", "log", "tmp", "toolkit", ".venv",
        ".baas-installer", ".git"};
    return std::find(protected_paths.begin(), protected_paths.end(), first) != protected_paths.end();
}

std::string manifest_path_to_utf8(const fs::path& path) {
#ifdef _WIN32
    const auto wide = path.generic_wstring();
    if (wide.empty()) return {};
    const auto size = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, wide.data(),
                                          static_cast<int>(wide.size()), nullptr, 0,
                                          nullptr, nullptr);
    if (size <= 0) throw std::runtime_error("deployment path could not be encoded as UTF-8");
    std::string result(static_cast<std::size_t>(size), '\0');
    WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, wide.data(),
                        static_cast<int>(wide.size()), result.data(), size,
                        nullptr, nullptr);
    return result;
#else
    return path.generic_string();
#endif
}

fs::path manifest_path_from_utf8(const std::string& value) {
#ifdef _WIN32
    if (value.empty()) return {};
    const auto size = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, value.data(),
                                          static_cast<int>(value.size()), nullptr, 0);
    if (size <= 0) throw std::runtime_error("deployment manifest path is not valid UTF-8");
    std::wstring wide(static_cast<std::size_t>(size), L'\0');
    MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, value.data(),
                        static_cast<int>(value.size()), wide.data(), size);
    return fs::path(wide);
#else
    return fs::path(value);
#endif
}

bool starts_with_path(const fs::path& path, const fs::path& prefix) {
    auto path_it = path.begin();
    for (auto prefix_it = prefix.begin(); prefix_it != prefix.end(); ++prefix_it, ++path_it) {
        if (path_it == path.end() || *path_it != *prefix_it) return false;
    }
    return true;
}

void cleanup_owned_temporary(const fs::path& temporary, const fs::path& state_dir) {
    if (temporary.parent_path() != state_dir ||
        !temporary.filename().string().starts_with("deployment-manifest-")) {
        return;
    }
    std::error_code ignored;
    fs::remove(temporary, ignored);
}

void replace_atomic(const fs::path& temporary, const fs::path& destination) {
    std::error_code error;
#ifdef _WIN32
    if (!MoveFileExW(temporary.wstring().c_str(), destination.wstring().c_str(),
                     MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
        throw std::runtime_error("deployment manifest could not be replaced: " +
                                 std::to_string(GetLastError()));
    }
#else
    fs::rename(temporary, destination, error);
    if (error) throw std::runtime_error("deployment manifest could not be replaced: " + error.message());
#endif
}

}  // namespace

fs::path deployment_manifest_path(const InstallPaths& paths, const DeploymentTree tree) {
    return paths.state_dir / (tree == DeploymentTree::Main
                                  ? "main-files-v1.json"
                                  : "ocr-files-v1.json");
}

bool deployment_relative_path_allowed(const DeploymentTree tree, const fs::path& relative) {
    if (relative.empty() || relative.is_absolute() || relative.has_root_path() ||
        has_parent_component(relative) || relative.lexically_normal() != relative) {
        return false;
    }
    const auto first = *relative.begin();
    if (protected_first_component(first)) return false;
    if (tree == DeploymentTree::Main) {
        static const fs::path ocr_bin("core/ocr/baas_ocr_client/bin");
        if (starts_with_path(relative, ocr_bin)) return false;
    }
    return true;
}

DeploymentManifestLoad load_deployment_manifest(const InstallPaths& paths,
                                                const DeploymentTree tree) {
    DeploymentManifestLoad result;
    const auto path = deployment_manifest_path(paths, tree);
    std::error_code error;
    result.exists = fs::exists(path, error);
    if (error || !result.exists || !fs::is_regular_file(path, error) || error) {
        if (error) result.error = "deployment manifest could not be inspected";
        return result;
    }
    try {
        std::ifstream input(path, std::ios::binary);
        const auto document = nlohmann::json::parse(input);
        if (document.at("schema").get<int>() != 1 ||
            document.at("tree").get<std::string>() != tree_name(tree) ||
            !document.at("files").is_array()) {
            result.error = "deployment manifest metadata is invalid";
            return result;
        }
        for (const auto& item : document.at("files")) {
            if (!item.is_string()) {
                result.files.clear();
                result.error = "deployment manifest contains a non-string path";
                return result;
            }
            const fs::path relative = manifest_path_from_utf8(item.get<std::string>());
            if (!deployment_relative_path_allowed(tree, relative) || !result.files.insert(relative).second) {
                result.files.clear();
                result.error = "deployment manifest contains an unsafe or duplicate path";
                return result;
            }
        }
        result.valid = true;
        return result;
    } catch (const std::exception& exception) {
        result.files.clear();
        result.error = std::string("deployment manifest is unreadable: ") + exception.what();
        return result;
    }
}

void save_deployment_manifest_atomic(const InstallPaths& paths, const DeploymentTree tree,
                                     const DeploymentFileSet& files) {
    nlohmann::json serialized = nlohmann::json::array();
    for (const auto& relative : files) {
        if (!deployment_relative_path_allowed(tree, relative)) {
            throw std::invalid_argument("unsafe deployment manifest path: " + manifest_path_to_utf8(relative));
        }
        serialized.push_back(manifest_path_to_utf8(relative));
    }
    std::error_code error;
    fs::create_directories(paths.state_dir, error);
    if (error) throw std::runtime_error("deployment manifest directory could not be created: " + error.message());
    const auto nonce = std::chrono::steady_clock::now().time_since_epoch().count();
    const auto temporary = paths.state_dir /
        ("deployment-manifest-" + std::string(tree_name(tree)) + "-" +
         std::to_string(nonce) + ".tmp");
    try {
        {
            std::ofstream output(temporary, std::ios::binary | std::ios::trunc);
            if (!output) throw std::runtime_error("temporary deployment manifest could not be created");
            output << nlohmann::json{{"schema", 1}, {"tree", tree_name(tree)}, {"files", serialized}}.dump(2)
                   << '\n';
            output.flush();
            if (!output) throw std::runtime_error("temporary deployment manifest could not be written");
        }
        replace_atomic(temporary, deployment_manifest_path(paths, tree));
    } catch (...) {
        cleanup_owned_temporary(temporary, paths.state_dir);
        throw;
    }
}

}  // namespace baas_installer
