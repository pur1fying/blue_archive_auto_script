#include "baas_installer/localization.hpp"

#include <algorithm>
#include <array>
#include <cstdlib>

#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#endif

namespace baas_installer {
namespace {

constexpr std::size_t message_count = static_cast<std::size_t>(MessageId::LaunchFailed) + 1;

constexpr std::array<const char*, message_count> english{
    "Welcome to BlueArchive Auto Script!", "Installation and migration tool", "Installation source", "Use MirrorChyan CDK", "Enter CDK",
    "Without a CDK, Git and ranked mirrors are used automatically.", "Start installation", "Retry", "Exit",
    "Main repository", "OCR component", "Deployment", "Python / uv", "Verification", "Launch BAAS",
    "Waiting", "Checking", "Downloading", "Applying", "Complete", "Failed",
    "Installation succeeded, but BAAS could not be launched",
};

constexpr std::array<const char*, message_count> chinese{
    "欢迎使用蔚蓝档案自动脚本！", "安装与迁移工具", "安装源设置", "使用 MirrorChyan CDK", "输入 CDK",
    "没有 CDK 时将使用 Git，并按镜像源自动回退。", "开始安装", "重试", "退出",
    "主仓库", "OCR 组件", "文件部署", "Python / uv", "完整性检查", "启动 BAAS",
    "等待中", "正在检查", "正在下载", "正在应用", "已完成", "失败",
    "安装成功，但无法启动 BAAS",
};

std::string environment_value(const char* name) {
    if (const char* value = std::getenv(name)) return value;
    return {};
}

bool is_chinese_locale(std::string locale) {
    std::transform(locale.begin(), locale.end(), locale.begin(), [](const unsigned char ch) {
        return ch == '_' ? '-' : static_cast<char>(std::tolower(ch));
    });
    const auto separator = locale.find_first_of("-.@");
    return locale.substr(0, separator) == "zh";
}

}  // namespace

Language detect_language(const LocaleInputs& inputs) {
    if (inputs.windows_ui_language != 0) {
        return (inputs.windows_ui_language & 0x03ffUL) == 0x0004UL ? Language::SimplifiedChinese : Language::English;
    }
    const auto& locale = !inputs.lc_all.empty() ? inputs.lc_all
                       : !inputs.lc_messages.empty() ? inputs.lc_messages
                                                     : inputs.lang;
    return is_chinese_locale(locale) ? Language::SimplifiedChinese : Language::English;
}

LocaleInputs system_locale_inputs() {
    LocaleInputs inputs;
#ifdef _WIN32
    inputs.windows_ui_language = GetUserDefaultUILanguage();
#else
    inputs.lc_all = environment_value("LC_ALL");
    inputs.lc_messages = environment_value("LC_MESSAGES");
    inputs.lang = environment_value("LANG");
#endif
    return inputs;
}

Language detect_system_language() { return detect_language(system_locale_inputs()); }

std::string message(const Language language, const MessageId id) {
    const auto index = static_cast<std::size_t>(id);
    return language == Language::SimplifiedChinese ? chinese[index] : english[index];
}

}  // namespace baas_installer
