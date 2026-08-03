#include "baas_installer/localization.hpp"

#include <iostream>

namespace {
bool expect_language(const baas_installer::LocaleInputs& inputs, const baas_installer::Language expected,
                     const char* label) {
    if (baas_installer::detect_language(inputs) == expected) return true;
    std::cerr << "unexpected language for " << label << '\n';
    return false;
}
}

int main() {
    using baas_installer::Language;
    using baas_installer::LocaleInputs;
    using baas_installer::MessageId;

    if (!expect_language({.lang = "zh-CN"}, Language::SimplifiedChinese, "zh-CN") ||
        !expect_language({.lc_messages = "zh_CN.UTF-8"}, Language::SimplifiedChinese, "zh_CN") ||
        !expect_language({.windows_ui_language = 0x0804}, Language::SimplifiedChinese, "Windows zh-CN") ||
        !expect_language({.lc_all = "en_US.UTF-8", .lang = "zh_CN"}, Language::English, "LC_ALL precedence") ||
        !expect_language({.lang = "ja_JP"}, Language::English, "Japanese") ||
        !expect_language({}, Language::English, "empty locale")) {
        return 1;
    }

    for (const auto language : {Language::English, Language::SimplifiedChinese}) {
        for (const auto id : {MessageId::Welcome, MessageId::AppSubtitle, MessageId::TaskMain, MessageId::TaskOcr,
                              MessageId::StateChecking, MessageId::StateDownloading,
                              MessageId::ActionRetry, MessageId::ActionExit, MessageId::LaunchFailed}) {
            if (baas_installer::message(language, id).empty()) {
                std::cerr << "message catalog contains an empty installer string\n";
                return 1;
            }
        }
    }
    return 0;
}
