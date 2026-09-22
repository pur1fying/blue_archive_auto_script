#include "baas_installer/config.hpp"

#include <algorithm>
#include <cctype>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <optional>
#include <sstream>
#include <stdexcept>

#include <nlohmann/json.hpp>

#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#endif

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
    if (value.empty() || (value.front() != '"' && value.front() != '\'')) return value;
    const char quote = value.front();
    std::string result;
    bool escaped = false;
    for (std::size_t index = 1; index < value.size(); ++index) {
        const char character = value[index];
        if (quote == '"' && escaped) {
            switch (character) {
                case 'b': result.push_back('\b'); break;
                case 'f': result.push_back('\f'); break;
                case 'n': result.push_back('\n'); break;
                case 'r': result.push_back('\r'); break;
                case 't': result.push_back('\t'); break;
                default: result.push_back(character); break;
            }
            escaped = false;
            continue;
        }
        if (quote == '"' && character == '\\') { escaped = true; continue; }
        if (character == quote) return result;
        result.push_back(character);
    }
    return trim(std::move(value));
}

std::vector<std::string> string_array(const std::string& value) {
    std::vector<std::string> result;
    for (std::size_t index = 0; index < value.size();) {
        if (value[index] == '#') {
            const auto newline = value.find('\n', index);
            if (newline == std::string::npos) break;
            index = newline + 1;
            continue;
        }
        if (value[index] != '"' && value[index] != '\'') { ++index; continue; }
        const char quote = value[index++];
        std::string item;
        bool escaped = false;
        while (index < value.size()) {
            const char character = value[index++];
            if (quote == '"' && escaped) {
                switch (character) {
                    case 'b': item.push_back('\b'); break;
                    case 'f': item.push_back('\f'); break;
                    case 'n': item.push_back('\n'); break;
                    case 'r': item.push_back('\r'); break;
                    case 't': item.push_back('\t'); break;
                    default: item.push_back(character); break;
                }
                escaped = false;
            } else if (quote == '"' && character == '\\') {
                escaped = true;
            } else if (character == quote) {
                result.push_back(std::move(item));
                break;
            } else {
                item.push_back(character);
            }
        }
    }
    return result;
}

void append_unique(std::vector<std::string>& target, const std::vector<std::string>& values) {
    for (const auto& value : values) {
        if (!value.empty() && std::find(target.begin(), target.end(), value) == target.end()) target.push_back(value);
    }
}

std::string toml_quote(const std::string& value) {
    std::string result{"\""};
    for (const char character : value) {
        if (character == '\\' || character == '"') {
            result.push_back('\\');
            result.push_back(character);
        } else if (character == '\n') result += "\\n";
        else if (character == '\r') result += "\\r";
        else if (character == '\t') result += "\\t";
        else result.push_back(character);
    }
    result.push_back('"');
    return result;
}

std::string render_array(const std::vector<std::string>& values) {
    std::ostringstream output;
    output << "[";
    for (std::size_t index = 0; index < values.size(); ++index) {
        if (index != 0) output << ", ";
        output << toml_quote(values[index]);
    }
    output << "]";
    return output.str();
}

bool is_managed_table(const std::string& table) {
    return table == "General" || table == "URLs" || table == "Paths" || table == "general" ||
           table == "paths" || table == "python" || table == "repositories";
}

bool is_known_key(const std::string& table, const std::string& key) {
    if (table == "General") return key == "mirrorc_cdk" || key == "current_BAAS_version" || key == "current_BAAS_Cpp_version" || key == "runtime_path" || key == "python_version" || key == "channel" || key == "git_backend" || key == "package_manager" || key == "source_list";
    if (table == "general") return key == "mirrorc_cdk" || key == "current_baas_sha" || key == "current_baas_cpp_sha" || key == "channel" || key == "git_backend";
    if (table == "python") return key == "runtime_path" || key == "python_version";
    if (table == "paths") return key == "baas_root_path" || key == "tmp_path" || key == "toolkit_path";
    if (table == "Paths") return key == "BAAS_ROOT_PATH" || key == "TMP_PATH" || key == "TOOL_KIT_PATH";
    if (table == "repositories") return key == "main_sources" || key == "cpp_sources";
    if (table == "URLs") return key == "REPO_URL_HTTP" || key == "REPO_URL_FALLBACKS" || key == "OCR_REPO_SOURCES";
    return false;
}

