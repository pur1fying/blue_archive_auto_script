#include "baas_installer/tui.hpp"

#include <iostream>

int main() {
    const auto redacted = baas_installer::redact_cdk("abcdef1234");
    if (redacted.find("abcdef1234") != std::string::npos || redacted.find("ab") != 0 || redacted.size() != 10) {
        std::cerr << "CDK redaction failed\n"; return 1;
    }
    return 0;
}
