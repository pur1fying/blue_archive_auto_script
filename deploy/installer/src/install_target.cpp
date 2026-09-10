#include "baas_installer/install_target.hpp"
#include "baas_installer/paths.hpp"

#include <algorithm>
#include <cstdlib>
#include <vector>

#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#endif

namespace fs = std::filesystem;

namespace baas_installer {
namespace {

bool is_cjk_ideograph(const char32_t codepoint) {
    return (codepoint >= 0x3400 && codepoint <= 0x4DBF) ||
           (codepoint >= 0x4E00 && codepoint <= 0x9FFF) ||
           (codepoint >= 0xF900 && codepoint <= 0xFAFF) ||
           (codepoint >= 0x20000 && codepoint <= 0x2EBEF) ||
           (codepoint >= 0x30000 && codepoint <= 0x323AF);
}

bool contains_chinese_characters(const fs::path& path) {
    const auto utf8 = path_to_utf8(path);
    for (std::size_t index = 0; index < utf8.size();) {
        const auto first = static_cast<unsigned char>(utf8[index]);
        char32_t codepoint{};
        std::size_t width{};
        if (first < 0x80) {
            codepoint = first;
            width = 1;
        } else if ((first & 0xE0) == 0xC0) {
            codepoint = first & 0x1F;
            width = 2;
        } else if ((first & 0xF0) == 0xE0) {
            codepoint = first & 0x0F;
            width = 3;
        } else if ((first & 0xF8) == 0xF0) {
            codepoint = first & 0x07;
            width = 4;
        } else {
            ++index;
            continue;
        }
        if (index + width > utf8.size()) break;
        for (std::size_t offset = 1; offset < width; ++offset) {
            codepoint = (codepoint << 6) |
                        (static_cast<unsigned char>(utf8[index + offset]) & 0x3F);
        }
        if (is_cjk_ideograph(codepoint)) return true;
        index += width;
    }
    return false;
}

bool contains_parent_component(const fs::path& path) {
    return std::any_of(path.begin(), path.end(), [](const fs::path& component) {
        return component == "..";
    });
}

bool is_reparse_or_symlink(const fs::path& path) {
    std::error_code error;
    if (fs::is_symlink(fs::symlink_status(path, error))) return true;
#ifdef _WIN32
    const auto attributes = GetFileAttributesW(path.wstring().c_str());
    return attributes != INVALID_FILE_ATTRIBUTES &&
           (attributes & FILE_ATTRIBUTE_REPARSE_POINT) != 0;
#else
    return false;
#endif
}

bool crosses_link(const fs::path& absolute_path) {
    fs::path current;
    for (const auto& component : absolute_path) {
        current /= component;
        std::error_code error;
        if (!fs::exists(current, error)) continue;
        if (error || is_reparse_or_symlink(current)) return true;
    }
    return false;
}

bool same_normalized_path(const fs::path& left, const fs::path& right) {
    auto lhs = fs::absolute(left).lexically_normal();
    auto rhs = fs::absolute(right).lexically_normal();
#ifdef _WIN32
    auto lhs_text = lhs.wstring();
    auto rhs_text = rhs.wstring();
    if (!lhs_text.empty()) CharLowerBuffW(lhs_text.data(), static_cast<DWORD>(lhs_text.size()));
    if (!rhs_text.empty()) CharLowerBuffW(rhs_text.data(), static_cast<DWORD>(rhs_text.size()));
    return lhs_text == rhs_text;
#else
    return lhs == rhs;
#endif
}

std::vector<fs::path> protected_user_roots() {
    std::vector<fs::path> result;
#ifdef _WIN32
    const char* profile = std::getenv("USERPROFILE");
#else
    const char* profile = std::getenv("HOME");
#endif
    if (profile == nullptr || *profile == '\0') return result;
    const fs::path home(profile);
    result.push_back(home);
    result.push_back(home / "Desktop");
    result.push_back(home / "Documents");
    result.push_back(home / "Downloads");
    return result;
}

bool directory_is_empty(const fs::path& path, std::error_code& error) {
    return fs::directory_iterator(path, error) == fs::directory_iterator();
}

bool directory_contains_only(const fs::path& directory,
                             const std::vector<fs::path>& allowed,
                             std::error_code& error) {
    for (fs::directory_iterator it(directory, error), end; !error && it != end; it.increment(error)) {
        bool matched = false;
        for (const auto& candidate : allowed) {
            if (same_normalized_path(it->path(), candidate)) {
                matched = true;
                break;
            }
        }
        if (!matched) return false;
    }
    return !error;
}

bool executable_directory_is_safe(const fs::path& executable, const fs::path& target,
                                  std::string& error_message) {
    const auto launcher = executable.parent_path();
    const auto setup = launcher / "setup.toml";
    if (same_normalized_path(launcher, target)) {
        // Directory cleanliness beside the executable is a first-install
        // guard only.  Existing setup is evaluated later as either a proven
        // BAAS installation or a clean interrupted-install retry.
        if (fs::is_regular_file(setup)) return true;
        std::error_code error;
        if (!directory_contains_only(launcher, {executable}, error)) {
            error_message = error ? "installer directory could not be inspected"
                                  : "installer directory contains unrelated files";
            return false;
        }
        return true;
    }
    return true;
}

}  // namespace

fs::path default_install_root(const fs::path& source_executable) {
    return fs::absolute(source_executable).lexically_normal().parent_path();
}

fs::path resolve_install_root(const fs::path& source_executable,
                              const fs::path& configured_root) {
    const auto executable = fs::absolute(source_executable).lexically_normal();
    const auto requested = configured_root.empty() ? fs::path(".") : configured_root;
    auto resolved = fs::absolute(requested.is_absolute() ? requested
                                                          : executable.parent_path() / requested)
                        .lexically_normal();
    if (resolved != resolved.root_path() && resolved.filename().empty()) {
        resolved = resolved.parent_path();
    }
    return resolved;
}

bool is_recognized_installation(const fs::path& root) {
    std::error_code error;
    if (!fs::is_directory(root, error) || error) return false;
    const auto state = root / ".baas-installer";
    if ((fs::is_regular_file(state / "installer.lock", error) && !error) ||
        (fs::is_regular_file(state / "main-files-v1.json", error) && !error) ||
        (fs::is_regular_file(state / "dependencies-v1.sha256", error) && !error)) {
        return true;
    }
    error.clear();
    return fs::is_regular_file(root / "main.py", error) && !error &&
           fs::is_regular_file(root / "requirements.txt", error) && !error;
}

TargetValidation validate_install_target(const fs::path& source_executable,
                                         const fs::path& requested_root) {
    TargetValidation result;
    if (requested_root.empty()) {
        result.error = "installation directory is empty";
        return result;
    }
    if (requested_root.is_relative() && contains_parent_component(requested_root)) {
        result.error = "a relative installation directory cannot contain a parent ('..') component";
        return result;
    }
    std::error_code error;
    const auto executable = fs::absolute(source_executable, error).lexically_normal();
    if (error || !fs::is_regular_file(executable, error) || error) {
        result.error = "running installer path is invalid";
        return result;
    }
    if (crosses_link(executable)) {
        result.error = "running installer path crosses a symbolic link or reparse point";
        return result;
    }
    const auto absolute = resolve_install_root(executable, requested_root);
    if (error || absolute.empty()) {
        result.error = "installation directory could not be normalized";
        return result;
    }
    result.root = absolute;
    if (contains_chinese_characters(absolute)) {
        result.error = "The installation directory contains Chinese characters. Qt is incompatible with "
                       "Chinese installation paths; use an ASCII-only path. / "
                       "安装目录不能包含中文字符：Qt 不兼容中文安装目录，请改用仅含 ASCII 字符的路径。";
        return result;
    }
    if (same_normalized_path(absolute, absolute.root_path())) {
        result.error = "a filesystem root cannot be used as the installation directory";
        return result;
    }
    for (const auto& protected_root : protected_user_roots()) {
        if (same_normalized_path(absolute, protected_root)) {
            result.error = "a user profile or standard user directory cannot be used directly";
            return result;
        }
    }
    if (crosses_link(absolute)) {
        result.error = "installation directory crosses a symbolic link or reparse point";
        return result;
    }
    if (!executable_directory_is_safe(executable, absolute, result.error)) return result;

    const bool exists = fs::exists(absolute, error);
    if (error) {
        result.error = "installation directory could not be inspected";
        return result;
    }
    if (!exists) {
        result.accepted = true;
        return result;
    }
    if (!fs::is_directory(absolute, error) || error) {
        result.error = "installation target is not a directory";
        return result;
    }
    result.existing_installation = is_recognized_installation(absolute);
    if (result.existing_installation) {
        result.accepted = true;
        return result;
    }
    if (same_normalized_path(absolute, executable.parent_path())) {
        if (!directory_contains_only(absolute, {executable, executable.parent_path() / "setup.toml"}, error) || error) {
            result.error = error ? "installation directory could not be inspected"
                                 : "installation directory contains unrelated files";
            return result;
        }
        result.accepted = true;
        return result;
    }
    if (!directory_is_empty(absolute, error) || error) {
        result.error = error ? "installation directory could not be inspected"
                             : "installation directory is not empty and is not a recognized BAAS installation";
        return result;
    }
    result.accepted = true;
    return result;
}

}  // namespace baas_installer
