#include "baas_installer/paths.hpp"

#include <filesystem>
#include <iostream>

int main(int argc, char* argv[]) {
    const auto executable = argc > 0 ? std::filesystem::path(argv[0]) : std::filesystem::path{};
    const auto paths = baas_installer::InstallPaths::from_executable(executable);
    std::cout << "BAAS installer root: " << paths.root.string() << '\n';
    return 0;
}
