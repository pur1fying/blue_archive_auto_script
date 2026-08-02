#include "baas_installer/config.hpp"

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

    const auto rendered = baas_installer::render_config(config);
    if (!require(rendered.find("[general]") != std::string::npos, "current schema")) return 1;
    if (!require(rendered.find("[General]") != std::string::npos, "legacy schema")) return 1;
    if (!require(rendered.find("keep_me = \"yes\"") != std::string::npos, "unknown field")) return 1;
    if (!require(rendered.find("legacy_extension = \"retain\"") != std::string::npos, "unknown managed-table field")) return 1;
    if (!require(rendered.find("source_list = [\n    \"https://pypi.example/simple\",\n    \"https://mirror.example/simple\",\n]") != std::string::npos,
                 "multiline unknown field")) return 1;
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
    return 0;
}
