#include "baas_installer/logging.hpp"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <regex>

namespace baas_installer {
namespace {

void replace_all(std::string& value, const std::string& needle, const std::string& replacement) {
    if (needle.empty()) return;
    for (std::size_t position = 0; (position = value.find(needle, position)) != std::string::npos;) {
        value.replace(position, needle.size(), replacement);
        position += replacement.size();
    }
}

std::string regex_redact(std::string value, const std::regex& pattern, const std::string& replacement) {
    return std::regex_replace(value, pattern, replacement);
}

std::string normalized_terminal_line(std::string value) {
    while (!value.empty() && (value.back() == ' ' || value.back() == '\t')) value.pop_back();
    static const std::vector<std::string> spinner_frames{
        "⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏",
    };
    for (const auto& frame : spinner_frames) {
        if (value.rfind(frame, 0) != 0) continue;
        value.erase(0, frame.size());
        while (!value.empty() && value.front() == ' ') value.erase(value.begin());
        break;
    }
    return value;
}

}  // namespace

void ChunkDecoder::erase_last_codepoint() {
    if (current_.empty()) return;
    auto position = current_.size() - 1;
    while (position > 0 && (static_cast<unsigned char>(current_[position]) & 0xc0U) == 0x80U) --position;
    current_.erase(position);
}

std::vector<DecodedLine> ChunkDecoder::consume(const std::string_view chunk) {
    std::vector<DecodedLine> output;
    for (const unsigned char byte : chunk) {
        switch (escape_state_) {
            case EscapeState::Escape:
                escape_state_ = byte == '[' ? EscapeState::Csi : byte == ']' ? EscapeState::Osc : EscapeState::Normal;
                continue;
            case EscapeState::Csi:
                if (byte >= 0x40U && byte <= 0x7eU) {
                    const bool line_repaint = byte == 'K' || byte == 'G' || byte == 'D' ||
                                              byte == 'A' || byte == 'H' || byte == 'f';
                    if (line_repaint && !current_.empty()) {
                        output.push_back({normalized_terminal_line(current_), true});
                        current_.clear();
                        after_line_erase_ = true;
                    }
                    escape_state_ = EscapeState::Normal;
                }
                continue;
            case EscapeState::Osc:
                if (byte == 0x07U) escape_state_ = EscapeState::Normal;
                else if (byte == 0x1bU) escape_state_ = EscapeState::OscEscape;
                continue;
            case EscapeState::OscEscape:
                escape_state_ = byte == '\\' ? EscapeState::Normal : EscapeState::Osc;
                continue;
            case EscapeState::Normal: break;
        }
        if (byte == 0x1bU) {
            escape_state_ = EscapeState::Escape;
        } else if (byte == '\r') {
            output.push_back({normalized_terminal_line(current_), true});
            current_.clear();
            after_carriage_return_ = true;
            after_line_erase_ = false;
        } else if (byte == '\n') {
            if (!after_carriage_return_ || !current_.empty()) {
                output.push_back({normalized_terminal_line(current_), after_line_erase_});
            }
            current_.clear();
            after_carriage_return_ = false;
            after_line_erase_ = false;
        } else if (byte == '\b') {
            erase_last_codepoint();
        } else if (byte >= 0x20U || byte >= 0x80U) {
            current_.push_back(static_cast<char>(byte));
            after_carriage_return_ = false;
        }
    }
    return output;
}

std::vector<DecodedLine> ChunkDecoder::finish() {
    std::vector<DecodedLine> output;
    if (!current_.empty()) output.push_back({normalized_terminal_line(std::move(current_)), false});
    current_.clear();
    after_carriage_return_ = false;
    after_line_erase_ = false;
    escape_state_ = EscapeState::Normal;
    return output;
}

void Redactor::add_secret(std::string secret) {
    if (!secret.empty() && std::find(secrets_.begin(), secrets_.end(), secret) == secrets_.end()) {
        secrets_.push_back(std::move(secret));
    }
}

std::string Redactor::redact(const std::string_view text) const {
    std::string value(text);
    for (const auto& secret : secrets_) replace_all(value, secret, "[REDACTED]");
    static const std::regex cdk(R"(([?&]cdk=)[^&\s]+)", std::regex::icase);
    static const std::regex authorization(R"((authorization\s*:\s*)[^\r\n]+)", std::regex::icase);
    static const std::regex cookie(R"((cookie\s*:\s*)[^\r\n]+)", std::regex::icase);
    value = regex_redact(std::move(value), cdk, "$1[REDACTED]");
    value = regex_redact(std::move(value), authorization, "$1[REDACTED]");
    return regex_redact(std::move(value), cookie, "$1[REDACTED]");
}

std::string severity_name(const LogSeverity severity) {
    switch (severity) {
        case LogSeverity::Debug: return "debug";
        case LogSeverity::Info: return "info";
        case LogSeverity::Warning: return "warning";
        case LogSeverity::Error: return "error";
    }
    return "info";
}

std::string format_log_event(const LogEvent& event) {
    return "[" + event.timestamp + "][" + event.task + "][" + event.backend + "][" +
           severity_name(event.severity) + "] " + event.text;
}

void EventLog::add_secret(std::string secret) {
    std::scoped_lock lock(mutex_);
    redactor_.add_secret(std::move(secret));
}

void EventLog::set_sink(std::filesystem::path path) {
    std::scoped_lock lock(mutex_);
    sink_ = std::move(path);
}

void EventLog::publish(LogEvent event) {
    std::scoped_lock lock(mutex_);
    event.text = redactor_.redact(event.text);
    bool replaced = false;
    if (event.replace_last) {
        const auto existing = std::find_if(events_.rbegin(), events_.rend(), [&](const LogEvent& candidate) {
            return candidate.task == event.task && candidate.backend == event.backend;
        });
        if (existing != events_.rend()) {
            *existing = event;
            replaced = true;
        }
    }
    if (!replaced) events_.push_back(event);
    if (sink_.empty()) return;
    std::error_code ignored;
    std::filesystem::create_directories(sink_.parent_path(), ignored);
    std::ofstream output(sink_, std::ios::binary | std::ios::app);
    output << format_log_event(event) << '\n';
}

std::vector<LogEvent> EventLog::snapshot() const {
    std::scoped_lock lock(mutex_);
    return events_;
}

}  // namespace baas_installer
