#include "baas_installer/git.hpp"

#include <iostream>

int main() {
    if (baas_installer::git_backend_name(baas_installer::GitBackend::GitCli) != "git-cli") {
        std::cerr << "git backend label failed\n";
        return 1;
    }
    if (baas_installer::git_backend_name(baas_installer::GitBackend::None) != "none") {
        std::cerr << "none backend label failed\n";
        return 1;
    }
    return 0;
}
