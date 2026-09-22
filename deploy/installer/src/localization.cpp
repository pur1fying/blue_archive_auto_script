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

constexpr std::size_t message_count = static_cast<std::size_t>(MessageId::InstallDirectoryInvalidTitle) + 1;

constexpr std::array<const char*, message_count> english{
    "Welcome to BlueArchive Auto Script!", "Installation and migration tool", "Installation source", "Use MirrorChyan CDK", "Enter CDK",
    "Without a CDK, Git and ranked mirrors are used automatically.", "Start installation", "Retry", "Exit",
    "Main repository", "OCR component", "Deployment", "Python / uv", "Verification", "Launch BAAS",
    "Waiting", "Checking", "Downloading", "Applying", "Complete", "Failed",
    "Choose a dedicated installation directory",
    "Only a new, empty, or recognized BAAS directory is accepted.",
    "Relative example: BAAS",
#ifdef _WIN32
    R"(Absolute example: D:\Games\BAAS)",
#else
    "Absolute example: /home/user/BAAS",
#endif
    "Installation succeeded, but BAAS could not be launched",
    "MirrorChyan installation failed",
    "MirrorChyan will not fall back to Git. Re-enter the CDK or return to installation settings.",
    "Re-enter CDK", "Back to settings", "Back", "Validating CDK...", "Enter a MirrorChyan CDK",
    "Confirm", "Invalid installation directory",
};

constexpr std::array<const char*, message_count> chinese{
    "欢迎使用蔚蓝档案自动脚本！", "安装与迁移工具", "安装源设置", "使用 MirrorChyan CDK", "输入 CDK",
    "没有 CDK 时将使用 Git，并按镜像源自动回退。", "开始安装", "重试", "退出",
    "主仓库", "OCR 组件", "文件部署", "Python / uv", "完整性检查", "启动 BAAS",
    "等待中", "正在检查", "正在下载", "正在应用", "已完成", "失败",
    "选择专用安装目录",
    "仅允许新目录、空目录或可识别的 BAAS 目录。",
    "相对路径示例：BAAS",
#ifdef _WIN32
    R"(绝对路径示例：D:\Games\BAAS)",
#else
    "绝对路径示例：/home/user/BAAS",
#endif
    "安装成功，但无法启动 BAAS",
    "MirrorChyan 安装失败",
    "MirrorChyan 不会回退到 Git。请重新填写 CDK，或返回安装设置。",
    "重新填写 CDK", "返回安装设置", "返回", "正在验证 CDK……", "请输入 MirrorChyan CDK",
    "确定", "安装目录不合法",
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
