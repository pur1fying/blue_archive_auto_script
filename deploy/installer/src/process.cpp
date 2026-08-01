#include "baas_installer/process.hpp"

#include <cstdlib>

namespace baas_installer {
namespace {
std::string quote(const std::string& text) {
    std::string result{"\""};
    for (const char character : text) { if (character == '\"') result += '\\'; result += character; }
    return result + '\"';
}
}

int run_process(const std::vector<std::string>& arguments, const std::map<std::string, std::string>& environment) {
    if (arguments.empty()) return 1;
    std::string command;
#ifdef _WIN32
    command = "setlocal";
    for (const auto& [key, value] : environment) command += " && set " + quote(key + "=" + value);
    command += " && ";
#else
    for (const auto& [key, value] : environment) command += key + "=" + quote(value) + " ";
#endif
    for (const auto& argument : arguments) command += quote(argument) + " ";
    return std::system(command.c_str());
}

}  // namespace baas_installer
