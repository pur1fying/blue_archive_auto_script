#include "baas_installer/process.hpp"

#include <cerrno>
#include <fstream>
#include <mutex>
#include <sstream>
#include <thread>

#ifdef _WIN32
#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0A00
#endif
#define NOMINMAX
#include <windows.h>
#else
#include <cstdio>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <sys/wait.h>
#include <unistd.h>
#ifdef __APPLE__
#include <util.h>
#else
#include <pty.h>
#endif
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
    if (spec.on_chunk) spec.on_chunk(chunk);
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

std::vector<wchar_t> make_command(const std::vector<std::string>& arguments) {
    std::wstring command;
    for (const auto& argument : arguments) {
        if (!command.empty()) command += L' ';
        command += quote_windows(widen(argument));
    }
    std::vector<wchar_t> mutable_command(command.begin(), command.end());
    mutable_command.push_back(L'\0');
    return mutable_command;
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

    auto mutable_command = make_command(spec.arguments);
    auto environment = make_environment(spec.environment);
    const auto working_directory = spec.working_directory.empty() ? std::wstring{} : spec.working_directory.wstring();
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    startup.dwFlags = STARTF_USESTDHANDLES;
    startup.hStdOutput = write_pipe;
    startup.hStdError = write_pipe;
    startup.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    PROCESS_INFORMATION process{};
    HANDLE job = CreateJobObjectW(nullptr, nullptr);
    if (job) {
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits{};
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        if (!SetInformationJobObject(job, JobObjectExtendedLimitInformation, &limits, sizeof(limits))) {
            CloseHandle(job);
            job = nullptr;
        }
    }
    const BOOL started = CreateProcessW(nullptr, mutable_command.data(), nullptr, nullptr, TRUE,
        CREATE_NO_WINDOW | CREATE_UNICODE_ENVIRONMENT | CREATE_SUSPENDED, environment.data(),
        working_directory.empty() ? nullptr : working_directory.c_str(), &startup, &process);
    CloseHandle(write_pipe);
    if (!started) { if (job) CloseHandle(job); CloseHandle(read_pipe); return result; }
    if (job && !AssignProcessToJobObject(job, process.hProcess)) {
        CloseHandle(job);
        job = nullptr;
    }
    ResumeThread(process.hThread);
    std::thread reader([&] {
        char buffer[4096];
        DWORD read = 0;
        while (ReadFile(read_pipe, buffer, sizeof(buffer), &read, nullptr) && read > 0) {
            publish_output(spec, result, std::string(buffer, buffer + read), log);
        }
    });
    const DWORD timeout = spec.timeout <= std::chrono::milliseconds::zero()
        ? INFINITE
        : static_cast<DWORD>(std::min<std::int64_t>(spec.timeout.count(), MAXDWORD - 1));
    const bool timed_out = WaitForSingleObject(process.hProcess, timeout) == WAIT_TIMEOUT;
    if (timed_out) {
        if (job) TerminateJobObject(job, 124);
        else TerminateProcess(process.hProcess, 124);
        WaitForSingleObject(process.hProcess, INFINITE);
    }
    DWORD exit_code = 1;
    GetExitCodeProcess(process.hProcess, &exit_code);
    result.exit_code = timed_out ? 124 : static_cast<int>(exit_code);
    if (job) CloseHandle(job);
    if (reader.joinable()) reader.join();
    CloseHandle(read_pipe);
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
#else
    int output_pipe[2]{};
    if (pipe(output_pipe) != 0) return result;
    const pid_t child = fork();
    if (child < 0) { close(output_pipe[0]); close(output_pipe[1]); return result; }
    if (child == 0) {
        setpgid(0, 0);
        close(output_pipe[0]);
        dup2(output_pipe[1], STDOUT_FILENO);
        dup2(output_pipe[1], STDERR_FILENO);
        close(output_pipe[1]);
        if (!spec.working_directory.empty() && chdir(spec.working_directory.c_str()) != 0) _exit(127);
        for (const auto& [key, value] : spec.environment) setenv(key.c_str(), value.c_str(), 1);
        std::vector<char*> argv;
        argv.reserve(spec.arguments.size() + 1);
        for (const auto& argument : spec.arguments) argv.push_back(const_cast<char*>(argument.c_str()));
        argv.push_back(nullptr);
        execvp(argv.front(), argv.data());
        _exit(127);
    }
    setpgid(child, child);
    close(output_pipe[1]);
    const int flags = fcntl(output_pipe[0], F_GETFL, 0);
    fcntl(output_pipe[0], F_SETFL, flags | O_NONBLOCK);
    const auto started_at = std::chrono::steady_clock::now();
    int status = 0;
    bool exited = false;
    bool timed_out = false;
    while (true) {
        char buffer[4096];
        while (const auto count = read(output_pipe[0], buffer, sizeof(buffer))) {
            if (count > 0) publish_output(spec, result, std::string(buffer, buffer + count), log);
            else break;
        }
        if (!exited) exited = waitpid(child, &status, WNOHANG) == child;
        if (exited) {
            const auto count = read(output_pipe[0], buffer, sizeof(buffer));
            if (count > 0) { publish_output(spec, result, std::string(buffer, buffer + count), log); continue; }
            break;
        }
        if (spec.timeout > std::chrono::milliseconds::zero() &&
            std::chrono::steady_clock::now() - started_at >= spec.timeout) {
            timed_out = true;
            kill(-child, SIGKILL);
            waitpid(child, &status, 0);
            exited = true;
            continue;
        }
        pollfd descriptor{output_pipe[0], POLLIN, 0};
        poll(&descriptor, 1, 20);
    }
    close(output_pipe[0]);
    result.exit_code = timed_out ? 124 : (WIFEXITED(status) ? WEXITSTATUS(status) : 1);
#endif
    return result;
}

