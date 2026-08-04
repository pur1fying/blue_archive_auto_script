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
BAAS_ROOT_PATH = "legacy-root"

[custom]
keep_me = "yes"
)");

    if (!require(config.mirrorc_cdk == "legacy-cdk", "legacy cdk")) return 1;
    if (!require(config.main_sha == "legacy-main", "legacy SHA")) return 1;
    if (!require(config.uses_portable_runtime(), "portable runtime")) return 1;
    if (!require(config.pypi_sources.size() == 2 && config.pypi_sources.front() == "https://pypi.example/simple",
                 "legacy source_list parsed")) return 1;
    if (!require(config.baas_root_path == "legacy-root", "legacy BAAS root parsed")) return 1;

    const auto rendered = baas_installer::render_config(config);
    if (!require(rendered.starts_with("schema_version = 1\n"), "configuration has leading whitespace")) return 1;
    if (!require(rendered.find("[general]") == std::string::npos &&
                     rendered.find("[paths]") == std::string::npos &&
                     rendered.find("[python]") == std::string::npos &&
                     rendered.find("[repositories]") == std::string::npos,
                 "duplicate lower-case schema was rendered")) return 1;
    if (!require(rendered.find("[General]") != std::string::npos &&
                     rendered.find("[URLs]") != std::string::npos &&
                     rendered.find("[Paths]") != std::string::npos,
                 "canonical BAAS schema")) return 1;
    if (!require(rendered.find("keep_me = \"yes\"") != std::string::npos, "unknown field")) return 1;
    if (!require(rendered.find("legacy_extension = \"retain\"") != std::string::npos, "unknown managed-table field")) return 1;
    if (!require(rendered.find("source_list = [\"https://pypi.example/simple\", \"https://mirror.example/simple\"]") != std::string::npos,
                 "configured source list rendered")) return 1;
    if (!require(rendered.find("package_manager = \"uv\"") != std::string::npos, "uv manager")) return 1;
    const auto rendered_twice = baas_installer::render_config(baas_installer::parse_config(rendered));
    if (rendered_twice != rendered) {
        std::cerr << "first render:\n" << rendered << "second render:\n" << rendered_twice;
    }
    if (!require(rendered_twice == rendered, "repeated saves changed canonical formatting")) return 1;

    const auto schema_once = baas_installer::render_config(baas_installer::parse_config("schema_version = 0\n[General]\nruntime_path = \"default\"\n"));
    if (!require(schema_once.find("schema_version = 0") == std::string::npos, "old schema version removed")) return 1;

    const auto mixed = baas_installer::parse_config(R"(
[general]
current_baas_sha = "current-main"
[paths]
baas_root_path = "current-root"
[General]
current_BAAS_version = "legacy-main"
[Paths]
BAAS_ROOT_PATH = "legacy-root"
)");
    if (!require(mixed.main_sha == "current-main" && mixed.baas_root_path == "current-root",
                 ("current schema precedence: main=" + mixed.main_sha +
                  " root=" + mixed.baas_root_path).c_str())) return 1;

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
    const auto canonical_sources = baas_installer::parse_config(baas_installer::render_config(syntax));
    if (!require(canonical_sources.main_sources == syntax.main_sources &&
                     canonical_sources.ocr_sources == syntax.ocr_sources &&
                     canonical_sources.pypi_sources == syntax.pypi_sources,
                 "canonical schema changed configured source order")) return 1;

    const auto fixture = std::filesystem::temp_directory_path() / "baas-installer-config-atomic";
    std::error_code ignored;
    std::filesystem::remove_all(fixture, ignored);
    auto paths = baas_installer::InstallPaths::from_install_root(
        fixture / "BAAS", fixture / "launcher" / "BlueArchiveAutoScript.exe");
    auto saved = syntax;
    saved.baas_root_path = "..\\BAAS";
    saved.main_sha = "first";
    baas_installer::save_config_atomic(saved, paths);
    saved.main_sha = "second";
    baas_installer::save_config_atomic(saved, paths);
    const auto loaded = baas_installer::load_config(paths);
    if (!require(loaded.main_sha == "second" && loaded.baas_root_path == "..\\BAAS" &&
                     paths.setup_toml == fixture / "launcher" / "setup.toml" &&
                     !std::filesystem::exists(paths.root / "setup.toml"),
                 "configuration was not persisted beside the executable")) return 1;
    saved.mirrorc_cdk = "wrong-session-cdk";
    baas_installer::begin_install_session_config(saved, paths);
    if (!require(saved.mirrorc_cdk.empty() && baas_installer::load_config(paths).mirrorc_cdk.empty(),
                 "installation identity persisted a candidate CDK before MirrorChyan success")) return 1;
    baas_installer::commit_successful_mirror_cdk(saved, paths, "verified-session-cdk");
    if (!require(saved.mirrorc_cdk == "verified-session-cdk" &&
                     baas_installer::load_config(paths).mirrorc_cdk == "verified-session-cdk",
                 "successful MirrorChyan CDK was not persisted")) return 1;
    baas_installer::begin_install_session_config(saved, paths, "preflight-validated-cdk");
    if (!require(saved.mirrorc_cdk == "preflight-validated-cdk" &&
                     baas_installer::load_config(paths).mirrorc_cdk == "preflight-validated-cdk",
                 "a preflight-validated CDK was not persisted when installation began")) return 1;
    baas_installer::clear_mirror_cdk(saved, paths);
    if (!require(saved.mirrorc_cdk.empty() && baas_installer::load_config(paths).mirrorc_cdk.empty(),
                  "a failed MirrorChyan attempt left its CDK in setup.toml")) return 1;
    std::filesystem::remove(paths.setup_toml, ignored);
    std::filesystem::create_directories(paths.setup_toml);
    bool replacement_failed = false;
    try {
        baas_installer::save_config_atomic(saved, paths);
    } catch (const std::exception&) {
        replacement_failed = true;
    }
    bool temporary_left = false;
    for (const auto& entry : std::filesystem::directory_iterator(paths.setup_toml.parent_path())) {
        const auto name = entry.path().filename().string();
        temporary_left = temporary_left || name.starts_with("setup.toml.new-");
    }
    if (!require(replacement_failed && !temporary_left,
                 "failed atomic replacement left setup.toml.new-* behind")) return 1;

    auto pointer_paths = baas_installer::InstallPaths::from_install_root(
        fixture / "pointer-target", fixture / "pointer-launcher" / "BlueArchiveAutoScript.exe");
    std::filesystem::create_directories(pointer_paths.state_dir);
    const auto pointer = pointer_paths.state_dir / "setup-location-v1.json";
    std::ofstream(pointer) << "user-owned pointer contents";
    bool pointer_refused = false;
    try {
        baas_installer::save_setup_location_pointer_atomic(pointer_paths);
    } catch (const std::exception&) {
        pointer_refused = true;
    }
    std::ifstream pointer_input(pointer);
    const std::string pointer_contents{std::istreambuf_iterator<char>(pointer_input), {}};
    if (!require(pointer_refused && pointer_contents == "user-owned pointer contents",
                 "an unrecognized setup location pointer was overwritten")) return 1;
    std::filesystem::remove_all(fixture, ignored);
    return 0;
}