std::optional<std::string> assignment_key(const std::string& stripped) {
    if (stripped.empty() || stripped.front() == '#') return std::nullopt;
    std::size_t end = 0;
    if (stripped.front() == '"' || stripped.front() == '\'') {
        const char quote = stripped.front();
        end = stripped.find(quote, 1);
        if (end == std::string::npos) return std::nullopt;
        ++end;
    } else {
        while (end < stripped.size()) {
            const auto character = static_cast<unsigned char>(stripped[end]);
            if (!std::isalnum(character) && character != '_' && character != '-') break;
            ++end;
        }
        if (end == 0) return std::nullopt;
    }
    auto equals = end;
    while (equals < stripped.size() && std::isspace(static_cast<unsigned char>(stripped[equals]))) ++equals;
    if (equals >= stripped.size() || stripped[equals] != '=') return std::nullopt;
    return unquote(stripped.substr(0, end));
}

std::string preserved_unknown(const InstallerConfig& config, const std::string& wanted_table) {
    std::ostringstream output;
    std::istringstream input(config.source_toml);
    std::string line, table;
    bool preserving = false;
    while (std::getline(input, line)) {
        const auto stripped = trim(line);
        if (stripped.size() > 2 && stripped.front() == '[' && stripped.back() == ']') {
            table = stripped.substr(1, stripped.size() - 2);
            preserving = false;
            continue;
        }
        if (table != wanted_table) continue;
        if (const auto key = assignment_key(stripped)) preserving = !is_known_key(table, *key);
        if (preserving && !stripped.empty()) output << line << '\n';
    }
    return output.str();
}

std::string preserved_unmanaged(const InstallerConfig& config) {
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
        if (!keep) continue;
        const auto equal = stripped.find('=');
        if (table.empty() && equal != std::string::npos &&
            trim(stripped.substr(0, equal)) == "schema_version") continue;
        if (!stripped.empty()) output << line << '\n';
    }
    return output.str();
}

void set_value(InstallerConfig& config, const std::string& table, const std::string& key, const std::string& value) {
    const auto assign = [](std::string& target, const std::string& source) { target = unquote(source); };
    if ((table == "general" || table == "General") && key == "mirrorc_cdk") assign(config.mirrorc_cdk, value);
    if ((table == "paths" && key == "baas_root_path") ||
        (table == "Paths" && key == "BAAS_ROOT_PATH")) assign(config.baas_root_path, value);
    if ((table == "general" && key == "current_baas_sha") || (table == "General" && key == "current_BAAS_version")) assign(config.main_sha, value);
    if ((table == "general" && key == "current_baas_cpp_sha") || (table == "General" && key == "current_BAAS_Cpp_version")) assign(config.ocr_sha, value);
    if ((table == "python" && key == "runtime_path") || (table == "General" && key == "runtime_path")) assign(config.runtime_path, value);
    if ((table == "python" || table == "General") && key == "python_version") assign(config.python_version, value);
    if ((table == "general" || table == "General") && key == "channel") assign(config.channel, value);
    if ((table == "general" || table == "General") && key == "git_backend") assign(config.git_backend, value);
    if (table == "General" && key == "source_list") config.pypi_sources = string_array(value);
    if (table == "repositories" && key == "main_sources") {
        auto parsed = string_array(value);
        append_unique(parsed, config.main_sources);
        config.main_sources = std::move(parsed);
    }
    if (table == "repositories" && key == "cpp_sources") {
        auto parsed = string_array(value);
        append_unique(parsed, config.ocr_sources);
        config.ocr_sources = std::move(parsed);
    }
    if (table == "URLs" && key == "REPO_URL_HTTP") append_unique(config.main_sources, {unquote(value)});
    if (table == "URLs" && key == "REPO_URL_FALLBACKS") append_unique(config.main_sources, string_array(value));
    if (table == "URLs" && key == "OCR_REPO_SOURCES") append_unique(config.ocr_sources, string_array(value));
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
    // Legacy data is read first irrespective of its textual position.  The new
    // lower-case schema is authoritative when both representations are present.
    const auto read_tables = [&](bool legacy_only) {
        std::istringstream input(content);
        std::string line, table;
        while (std::getline(input, line)) {
            const auto stripped = trim(line);
            if (stripped.size() > 2 && stripped.front() == '[' && stripped.back() == ']') {
                table = stripped.substr(1, stripped.size() - 2);
                continue;
            }
            const bool legacy = table == "General" || table == "Paths" || table == "URLs";
            if (legacy != legacy_only) continue;
            const auto equal = stripped.find('=');
            if (equal != std::string::npos) {
                auto value = stripped.substr(equal + 1);
                if (trim(value).starts_with('[')) {
                    const auto closed = [&] {
                        bool in_string = false;
                        char quote = 0;
                        for (const char character : value) {
                            if (!in_string && (character == '"' || character == '\'')) { in_string = true; quote = character; }
                            else if (in_string && character == quote) in_string = false;
                            else if (!in_string && character == ']') return true;
                        }
                        return false;
                    };
                    while (!closed() && std::getline(input, line)) value += "\n" + line;
                }
                set_value(config, table, trim(stripped.substr(0, equal)), value);
            }
        }
    };
    read_tables(true);
    read_tables(false);
    return config;
}

