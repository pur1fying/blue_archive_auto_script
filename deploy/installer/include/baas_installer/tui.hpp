#pragma once

#include <functional>
#include <map>
#include <mutex>
#include <string>
#include <utility>
#include <vector>

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
};

class InstallerViewModel {
public:
    explicit InstallerViewModel(bool setup_required);
    void begin_install();
    void update_task(const std::string& id, TaskStatus status, std::string detail, double progress = -1.0);
    void finish_success();
    void finish_failure(std::string error);
    InstallerSnapshot snapshot() const;

private:
    mutable std::mutex mutex_;
    InstallerSnapshot state_;
};

using TuiInstallAction = std::function<std::pair<bool, std::string>(
    const std::string& cdk, InstallerViewModel& model, const std::function<void()>& wake)>;

bool configure_utf8_terminal();
void apply_workflow_progress(InstallerViewModel& model, const std::string& task, const std::string& detail);
int run_unattended(const std::string& configured_cdk, const TuiInstallAction& install);
int run_tui(bool setup_required, const std::string& configured_cdk, const TuiInstallAction& install, bool auto_exit = false);

std::string redact_cdk(const std::string& cdk);

}  // namespace baas_installer
