#pragma once

#include <filesystem>
#include <functional>
#include <map>
#include <string>
#include <vector>

namespace baas_installer {

struct ProcessSpec {
    std::vector<std::string> arguments;
    std::map<std::string, std::string> environment;
    std::filesystem::path log_path;
    std::function<void(const std::string&)> on_output;
};

struct ProcessResult {
    int exit_code{1};
    std::string output;
};

ProcessResult run_process(const ProcessSpec& spec);
void set_default_process_log(const std::filesystem::path& path);
int run_process(const std::vector<std::string>& arguments, const std::map<std::string, std::string>& environment = {});
bool launch_detached(const std::vector<std::string>& arguments,
                     const std::map<std::string, std::string>& environment = {},
                     const std::filesystem::path& working_directory = {});
}  // namespace baas_installer