std::string render_config(const InstallerConfig& config) {
    const auto primary_main = config.main_sources.empty()
        ? std::string{"https://github.com/pur1fying/blue_archive_auto_script.git"}
        : config.main_sources.front();
    std::vector<std::string> main_fallbacks;
    if (config.main_sources.size() > 1) {
        main_fallbacks.assign(config.main_sources.begin() + 1, config.main_sources.end());
    }

    std::ostringstream output;
    output << "schema_version = 1\n\n"
           << "[General]\nmirrorc_cdk = " << toml_quote(config.mirrorc_cdk) << "\n"
           << "current_BAAS_version = " << toml_quote(config.main_sha) << "\n"
           << "current_BAAS_Cpp_version = " << toml_quote(config.ocr_sha) << "\n"
           << "channel = " << toml_quote(config.channel) << "\ngit_backend = " << toml_quote(config.git_backend) << "\n"
           << "runtime_path = " << toml_quote(config.runtime_path) << "\n"
           << "python_version = " << toml_quote(config.python_version) << "\n"
           << "source_list = " << render_array(config.pypi_sources) << "\npackage_manager = \"uv\"\n"
           << preserved_unknown(config, "General")
           << preserved_unknown(config, "general")
           << preserved_unknown(config, "python")
           << "\n[URLs]\nREPO_URL_HTTP = " << toml_quote(primary_main) << "\n"
           << "REPO_URL_FALLBACKS = " << render_array(main_fallbacks) << "\n"
           << "OCR_REPO_SOURCES = " << render_array(config.ocr_sources) << "\n"
           << preserved_unknown(config, "URLs")
           << preserved_unknown(config, "repositories")
           << "\n[Paths]\nBAAS_ROOT_PATH = " << toml_quote(config.baas_root_path)
           << "\nTMP_PATH = \"tmp\"\nTOOL_KIT_PATH = \"toolkit\"\n"
           << preserved_unknown(config, "Paths")
           << preserved_unknown(config, "paths");
    const auto unmanaged = preserved_unmanaged(config);
    if (!unmanaged.empty()) output << '\n' << unmanaged;
    return output.str();
}

InstallerConfig load_config(const InstallPaths& paths) {
    if (!fs::exists(paths.setup_toml)) return {};
    std::ifstream input(paths.setup_toml, std::ios::binary);
    return parse_config({std::istreambuf_iterator<char>(input), {}});
}

