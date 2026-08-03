#pragma once

#include "baas_installer/localization.hpp"
#include "baas_installer/logging.hpp"

#include <functional>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include <ftxui/dom/elements.hpp>

namespace baas_installer {

enum class InstallerScreen { Setup, Installing, Succeeded, Failed };
enum class TaskStatus { Pending, Running, Succeeded, Failed };

struct TaskSnapshot {
    std::string label;
    TaskStatus status{TaskStatus::Pending};
    std::string detail;
    double progress{-1.0};
};

struct InstallerSnapshot {
    InstallerScreen screen{InstallerScreen::Setup};
    std::map<std::string, TaskSnapshot> tasks;
    std::string error;
    std::vector<std::string> log_lines;
    std::size_t log_scroll{};
    bool exit_requested{};
};

class InstallerViewModel {
public:
    explicit InstallerViewModel(bool setup_required, Language language = detect_system_language(),
                                std::shared_ptr<EventLog> event_log = {});
    void begin_install();
    void update_task(const std::string& id, TaskStatus status, std::string detail, double progress = -1.0);
    void append_event(LogEvent event);
    void append_process_chunk(const std::string& task, const std::string& backend, std::string_view chunk);
    void scroll_logs(int delta);
    void add_log_secret(std::string secret);
    void set_log_sink(std::string path);
    std::string localized(MessageId id) const;
    void finish_success();
    void finish_failure(std::string error);
    InstallerSnapshot snapshot() const;

private:
    mutable std::mutex mutex_;
    InstallerSnapshot state_;
    Language language_;
    std::shared_ptr<EventLog> event_log_;
    std::unordered_map<std::string, ChunkDecoder> decoders_;
};

using TuiInstallAction = std::function<std::pair<bool, std::string>(
    const std::string& cdk, InstallerViewModel& model, const std::function<void()>& wake)>;

bool configure_utf8_terminal();
std::string task_marker(TaskStatus status);
void apply_workflow_progress(InstallerViewModel& model, const std::string& task, const std::string& detail);
ftxui::Element render_setup_view(const InstallerSnapshot& snapshot, Language language,
                                 ftxui::Element controls, int width, int height);
ftxui::Element render_installation_view(const InstallerSnapshot& snapshot, Language language,
                                        ftxui::Element footer, int width, int height);
int run_unattended(const std::string& configured_cdk, const TuiInstallAction& install);
int run_tui(bool setup_required, const std::string& configured_cdk, const TuiInstallAction& install, bool auto_exit = false);

std::string redact_cdk(const std::string& cdk);

}  // namespace baas_installer
