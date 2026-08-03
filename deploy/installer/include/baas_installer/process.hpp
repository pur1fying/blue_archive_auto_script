#pragma once

#include <filesystem>
#include <functional>
#include <map>
#include <chrono>
#include <string>
#include <string_view>
#include <vector>

namespace baas_installer {

struct ProcessSpec {
    std::vector<std::string> arguments;
    std::map<std::string, std::string> environment;
    std::filesystem::path log_path;
    std::filesystem::path working_directory;
    std::chrono::milliseconds timeout{std::chrono::milliseconds::zero()};
    bool use_pty{};
    std::function<void(const std::string&)> on_output;
    std::function<void(std::string_view)> on_chunk;
};

struct ProcessResult {
    int exit_code{1};
    std::string output;
};

ProcessResult run_process(const ProcessSpec& spec);
ProcessResult run_terminal_process(const ProcessSpec& spec);
void set_default_process_log(const std::filesystem::path& path);
int run_process(const std::vector<std::string>& arguments, const std::map<std::string, std::string>& environment = {});
bool launch_detached(const std::vector<std::string>& arguments,
                     const std::map<std::string, std::string>& environment = {},
                     const std::filesystem::path& working_directory = {});
}  // namespace baas_installer
