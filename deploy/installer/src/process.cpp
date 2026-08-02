#include "baas_installer/process.hpp"

#include <fstream>
#include <mutex>
#include <sstream>

#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#else
#include <cstdio>
#include <sys/wait.h>
#endif

namespace baas_installer {
namespace {

std::mutex default_log_mutex;
std::filesystem::path default_log_path;

void publish_output(const ProcessSpec& spec, ProcessResult& result, const std::string& chunk, std::ofstream& log) {
    result.output += chunk;
    if (log) {
        log.write(chunk.data(), static_cast<std::streamsize>(chunk.size()));
        log.flush();
    }
    if (spec.on_output) spec.on_output(chunk);
}

#ifdef _WIN32
std::wstring widen(const std::string& text) {
    if (text.empty()) return {};
    const int size = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, text.data(), static_cast<int>(text.size()), nullptr, 0);
    if (size <= 0) return std::wstring(text.begin(), text.end());
    std::wstring value(static_cast<std::size_t>(size), L'\0');
    MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, text.data(), static_cast<int>(text.size()), value.data(), size);
    return value;
}

std::wstring quote_windows(const std::wstring& value) {
    if (value.find_first_of(L" \t\"") == std::wstring::npos) return value;
    std::wstring quoted{L'\"'};
    std::size_t slashes = 0;
    for (const wchar_t character : value) {
        if (character == L'\\') { ++slashes; continue; }
        if (character == L'\"') quoted.append(slashes * 2 + 1, L'\\');
        else quoted.append(slashes, L'\\');
        slashes = 0;
        quoted += character;
    }
    quoted.append(slashes * 2, L'\\');
    quoted += L'\"';
    return quoted;
}

std::vector<wchar_t> make_environment(const std::map<std::string, std::string>& overrides) {
    std::map<std::wstring, std::wstring> values;
    if (wchar_t* block = GetEnvironmentStringsW()) {
        for (const wchar_t* item = block; *item; item += std::wcslen(item) + 1) {
            const std::wstring entry(item);
            const auto equals = entry.find(L'=', entry.front() == L'=' ? 1 : 0);
            if (equals != std::wstring::npos) values[entry.substr(0, equals)] = entry.substr(equals + 1);
        }
        FreeEnvironmentStringsW(block);
    }
    for (const auto& [key, value] : overrides) values[widen(key)] = widen(value);
    std::vector<wchar_t> block;
    for (const auto& [key, value] : values) {
        const auto entry = key + L"=" + value;
        block.insert(block.end(), entry.begin(), entry.end());
        block.push_back(L'\0');
    }
    block.push_back(L'\0');
    return block;
}
#else
std::string shell_quote(const std::string& value) {
    std::string result{"'"};
    for (const char character : value) result += character == '\'' ? "'\\''" : std::string(1, character);
    return result + "'";
}
#endif

}  // namespace

void set_default_process_log(const std::filesystem::path& path) {
    std::scoped_lock lock(default_log_mutex);
    default_log_path = path;
}

ProcessResult run_process(const ProcessSpec& spec) {
    ProcessResult result;
    if (spec.arguments.empty()) return result;
    std::ofstream log;
    if (!spec.log_path.empty()) {
        std::error_code ignored;
        std::filesystem::create_directories(spec.log_path.parent_path(), ignored);
        log.open(spec.log_path, std::ios::binary | std::ios::app);
    }

#ifdef _WIN32
    SECURITY_ATTRIBUTES attributes{sizeof(SECURITY_ATTRIBUTES), nullptr, TRUE};
    HANDLE read_pipe = nullptr;
    HANDLE write_pipe = nullptr;
    if (!CreatePipe(&read_pipe, &write_pipe, &attributes, 0)) return result;
    SetHandleInformation(read_pipe, HANDLE_FLAG_INHERIT, 0);

    std::wstring command;
    for (const auto& argument : spec.arguments) {
        if (!command.empty()) command += L' ';
        command += quote_windows(widen(argument));
    }
    std::vector<wchar_t> mutable_command(command.begin(), command.end());
    mutable_command.push_back(L'\0');
    auto environment = make_environment(spec.environment);
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    startup.dwFlags = STARTF_USESTDHANDLES;
    startup.hStdOutput = write_pipe;
    startup.hStdError = write_pipe;
    startup.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    PROCESS_INFORMATION process{};
    const BOOL started = CreateProcessW(nullptr, mutable_command.data(), nullptr, nullptr, TRUE,
        CREATE_NO_WINDOW | CREATE_UNICODE_ENVIRONMENT, environment.data(), nullptr, &startup, &process);
    CloseHandle(write_pipe);
    if (!started) { CloseHandle(read_pipe); return result; }
    char buffer[4096];
    DWORD read = 0;
    while (ReadFile(read_pipe, buffer, sizeof(buffer), &read, nullptr) && read > 0) {
        publish_output(spec, result, std::string(buffer, buffer + read), log);
    }
    WaitForSingleObject(process.hProcess, INFINITE);
    DWORD exit_code = 1;
    GetExitCodeProcess(process.hProcess, &exit_code);
    result.exit_code = static_cast<int>(exit_code);
    CloseHandle(read_pipe);
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
#else
    std::string command;
    for (const auto& [key, value] : spec.environment) command += key + "=" + shell_quote(value) + " ";
    for (const auto& argument : spec.arguments) command += shell_quote(argument) + " ";
    command += "2>&1";
    if (FILE* pipe = popen(command.c_str(), "r")) {
        char buffer[4096];
        while (const auto read = std::fread(buffer, 1, sizeof(buffer), pipe)) {
            publish_output(spec, result, std::string(buffer, buffer + read), log);
        }
        const int status = pclose(pipe);
        result.exit_code = WIFEXITED(status) ? WEXITSTATUS(status) : 1;
    }
#endif
    return result;
}

int run_process(const std::vector<std::string>& arguments, const std::map<std::string, std::string>& environment) {
    ProcessSpec spec;
    spec.arguments = arguments;
    spec.environment = environment;
    {
        std::scoped_lock lock(default_log_mutex);
        spec.log_path = default_log_path;
    }
    return run_process(spec).exit_code;
}

}  // namespace baas_installer
