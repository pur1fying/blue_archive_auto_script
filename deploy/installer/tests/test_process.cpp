#include "baas_installer/process.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>

int main(int argc, char* argv[]) {
    if (argc == 2 && std::string(argv[1]) == "--emit-child") {
        std::cout << "安装进度 42%" << std::endl;
        std::cerr << "child diagnostic" << std::endl;
        return 7;
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
    std::filesystem::remove(log, ignored);
    return 0;
}
