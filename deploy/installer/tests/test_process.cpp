#include "baas_installer/process.hpp"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <thread>

#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#include <io.h>
#else
#include <unistd.h>
#endif

int main(int argc, char* argv[]) {
    if (argc == 2 && std::string(argv[1]) == "--emit-child") {
        std::cout << "安装进度 42%" << std::endl;
        std::cerr << "child diagnostic" << std::endl;
        return 7;
    }
    if (argc == 3 && std::string(argv[1]) == "--write-marker") {
        std::ofstream(argv[2], std::ios::binary) << "detached";
        return 0;
    }
    if (argc == 3 && std::string(argv[1]) == "--emit-pty") {
#ifdef _WIN32
        DWORD console_mode = 0;
        const bool console_mode_available = GetConsoleMode(GetStdHandle(STD_OUTPUT_HANDLE), &console_mode) != 0;
        const bool terminal = _isatty(_fileno(stdout)) != 0 || console_mode_available;
        SetConsoleOutputCP(CP_UTF8);
#else
        const bool terminal = isatty(STDOUT_FILENO) != 0;
#endif
        const char* marker = std::getenv("BAAS_PTY_TEST");
        std::ofstream(argv[2], std::ios::binary) << "started terminal=" << (terminal ? "1" : "0")
                                                  << " env=" << (marker ? marker : "missing");
        std::cout << "tty=" << (terminal ? "1" : "0") << " env=" << (marker ? marker : "missing") << "\r";
        std::cout.flush();
        const std::string utf8 = "下载";
        std::cout.write(utf8.data(), 2);
        std::cout.flush();
        std::cout.write(utf8.data() + 2, static_cast<std::streamsize>(utf8.size() - 2));
        std::cout << " \x1b[32m42%\x1b[0m\n";
        std::cout.flush();
        return 9;
    }

    const auto log = std::filesystem::temp_directory_path() / "baas-installer-process-test.log";
    std::error_code ignored;
    std::filesystem::remove(log, ignored);
    std::string observed;
    baas_installer::ProcessSpec spec;
    spec.arguments = {std::filesystem::absolute(argv[0]).string(), "--emit-child"};
    spec.log_path = log;
    spec.on_output = [&](const std::string& line) { observed += line; };
    const auto result = baas_installer::run_process(spec);
    if (result.exit_code != 7 || observed.find("安装进度 42%") == std::string::npos) {
        std::cerr << "child output or exit code was not captured\n"; return 1;
    }
    std::ifstream input(log, std::ios::binary);
    const std::string saved{std::istreambuf_iterator<char>(input), {}};
    if (saved.find("安装进度 42%") == std::string::npos || saved.find("child diagnostic") == std::string::npos) {
        std::cerr << "captured child output was not appended to the requested log\n"; return 1;
    }

    std::string pty_chunks;
    std::size_t chunk_count = 0;
    const auto pty_marker = std::filesystem::temp_directory_path() / "baas-installer-pty-test.marker";
    std::filesystem::remove(pty_marker, ignored);
    baas_installer::ProcessSpec terminal_spec;
    terminal_spec.arguments = {std::filesystem::absolute(argv[0]).string(), "--emit-pty", pty_marker.string()};
    terminal_spec.environment = {{"BAAS_PTY_TEST", "visible"}};
    terminal_spec.working_directory = std::filesystem::temp_directory_path();
    terminal_spec.timeout = std::chrono::seconds(10);
    terminal_spec.use_pty = true;
    terminal_spec.on_chunk = [&](const std::string_view chunk) {
        ++chunk_count;
        pty_chunks.append(chunk);
    };
    const auto terminal_result = baas_installer::run_terminal_process(terminal_spec);
    std::ifstream marker_input(pty_marker, std::ios::binary);
    const std::string marker_value{std::istreambuf_iterator<char>(marker_input), {}};
    if (terminal_result.exit_code != 9 || marker_value != "started terminal=1 env=visible" ||
        pty_chunks.find("下载") == std::string::npos || pty_chunks.find("\x1b[32m") == std::string::npos ||
        chunk_count == 0) {
        std::cerr << "PTY execution did not preserve terminal-aware raw output; exit=" << terminal_result.exit_code
                  << " chunks=" << chunk_count << " bytes=" << pty_chunks.size() << " marker=" << marker_value
                  << " captured=" << pty_chunks << '\n';
        return 1;
    }
    std::filesystem::remove(pty_marker, ignored);

    const auto marker = std::filesystem::temp_directory_path() / "baas-installer-detached-test.marker";
    std::filesystem::remove(marker, ignored);
    if (!baas_installer::launch_detached(
            {std::filesystem::absolute(argv[0]).string(), "--write-marker", marker.string()}, {}, marker.parent_path())) {
        std::cerr << "detached child could not be started\n"; return 1;
    }
    for (int attempt = 0; attempt < 100 && !std::filesystem::exists(marker); ++attempt) {
        std::this_thread::sleep_for(std::chrono::milliseconds(20));
    }
    if (!std::filesystem::exists(marker)) {
        std::cerr << "detached child did not create marker\n"; return 1;
    }
    std::filesystem::remove(marker, ignored);
    std::filesystem::remove(log, ignored);
    return 0;
}
