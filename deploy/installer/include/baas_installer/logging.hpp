#pragma once

#include <filesystem>
#include <mutex>
#include <string>
#include <string_view>
#include <vector>

namespace baas_installer {

enum class LogSeverity { Debug, Info, Warning, Error };

struct DecodedLine {
    std::string text;
    bool replace_last{};
};

class ChunkDecoder {
public:
    std::vector<DecodedLine> consume(std::string_view chunk);
    std::vector<DecodedLine> finish();

private:
    enum class EscapeState { Normal, Escape, Csi, Osc, OscEscape };
    void erase_last_codepoint();
    std::string current_;
    EscapeState escape_state_{EscapeState::Normal};
    bool after_carriage_return_{};
    bool after_line_erase_{};
};

class Redactor {
public:
    void add_secret(std::string secret);
    std::string redact(std::string_view text) const;

private:
    std::vector<std::string> secrets_;
};

struct LogEvent {
    std::string timestamp;
    std::string task;
    std::string backend;
    LogSeverity severity{LogSeverity::Info};
    std::string text;
    bool replace_last{};
};

std::string severity_name(LogSeverity severity);
std::string format_log_event(const LogEvent& event);

class EventLog {
public:
    void add_secret(std::string secret);
    void set_sink(std::filesystem::path path);
    void publish(LogEvent event);
    std::vector<LogEvent> snapshot() const;

private:
    mutable std::mutex mutex_;
    Redactor redactor_;
    std::filesystem::path sink_;
    std::vector<LogEvent> events_;
};

}  // namespace baas_installer
