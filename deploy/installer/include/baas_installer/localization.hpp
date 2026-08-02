#pragma once

#include <string>

namespace baas_installer {

enum class Language { English, SimplifiedChinese };

struct LocaleInputs {
    std::string lc_all;
    std::string lc_messages;
    std::string lang;
    unsigned long windows_ui_language{};
};

enum class MessageId {
    Welcome,
    AppSubtitle,
    SetupTitle,
    UseMirror,
    CdkPlaceholder,
    GitFallbackHint,
    ActionStart,
    ActionRetry,
    ActionExit,
    TaskMain,
    TaskOcr,
    TaskDeployment,
    TaskUv,
    TaskVerify,
    TaskLaunch,
    StateWaiting,
    StateChecking,
    StateDownloading,
    StateApplying,
    StateComplete,
    StateFailed,
    LaunchFailed,
};

Language detect_language(const LocaleInputs& inputs);
LocaleInputs system_locale_inputs();
Language detect_system_language();
std::string message(Language language, MessageId id);

}  // namespace baas_installer
