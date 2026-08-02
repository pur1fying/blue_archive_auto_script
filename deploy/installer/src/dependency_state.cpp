#include "baas_installer/dependency_state.hpp"

#include "baas_installer/digest.hpp"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <sstream>
#include <stdexcept>

namespace fs = std::filesystem;

namespace baas_installer {
namespace {

std::string read_file(const fs::path& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) return {};
    return {std::istreambuf_iterator<char>(input), {}};
}

void append_field(std::string& output, const std::string_view name, const std::string_view value) {
    output.append(name).push_back(':');
    output.append(std::to_string(value.size())).push_back(':');
    output.append(value).push_back('\n');
}

std::string platform_name() {
#ifdef _WIN32
    return "windows-x64";
#elif defined(__APPLE__) && (defined(__aarch64__) || defined(__arm64__))
    return "macos-arm64";
#elif defined(__APPLE__)
    return "macos-x64";
#else
    return "linux-x64";
#endif
}

fs::path virtualenv_python(const InstallPaths& paths) {
#ifdef _WIN32
    return paths.venv_dir / "Scripts" / "python.exe";
#else
    return paths.venv_dir / "bin" / "python";
#endif
}

std::string runtime_name(const InstallerConfig& config) {
    return config.uses_portable_runtime() ? "portable" : "custom";
}

std::string field(const std::string& content, const std::string& name) {
    std::istringstream input(content);
    std::string line;
    const auto prefix = name + "=";
    while (std::getline(input, line)) {
        if (line.starts_with(prefix)) return line.substr(prefix.size());
    }
    return {};
}

DependencyStamp load_dependency_stamp(const InstallPaths& paths) {
    const auto content = read_file(dependency_stamp_path(paths));
    DependencyStamp result;
    try {
        const auto schema = field(content, "schema");
        result.schema = schema.empty() ? 0 : std::stoi(schema);
    } catch (...) {
        result.schema = 0;
    }
    result.input_sha256 = field(content, "input_sha256");
    result.lock_sha256 = field(content, "lock_sha256");
    result.python_version = field(content, "python");
    result.runtime = field(content, "runtime");
    return result;
}

void replace_file_atomic(const fs::path& path, const std::string& content) {
    fs::create_directories(path.parent_path());
    const fs::path next = path.string() + ".new";
    const fs::path backup = path.string() + ".bak";
    {
        std::ofstream output(next, std::ios::binary | std::ios::trunc);
        if (!output) throw std::runtime_error("failed to create atomic dependency state");
        output << content;
        output.flush();
        if (!output) throw std::runtime_error("failed to write atomic dependency state");
    }
    std::error_code error;
    fs::remove(backup, error);
    error.clear();
    if (fs::exists(path)) {
        fs::rename(path, backup, error);
        if (error) {
            fs::remove(next, error);
            throw std::runtime_error("failed to rotate dependency state");
        }
    }
    error.clear();
    fs::rename(next, path, error);
    if (error) {
        std::error_code ignored;
        if (fs::exists(backup)) fs::rename(backup, path, ignored);
        fs::remove(next, ignored);
        throw std::runtime_error("failed to replace dependency state");
    }
}

bool has_managed_python(const InstallPaths& paths) {
    std::error_code error;
    if (!fs::is_directory(paths.toolkit_dir / "uv" / "cpython", error)) return false;
    for (fs::recursive_directory_iterator item(paths.toolkit_dir / "uv" / "cpython", error), end;
         !error && item != end; item.increment(error)) {
        if (!item->is_regular_file(error)) continue;
        auto name = item->path().filename().string();
        std::transform(name.begin(), name.end(), name.begin(), [](const unsigned char character) {
            return static_cast<char>(std::tolower(character));
        });
#ifdef _WIN32
        if (name == "python.exe") return true;
#else
        if (name == "python" || name == "python3") return true;
#endif
    }
    return false;
}

bool marker_matches(const InstallPaths& paths, const InstallerConfig& config) {
    return read_file(paths.venv_dir / ".baas-installer-managed") ==
           "python=" + config.python_version + "\n";
}

std::string trim(std::string value) {
    const auto first = value.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) return {};
    const auto last = value.find_last_not_of(" \t\r\n");
    return value.substr(first, last - first + 1);
}

bool repair_managed_value(std::string& value, const fs::path& current_python_root) {
    std::string normalized = value;
    std::replace(normalized.begin(), normalized.end(), '\\', '/');
    std::transform(normalized.begin(), normalized.end(), normalized.begin(), [](const unsigned char character) {
        return static_cast<char>(std::tolower(character));
    });
    constexpr std::string_view marker = "toolkit/uv/cpython/";
    bool changed = false;
    std::size_t search = 0;
    auto found = normalized.find(marker, search);
    while (found != std::string::npos) {
        std::size_t start = found;
        while (start != 0) {
            const char previous = value[start - 1];
            if (std::isspace(static_cast<unsigned char>(previous)) || previous == '\'' || previous == '"' ||
                previous == '=') break;
            --start;
        }
        const auto end = found + marker.size();
        auto replacement = current_python_root.string();
        if (!replacement.empty() && replacement.back() != fs::path::preferred_separator) {
            replacement.push_back(fs::path::preferred_separator);
        }
        value.replace(start, end - start, replacement);
        normalized = value;
        std::replace(normalized.begin(), normalized.end(), '\\', '/');
        std::transform(normalized.begin(), normalized.end(), normalized.begin(), [](const unsigned char character) {
            return static_cast<char>(std::tolower(character));
        });
        search = start + replacement.size();
        changed = true;
        found = normalized.find(marker, search);
    }
    return changed;
}

}  // namespace

