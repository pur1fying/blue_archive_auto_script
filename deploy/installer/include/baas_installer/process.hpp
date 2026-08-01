#pragma once

#include <map>
#include <string>
#include <vector>

namespace baas_installer {
int run_process(const std::vector<std::string>& arguments, const std::map<std::string, std::string>& environment = {});
}  // namespace baas_installer