ProcessResult run_terminal_process(const ProcessSpec& spec) {
    ProcessResult result;
    if (spec.arguments.empty()) return result;
    std::ofstream log;
    if (!spec.log_path.empty()) {
        std::error_code ignored;
        std::filesystem::create_directories(spec.log_path.parent_path(), ignored);
        log.open(spec.log_path, std::ios::binary | std::ios::app);
    }
#ifdef _WIN32
    HANDLE pseudo_input_read = nullptr;
    HANDLE pseudo_input_write = nullptr;
    HANDLE pseudo_output_read = nullptr;
    HANDLE pseudo_output_write = nullptr;
    if (!CreatePipe(&pseudo_input_read, &pseudo_input_write, nullptr, 0) ||
        !CreatePipe(&pseudo_output_read, &pseudo_output_write, nullptr, 0)) {
        if (pseudo_input_read) CloseHandle(pseudo_input_read);
        if (pseudo_input_write) CloseHandle(pseudo_input_write);
        if (pseudo_output_read) CloseHandle(pseudo_output_read);
        if (pseudo_output_write) CloseHandle(pseudo_output_write);
        return result;
    }
    HPCON pseudo_console = nullptr;
    const COORD size{120, 40};
    if (FAILED(CreatePseudoConsole(size, pseudo_input_read, pseudo_output_write, 0, &pseudo_console))) {
        CloseHandle(pseudo_input_read); CloseHandle(pseudo_input_write);
        CloseHandle(pseudo_output_read); CloseHandle(pseudo_output_write);
        return result;
    }
    CloseHandle(pseudo_input_read);
    CloseHandle(pseudo_output_write);

    SIZE_T attribute_size = 0;
    InitializeProcThreadAttributeList(nullptr, 1, 0, &attribute_size);
    auto attribute_memory = std::vector<unsigned char>(attribute_size);
    auto* attributes_list = reinterpret_cast<PPROC_THREAD_ATTRIBUTE_LIST>(attribute_memory.data());
    if (!InitializeProcThreadAttributeList(attributes_list, 1, 0, &attribute_size)) {
        ClosePseudoConsole(pseudo_console);
        CloseHandle(pseudo_input_write); CloseHandle(pseudo_output_read);
        return result;
    }
    if (!UpdateProcThreadAttribute(attributes_list, 0, PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE,
                                   pseudo_console, sizeof(pseudo_console), nullptr, nullptr)) {
        DeleteProcThreadAttributeList(attributes_list);
        ClosePseudoConsole(pseudo_console);
        CloseHandle(pseudo_input_write); CloseHandle(pseudo_output_read);
        return result;
    }

    STARTUPINFOEXW startup{};
    startup.StartupInfo.cb = sizeof(startup);
    startup.StartupInfo.dwFlags = STARTF_USESTDHANDLES;
    startup.StartupInfo.hStdInput = nullptr;
    startup.StartupInfo.hStdOutput = nullptr;
    startup.StartupInfo.hStdError = nullptr;
    startup.lpAttributeList = attributes_list;
    auto mutable_command = make_command(spec.arguments);
    auto environment = make_environment(spec.environment);
    const auto working_directory = spec.working_directory.empty() ? std::wstring{} : spec.working_directory.wstring();
    PROCESS_INFORMATION process{};
    const BOOL started = CreateProcessW(nullptr, mutable_command.data(), nullptr, nullptr, FALSE,
        EXTENDED_STARTUPINFO_PRESENT | CREATE_UNICODE_ENVIRONMENT, environment.data(),
        working_directory.empty() ? nullptr : working_directory.c_str(), &startup.StartupInfo, &process);
    DeleteProcThreadAttributeList(attributes_list);
    if (!started) {
        CloseHandle(pseudo_input_write);
        ClosePseudoConsole(pseudo_console);
        CloseHandle(pseudo_output_read);
        return result;
    }

    std::thread reader([&] {
        char buffer[4096];
        DWORD read = 0;
        while (ReadFile(pseudo_output_read, buffer, sizeof(buffer), &read, nullptr) && read > 0) {
            publish_output(spec, result, std::string(buffer, buffer + read), log);
        }
    });
    const DWORD timeout = spec.timeout <= std::chrono::milliseconds::zero()
        ? INFINITE
        : static_cast<DWORD>(std::min<std::int64_t>(spec.timeout.count(), MAXDWORD - 1));
    if (WaitForSingleObject(process.hProcess, timeout) == WAIT_TIMEOUT) {
        TerminateProcess(process.hProcess, 124);
        WaitForSingleObject(process.hProcess, INFINITE);
    }
    DWORD exit_code = 1;
    GetExitCodeProcess(process.hProcess, &exit_code);
    result.exit_code = static_cast<int>(exit_code);
    CloseHandle(pseudo_input_write);
    ClosePseudoConsole(pseudo_console);
    if (reader.joinable()) reader.join();
    CloseHandle(pseudo_output_read);
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
#else
    int master = -1;
    const pid_t child = forkpty(&master, nullptr, nullptr, nullptr);
    if (child < 0) return result;
    if (child == 0) {
        if (!spec.working_directory.empty() && chdir(spec.working_directory.c_str()) != 0) _exit(127);
        for (const auto& [key, value] : spec.environment) setenv(key.c_str(), value.c_str(), 1);
        std::vector<char*> argv;
        argv.reserve(spec.arguments.size() + 1);
        for (const auto& argument : spec.arguments) argv.push_back(const_cast<char*>(argument.c_str()));
        argv.push_back(nullptr);
        execvp(argv.front(), argv.data());
        _exit(127);
    }
    const int flags = fcntl(master, F_GETFL, 0);
    fcntl(master, F_SETFL, flags | O_NONBLOCK);
    const auto started_at = std::chrono::steady_clock::now();
    int status = 0;
    bool exited = false;
    while (true) {
        char buffer[4096];
        while (const auto count = read(master, buffer, sizeof(buffer))) {
            if (count > 0) publish_output(spec, result, std::string(buffer, buffer + count), log);
            else break;
        }
        if (!exited) exited = waitpid(child, &status, WNOHANG) == child;
        if (exited) {
            const auto count = read(master, buffer, sizeof(buffer));
            if (count > 0) {
                publish_output(spec, result, std::string(buffer, buffer + count), log);
                continue;
            }
            break;
        }
        if (spec.timeout > std::chrono::milliseconds::zero() &&
            std::chrono::steady_clock::now() - started_at >= spec.timeout) {
            kill(child, SIGKILL);
            waitpid(child, &status, 0);
            exited = true;
            continue;
        }
        pollfd descriptor{master, POLLIN, 0};
        poll(&descriptor, 1, 20);
    }
    close(master);
    result.exit_code = WIFEXITED(status) ? WEXITSTATUS(status) : 1;
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

bool launch_detached(const std::vector<std::string>& arguments,
                     const std::map<std::string, std::string>& environment_overrides,
                     const std::filesystem::path& working_directory) {
    if (arguments.empty()) return false;
#ifdef _WIN32
    auto mutable_command = make_command(arguments);
    auto environment = make_environment(environment_overrides);
    const auto working_directory_wide = working_directory.empty() ? std::wstring{} : working_directory.wstring();
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION process{};
    const BOOL started = CreateProcessW(nullptr, mutable_command.data(), nullptr, nullptr, FALSE,
        CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS | CREATE_UNICODE_ENVIRONMENT,
        environment.data(), working_directory_wide.empty() ? nullptr : working_directory_wide.c_str(), &startup, &process);
    if (!started) return false;
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return true;
#else
    int status_pipe[2]{};
    if (pipe(status_pipe) != 0) return false;
    if (fcntl(status_pipe[1], F_SETFD, FD_CLOEXEC) != 0) {
        close(status_pipe[0]);
        close(status_pipe[1]);
        return false;
    }
    const pid_t child = fork();
    if (child < 0) {
        close(status_pipe[0]);
        close(status_pipe[1]);
        return false;
    }
    if (child > 0) {
        close(status_pipe[1]);
        int child_error = 0;
        ssize_t count = -1;
        do { count = read(status_pipe[0], &child_error, sizeof(child_error)); } while (count < 0 && errno == EINTR);
        close(status_pipe[0]);
        if (count == 0) return true;
        int status = 0;
        (void)waitpid(child, &status, 0);
        return false;
    }
    close(status_pipe[0]);
    const auto fail = [&](const int error_number) {
        const int value = error_number == 0 ? EIO : error_number;
        (void)write(status_pipe[1], &value, sizeof(value));
        _exit(127);
    };
    if (setsid() < 0) fail(errno);
    if (!working_directory.empty() && chdir(working_directory.c_str()) != 0) fail(errno);
    for (const auto& [key, value] : environment_overrides) {
        if (setenv(key.c_str(), value.c_str(), 1) != 0) fail(errno);
    }
    const int null_fd = open("/dev/null", O_RDWR);
    if (null_fd < 0) fail(errno);
    if (dup2(null_fd, STDIN_FILENO) < 0 || dup2(null_fd, STDOUT_FILENO) < 0 ||
        dup2(null_fd, STDERR_FILENO) < 0) fail(errno);
    if (null_fd > STDERR_FILENO) close(null_fd);
    std::vector<char*> argv;
    argv.reserve(arguments.size() + 1);
    for (const auto& argument : arguments) argv.push_back(const_cast<char*>(argument.c_str()));
    argv.push_back(nullptr);
    execvp(argv.front(), argv.data());
    fail(errno);
#endif
}

}  // namespace baas_installer