void save_config_atomic(const InstallerConfig& config, const InstallPaths& paths) {
    fs::create_directories(paths.setup_toml.parent_path());
    const auto nonce = std::chrono::steady_clock::now().time_since_epoch().count();
    const auto next = paths.setup_toml.parent_path() /
                      (paths.setup_toml.filename().string() + ".new-" + std::to_string(nonce));
    try {
        {
            std::ofstream output(next, std::ios::binary | std::ios::trunc);
            if (!output) throw std::runtime_error("failed to create setup.toml.new");
            output << render_config(config);
            output.flush();
            if (!output) throw std::runtime_error("failed to write setup.toml.new");
            output.close();
            if (!output) throw std::runtime_error("failed to close setup.toml.new");
        }
#ifdef _WIN32
        if (!MoveFileExW(next.wstring().c_str(), paths.setup_toml.wstring().c_str(),
                         MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
            throw std::runtime_error("failed to replace setup.toml");
        }
#else
        std::error_code error;
        fs::rename(next, paths.setup_toml, error);
        if (error) throw std::runtime_error("failed to replace setup.toml");
#endif
    } catch (...) {
        std::error_code cleanup_error;
        fs::remove(next, cleanup_error);
        throw;
    }
}

void save_setup_location_pointer_atomic(const InstallPaths& paths) {
    const auto destination = paths.state_dir / "setup-location-v1.json";
    if (fs::exists(destination)) {
        try {
            if (!fs::is_regular_file(destination)) throw std::runtime_error("not a regular file");
            std::ifstream input(destination, std::ios::binary);
            const auto existing = nlohmann::json::parse(input);
            if (existing.at("schema_version").get<int>() != 1 ||
                existing.at("managed_by").get<std::string>() != "baas-installer") {
                throw std::runtime_error("not installer managed");
            }
        } catch (const std::exception&) {
            throw std::runtime_error("refusing to overwrite an unrecognized setup location pointer");
        }
    }

    const auto stored_path = fs::absolute(paths.setup_toml).lexically_normal();
    auto portable_path = path_to_utf8(stored_path);
    std::replace(portable_path.begin(), portable_path.end(), '\\', '/');
    const nlohmann::json document{
        {"schema_version", 1},
        {"managed_by", "baas-installer"},
        {"base", "absolute"},
        {"path", portable_path},
    };

    fs::create_directories(destination.parent_path());
    const auto nonce = std::chrono::steady_clock::now().time_since_epoch().count();
    const auto temporary = destination.parent_path() /
        (destination.filename().string() + ".new-" + std::to_string(nonce));
    try {
        {
            std::ofstream output(temporary, std::ios::binary | std::ios::trunc);
            if (!output) throw std::runtime_error("failed to create setup location pointer");
            output << document.dump() << '\n';
            output.flush();
            if (!output) throw std::runtime_error("failed to write setup location pointer");
        }
#ifdef _WIN32
        if (!MoveFileExW(temporary.wstring().c_str(), destination.wstring().c_str(),
                         MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
            throw std::runtime_error("failed to replace setup location pointer");
        }
#else
        std::error_code error;
        fs::rename(temporary, destination, error);
        if (error) throw std::runtime_error("failed to replace setup location pointer");
#endif
    } catch (...) {
        std::error_code cleanup_error;
        fs::remove(temporary, cleanup_error);
        throw;
    }
}

void begin_install_session_config(InstallerConfig& config, const InstallPaths& paths,
                                  const std::string& validated_cdk) {
    config.mirrorc_cdk = validated_cdk;
    save_config_atomic(config, paths);
}

void clear_mirror_cdk(InstallerConfig& config, const InstallPaths& paths) {
    config.mirrorc_cdk.clear();
    save_config_atomic(config, paths);
}

void commit_successful_mirror_cdk(InstallerConfig& config, const InstallPaths& paths,
                                  const std::string& verified_cdk) {
    config.mirrorc_cdk = verified_cdk;
    save_config_atomic(config, paths);
}

}  // namespace baas_installer