fs::path dependency_stamp_path(const InstallPaths& paths) {
    return paths.state_dir / "dependencies-v1.sha256";
}

DependencyStamp make_dependency_stamp(const InstallPaths&, const InstallerConfig& config,
                                      const fs::path& requirements, const fs::path& compiled_lock) {
    DependencyStamp result;
    result.python_version = config.python_version;
    result.runtime = runtime_name(config);
    std::string canonical;
    append_field(canonical, "schema", "1");
    append_field(canonical, "platform", platform_name());
    append_field(canonical, "requirements", read_file(requirements));
    append_field(canonical, "python", config.python_version);
    append_field(canonical, "runtime", result.runtime);
    if (!config.uses_portable_runtime()) append_field(canonical, "interpreter", config.runtime_path);
    result.input_sha256 = sha256_bytes(canonical);
    result.lock_sha256 = sha256_file(compiled_lock);
    return result;
}

DependencyState inspect_dependency_state(const InstallPaths& paths, const InstallerConfig& config,
                                         const fs::path& requirements, const fs::path& compiled_lock) {
    DependencyState result;
    if (!fs::is_regular_file(requirements)) {
        result.reason = "requirements missing";
        return result;
    }
    if (!fs::is_regular_file(compiled_lock)) {
        result.reason = "compiled lock missing";
        return result;
    }
    result.current = make_dependency_stamp(paths, config, requirements, compiled_lock);
    const auto saved = load_dependency_stamp(paths);
    if (saved.schema != 1 || saved.input_sha256 != result.current.input_sha256 ||
        saved.lock_sha256 != result.current.lock_sha256 || saved.python_version != config.python_version ||
        saved.runtime != result.current.runtime) {
        result.reason = "dependency stamp changed";
        return result;
    }
    if (config.uses_portable_runtime()) {
        if (!marker_matches(paths, config) || !fs::is_regular_file(paths.venv_dir / "pyvenv.cfg") ||
            !fs::is_regular_file(virtualenv_python(paths)) || !has_managed_python(paths)) {
            result.reason = "managed environment incomplete";
            return result;
        }
    } else if (!fs::is_regular_file(config.runtime_path)) {
        result.reason = "custom interpreter missing";
        return result;
    }
    result.cache_hit = true;
    result.reason = "dependency stamp unchanged";
    return result;
}

void save_dependency_stamp_atomic(const DependencyStamp& stamp, const InstallPaths& paths) {
    if (stamp.schema != 1 || !is_sha256(stamp.input_sha256) || !is_sha256(stamp.lock_sha256)) {
        throw std::runtime_error("cannot persist invalid dependency stamp");
    }
    std::ostringstream output;
    output << "schema=1\n"
           << "input_sha256=" << stamp.input_sha256 << '\n'
           << "lock_sha256=" << stamp.lock_sha256 << '\n'
           << "python=" << stamp.python_version << '\n'
           << "runtime=" << stamp.runtime << '\n';
    replace_file_atomic(dependency_stamp_path(paths), output.str());
}

bool repair_managed_venv_after_move(const InstallPaths& paths, const InstallerConfig& config,
                                    std::string& error) {
    if (!config.uses_portable_runtime() || !marker_matches(paths, config)) return true;
    const auto config_path = paths.venv_dir / "pyvenv.cfg";
    if (!fs::is_regular_file(config_path)) return true;
    std::istringstream input(read_file(config_path));
    std::ostringstream output;
    std::string line;
    bool changed = false;
    while (std::getline(input, line)) {
        const auto equal = line.find('=');
        if (equal != std::string::npos) {
            auto key = trim(line.substr(0, equal));
            std::transform(key.begin(), key.end(), key.begin(), [](const unsigned char character) {
                return static_cast<char>(std::tolower(character));
            });
            if (key == "home" || key == "executable" || key == "command") {
                auto value = line.substr(equal + 1);
                if (repair_managed_value(value, paths.toolkit_dir / "uv" / "cpython")) {
                    line = line.substr(0, equal + 1) + value;
                    changed = true;
                }
            }
        }
        output << line << '\n';
    }
    try {
        if (changed) replace_file_atomic(config_path, output.str());
#ifndef _WIN32
        const auto binary_dir = paths.venv_dir / "bin";
        if (fs::is_directory(binary_dir)) {
            for (const auto& item : fs::directory_iterator(binary_dir)) {
                if (!item.is_symlink()) continue;
                auto target = fs::read_symlink(item.path());
                auto value = target.string();
                if (!repair_managed_value(value, paths.toolkit_dir / "uv" / "cpython")) continue;
                const auto replacement = item.path().parent_path() / (item.path().filename().string() + ".new");
                std::error_code link_error;
                fs::remove(replacement, link_error);
                link_error.clear();
                fs::create_symlink(fs::path(value), replacement, link_error);
                if (!link_error) fs::rename(replacement, item.path(), link_error);
                if (link_error) {
                    fs::remove(replacement, link_error);
                    throw std::runtime_error("could not repair managed virtualenv symlink");
                }
            }
        }
#endif
        return true;
    } catch (const std::exception& exception) {
        error = exception.what();
        return false;
    }
}

}  // namespace baas_installer
