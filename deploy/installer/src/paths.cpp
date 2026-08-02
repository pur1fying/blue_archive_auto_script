#include "baas_installer/paths.hpp"

#include <array>
#include <cstdint>
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
    const auto root = executable.lexically_normal().parent_path();
    const auto toolkit_dir = root / "toolkit";
    return {
        .executable = executable.lexically_normal(),
        .root = root,
        .setup_toml = root / "setup.toml",
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

}  // namespace baas_installer
