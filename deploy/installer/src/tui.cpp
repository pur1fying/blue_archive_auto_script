#include "baas_installer/tui.hpp"

#include <iostream>

#ifdef _WIN32
#include <conio.h>
#else
#include <termios.h>
#include <unistd.h>
#endif

namespace baas_installer {

std::string redact_cdk(const std::string& cdk) {
    if (cdk.empty()) return "(none)";
    if (cdk.size() <= 4) return "****";
    return cdk.substr(0, 2) + std::string(cdk.size() - 4, '*') + cdk.substr(cdk.size() - 2);
}

void print_tui_banner() { std::cout << "\n╔══════════════════════════════════════╗\n║       BAAS Installer (portable)      ║\n╚══════════════════════════════════════╝\n"; }
void print_progress(const std::string& task, const std::string& state, const std::string& detail) { std::cout << "[" << task << "] " << state << (detail.empty() ? "" : " — " + detail) << '\n'; }
bool ask_yes_no(const std::string& prompt) { std::cout << prompt << " [y/N] "; std::string answer; std::getline(std::cin, answer); return answer == "y" || answer == "Y" || answer == "yes" || answer == "YES"; }

std::string ask_secret(const std::string& prompt) {
    std::cout << prompt;
    std::string value;
#ifdef _WIN32
    for (int key; (key = _getch()) != '\r' && key != '\n';) {
        if (key == '\b') { if (!value.empty()) { value.pop_back(); std::cout << "\b \b"; } }
        else if (key >= 32 && key <= 126) { value.push_back(static_cast<char>(key)); std::cout << '*'; }
    }
#else
    termios old_state{}; tcgetattr(STDIN_FILENO, &old_state); auto hidden = old_state; hidden.c_lflag &= ~ECHO; tcsetattr(STDIN_FILENO, TCSANOW, &hidden);
    std::getline(std::cin, value); tcsetattr(STDIN_FILENO, TCSANOW, &old_state);
#endif
    std::cout << '\n';
    return value;
}

}  // namespace baas_installer
