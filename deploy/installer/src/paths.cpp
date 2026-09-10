#include "baas_installer/paths.hpp"

#include <array>
#include <cstdint>
#include <stdexcept>
#include <string>

#ifdef _WIN32
#include <windows.h>
#elif defined(__linux__)
#include <unistd.h>
#elif defined(__APPLE__)
#include <mach-o/dyld.h>
#endif

namespace baas_installer {

InstallPaths InstallPaths::from_executable(const std::filesystem::path& executable) {
    const auto normalized = executable.lexically_normal();
    return from_root(normalized.parent_path(), normalized.filename());
}

InstallPaths InstallPaths::from_root(const std::filesystem::path& requested_root,
                                    const std::filesystem::path& executable_name) {
    const auto root = std::filesystem::absolute(requested_root).lexically_normal();
    return from_install_root(root, root / executable_name);
}

InstallPaths InstallPaths::from_install_root(const std::filesystem::path& requested_root,
                                             const std::filesystem::path& requested_executable) {
    const auto root = std::filesystem::absolute(requested_root).lexically_normal();
    const auto executable = std::filesystem::absolute(requested_executable).lexically_normal();
    const auto toolkit_dir = root / "toolkit";
    return {
        .executable = executable,
        .root = root,
        .setup_toml = executable.parent_path() / "setup.toml",
        .tmp_dir = root / "tmp",
        .toolkit_dir = toolkit_dir,
        .uv_dir = toolkit_dir / "uv",
        .venv_dir = root / ".venv",
        .logs_dir = root / "log",
        .state_dir = root / ".baas-installer",
    };
}

std::filesystem::path current_executable_path() {
#ifdef _WIN32
    std::wstring buffer(32768, L'\0');
    const auto size = GetModuleFileNameW(nullptr, buffer.data(), static_cast<DWORD>(buffer.size()));
    if (size != 0 && size < buffer.size()) return std::filesystem::path(buffer.substr(0, size));
#elif defined(__linux__)
    std::array<char, 4096> buffer{};
    const auto size = readlink("/proc/self/exe", buffer.data(), buffer.size() - 1);
    if (size > 0) return std::filesystem::path(std::string(buffer.data(), static_cast<std::size_t>(size)));
#elif defined(__APPLE__)
    std::uint32_t size = 0;
    _NSGetExecutablePath(nullptr, &size);
    std::string buffer(size, '\0');
    if (_NSGetExecutablePath(buffer.data(), &size) == 0) return std::filesystem::weakly_canonical(buffer.c_str());
#endif
    return {};
}

std::string path_to_utf8(const std::filesystem::path& path) {
#ifdef _WIN32
    const auto wide = path.wstring();
    if (wide.empty()) return {};
    const auto size = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS,
                                          wide.data(), static_cast<int>(wide.size()),
                                          nullptr, 0, nullptr, nullptr);
    if (size <= 0) throw std::filesystem::filesystem_error(
        "path could not be encoded as UTF-8", path, std::error_code{});
    std::string result(static_cast<std::size_t>(size), '\0');
    WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, wide.data(),
                        static_cast<int>(wide.size()), result.data(), size,
                        nullptr, nullptr);
    return result;
#else
    return path.string();
#endif
}

std::filesystem::path path_from_utf8(const std::string_view value) {
#ifdef _WIN32
    if (value.empty()) return {};
    const auto size = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS,
                                          value.data(), static_cast<int>(value.size()),
                                          nullptr, 0);
    if (size <= 0) throw std::invalid_argument("path is not valid UTF-8");
    std::wstring wide(static_cast<std::size_t>(size), L'\0');
    MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, value.data(),
                        static_cast<int>(value.size()), wide.data(), size);
    return std::filesystem::path(wide);
#else
    return std::filesystem::path(value);
#endif
}

}  // namespace baas_installer
