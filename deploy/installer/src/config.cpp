#include "baas_installer/config.hpp"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <stdexcept>

namespace fs = std::filesystem;

namespace baas_installer {
namespace {

std::string trim(std::string value) {
    const auto not_space = [](unsigned char ch) { return !std::isspace(ch); };
    value.erase(value.begin(), std::find_if(value.begin(), value.end(), not_space));
    value.erase(std::find_if(value.rbegin(), value.rend(), not_space).base(), value.end());
    return value;
}

std::string unquote(std::string value) {
    value = trim(std::move(value));
    if (value.size() >= 2 && value.front() == '"' && value.back() == '"') {
        return value.substr(1, value.size() - 2);
    }
    return value;
}

bool is_managed_table(const std::string& table) {
    return table == "General" || table == "URLs" || table == "Paths" || table == "general" ||
           table == "paths" || table == "python" || table == "repositories";
}

void set_value(InstallerConfig& config, const std::string& table, const std::string& key, const std::string& value) {
    const bool legacy = table == "General";
    const auto assign = [legacy](std::string& target, const std::string& source) {
        if (!legacy || target.empty()) target = unquote(source);
    };
    if ((table == "general" || table == "General") && key == "mirrorc_cdk") assign(config.mirrorc_cdk, value);
    if ((table == "general" && key == "current_baas_sha") || (table == "General" && key == "current_BAAS_version")) assign(config.main_sha, value);
    if ((table == "general" && key == "current_baas_cpp_sha") || (table == "General" && key == "current_BAAS_Cpp_version")) assign(config.ocr_sha, value);
    if ((table == "python" && key == "runtime_path") || (table == "General" && key == "runtime_path")) assign(config.runtime_path, value);
    if (table == "python" && key == "python_version") assign(config.python_version, value);
    if ((table == "general" || table == "General") && key == "channel") assign(config.channel, value);
    if ((table == "general" || table == "General") && key == "git_backend") assign(config.git_backend, value);
}

}  // namespace

bool InstallerConfig::uses_portable_runtime() const {
    auto value = runtime_path;
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char c) { return std::tolower(c); });
    return value == "default";
}

InstallerConfig parse_config(const std::string& content) {
    InstallerConfig config;
    config.source_toml = content;
    std::istringstream input(content);
    std::string line, table;
    while (std::getline(input, line)) {
        const auto stripped = trim(line);
        if (stripped.size() > 2 && stripped.front() == '[' && stripped.back() == ']') {
            table = stripped.substr(1, stripped.size() - 2);
            continue;
        }
        const auto equal = stripped.find('=');
        if (equal != std::string::npos) set_value(config, table, trim(stripped.substr(0, equal)), stripped.substr(equal + 1));
    }
    return config;
}

std::string render_config(const InstallerConfig& config) {
    std::ostringstream output;
    std::istringstream input(config.source_toml);
    std::string line, table;
    bool keep = true;
    while (std::getline(input, line)) {
        const auto stripped = trim(line);
        if (stripped.size() > 2 && stripped.front() == '[' && stripped.back() == ']') {
            table = stripped.substr(1, stripped.size() - 2);
            keep = !is_managed_table(table);
        }
        if (keep) output << line << '\n';
    }
    output << "schema_version = 1\n\n[general]\n"
           << "mirrorc_cdk = \"" << config.mirrorc_cdk << "\"\n"
           << "channel = \"" << config.channel << "\"\n"
           << "current_baas_sha = \"" << config.main_sha << "\"\n"
           << "current_baas_cpp_sha = \"" << config.ocr_sha << "\"\n"
           << "git_backend = \"" << config.git_backend << "\"\n\n"
           << "[paths]\nbaas_root_path = \".\"\ntmp_path = \"tmp\"\ntoolkit_path = \"toolkit\"\n\n"
           << "[python]\nruntime_path = \"" << config.runtime_path << "\"\npython_version = \"" << config.python_version << "\"\n\n"
           << "[repositories]\nmain_sources = []\ncpp_sources = []\n\n"
           << "[General]\nmirrorc_cdk = \"" << config.mirrorc_cdk << "\"\n"
           << "current_BAAS_version = \"" << config.main_sha << "\"\n"
           << "current_BAAS_Cpp_version = \"" << config.ocr_sha << "\"\n"
           << "channel = \"" << config.channel << "\"\ngit_backend = \"" << config.git_backend << "\"\n"
           << "runtime_path = \"" << config.runtime_path << "\"\npackage_manager = \"uv\"\n\n"
           << "[URLs]\nREPO_URL_HTTP = \"https://github.com/pur1fying/blue_archive_auto_script.git\"\n\n"
           << "[Paths]\nBAAS_ROOT_PATH = \".\"\nTMP_PATH = \"tmp\"\nTOOL_KIT_PATH = \"toolkit\"\n";
    return output.str();
}

InstallerConfig load_config(const InstallPaths& paths) {
    if (!fs::exists(paths.setup_toml)) return {};
    std::ifstream input(paths.setup_toml, std::ios::binary);
    return parse_config({std::istreambuf_iterator<char>(input), {}});
}

void save_config_atomic(const InstallerConfig& config, const InstallPaths& paths) {
    fs::create_directories(paths.root);
    const auto next = paths.setup_toml.string() + ".new";
    const auto backup = paths.setup_toml.string() + ".bak";
    { std::ofstream output(next, std::ios::binary | std::ios::trunc); output << render_config(config); output.flush(); }
    std::error_code error;
    if (fs::exists(paths.setup_toml)) fs::rename(paths.setup_toml, backup, error);
    fs::rename(next, paths.setup_toml, error);
    if (error) { if (fs::exists(backup)) fs::rename(backup, paths.setup_toml, error); throw std::runtime_error("failed to replace setup.toml"); }
}

}  // namespace baas_installer
