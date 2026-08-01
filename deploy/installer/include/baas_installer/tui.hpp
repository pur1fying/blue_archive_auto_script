#pragma once

#include <string>

namespace baas_installer {

std::string redact_cdk(const std::string& cdk);
void print_tui_banner();
void print_progress(const std::string& task, const std::string& state, const std::string& detail = {});
bool ask_yes_no(const std::string& prompt);
std::string ask_secret(const std::string& prompt);

}  // namespace baas_installer
