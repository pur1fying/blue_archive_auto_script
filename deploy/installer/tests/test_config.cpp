#include "baas_installer/config.hpp"
#include "baas_installer/paths.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>

namespace {
bool require(bool value, const char* message) {
    if (!value) std::cerr << message << '\n';
    return value;
}
}

int main() {
    const auto config = baas_installer::parse_config(R"(
[General]
mirrorc_cdk = "legacy-cdk"
current_BAAS_version = "legacy-main"
runtime_path = "default"
legacy_extension = "retain"
source_list = [
    "https://pypi.example/simple",
    "https://mirror.example/simple",
]

[Paths]
BAAS_ROOT_PATH = ""

[custom]
keep_me = "yes"
)");

    if (!require(config.mirrorc_cdk == "legacy-cdk", "legacy cdk")) return 1;
    if (!require(config.main_sha == "legacy-main", "legacy SHA")) return 1;
    if (!require(config.uses_portable_runtime(), "portable runtime")) return 1;
    if (!require(config.pypi_sources.size() == 2 && config.pypi_sources.front() == "https://pypi.example/simple",
                 "legacy source_list parsed")) return 1;

    const auto rendered = baas_installer::render_config(config);
    if (!require(rendered.find("[general]") != std::string::npos, "current schema")) return 1;
    if (!require(rendered.find("[General]") != std::string::npos, "legacy schema")) return 1;
    if (!require(rendered.find("keep_me = \"yes\"") != std::string::npos, "unknown field")) return 1;
    if (!require(rendered.find("legacy_extension = \"retain\"") != std::string::npos, "unknown managed-table field")) return 1;
    if (!require(rendered.find("source_list = [\"https://pypi.example/simple\", \"https://mirror.example/simple\"]") != std::string::npos,
                 "configured source list rendered")) return 1;
    if (!require(rendered.find("package_manager = \"uv\"") != std::string::npos, "uv manager")) return 1;

    const auto schema_once = baas_installer::render_config(baas_installer::parse_config("schema_version = 0\n[General]\nruntime_path = \"default\"\n"));
    if (!require(schema_once.find("schema_version = 0") == std::string::npos, "old schema version removed")) return 1;

    const auto mixed = baas_installer::parse_config(R"(
[general]
current_baas_sha = "current-main"
[General]
current_BAAS_version = "legacy-main"
)");
    if (!require(mixed.main_sha == "current-main", "current schema precedence")) return 1;

    const auto syntax = baas_installer::parse_config(R"(
[General]
runtime_path = 'default' # portable runtime
[URLs]
REPO_URL_HTTP = 'https://private.example/main.git' # preferred Git source
[repositories]
main_sources = ["https://current.example/main.git"] # "ignored-comment-value"
cpp_sources = ['https://current.example/ocr.git']
)");
    if (!require(syntax.uses_portable_runtime(), "literal TOML string/comment parsing")) return 1;
    if (!require(syntax.main_sources.size() == 2 && syntax.main_sources[0] == "https://current.example/main.git" &&
                 syntax.main_sources[1] == "https://private.example/main.git", "configured main sources")) return 1;
    if (!require(syntax.ocr_sources.size() == 1 && syntax.ocr_sources[0] == "https://current.example/ocr.git",
                 "configured OCR sources")) return 1;

    const auto fixture = std::filesystem::temp_directory_path() / "baas-installer-config-atomic";
    std::error_code ignored;
    std::filesystem::remove_all(fixture, ignored);
    auto paths = baas_installer::InstallPaths::from_executable(fixture / "BlueArchiveAutoScript.exe");
    auto saved = syntax;
    saved.main_sha = "first";
    baas_installer::save_config_atomic(saved, paths);
    saved.main_sha = "second";
    baas_installer::save_config_atomic(saved, paths);
    const auto loaded = baas_installer::load_config(paths);
    if (!require(loaded.main_sha == "second" && std::filesystem::exists(paths.setup_toml.string() + ".bak"),
                 "repeated atomic save with existing backup")) return 1;
    std::filesystem::remove_all(fixture, ignored);
    return 0;
}
