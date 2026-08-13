#include "baas_installer/logging.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>

int main() {
    baas_installer::ChunkDecoder decoder;
    const std::string chinese = "下载";
    auto events = decoder.consume(std::string_view(chinese).substr(0, 2));
    if (!events.empty()) {
        std::cerr << "incomplete UTF-8 must remain buffered\n";
        return 1;
    }
    auto remaining = std::string(std::string_view(chinese).substr(2));
    remaining += "\x1b[31m 12%\x1b[0m\r34%\rabc\bD\n";
    auto more = decoder.consume(remaining);
    events.insert(events.end(), more.begin(), more.end());
    const auto tail = decoder.finish();
    events.insert(events.end(), tail.begin(), tail.end());

    bool saw_progress = false;
    bool saw_line = false;
    for (const auto& event : events) {
        if (event.replace_last && event.text == "34%") saw_progress = true;
        if (!event.replace_last && event.text == "abD") saw_line = true;
        if (event.text.find('\x1b') != std::string::npos) {
            std::cerr << "ANSI escape sequence leaked from decoder\n";
            return 1;
        }
    }
    if (!saw_progress || !saw_line) {
        std::cerr << "carriage return or backspace normalization failed\n";
        return 1;
    }

    baas_installer::ChunkDecoder repaint_decoder;
    const auto repaint = repaint_decoder.consume("10%\x1b[2K20%\x1b[2K30%\n");
    if (repaint.size() != 3 || repaint[0].text != "10%" || !repaint[0].replace_last ||
        repaint[1].text != "20%" || !repaint[1].replace_last ||
        repaint[2].text != "30%" || !repaint[2].replace_last) {
        std::cerr << "ANSI erase-line progress was not normalized as replacement frames\n";
        return 1;
    }
    baas_installer::ChunkDecoder cursor_decoder;
    const auto cursor = cursor_decoder.consume("⠧ package   \x1b[80Ddone\n");
    if (cursor.size() != 2 || cursor[0].text != "package" || !cursor[0].replace_last ||
        cursor[1].text != "done" || !cursor[1].replace_last) {
        std::cerr << "ANSI cursor repaint or spinner normalization failed\n";
        return 1;
    }

    baas_installer::Redactor redactor;
    redactor.add_secret("super-secret-value");
    const auto redacted = redactor.redact(
        "super-secret-value ?cdk=query-value Authorization: Bearer token-value Cookie: sid=cookie-value");
    for (const auto& leaked : {"super-secret-value", "query-value", "token-value", "cookie-value"}) {
        if (redacted.find(leaked) != std::string::npos) {
            std::cerr << "sensitive value was not redacted\n";
            return 1;
        }
    }

    const auto log_path = std::filesystem::temp_directory_path() / "baas-installer-event-log-test.log";
    std::error_code ignored;
    std::filesystem::remove(log_path, ignored);
    baas_installer::EventLog log;
    log.add_secret("disk-secret");
    log.set_sink(log_path);
    log.publish({.timestamp = "12:34:56", .task = "main", .backend = "git-cli",
                 .severity = baas_installer::LogSeverity::Info, .text = "progress disk-secret"});
    const auto snapshot = log.snapshot();
    if (snapshot.size() != 1 || snapshot.front().text.find("disk-secret") != std::string::npos) {
        std::cerr << "memory event log did not redact input\n";
        return 1;
    }
    std::ifstream input(log_path, std::ios::binary);
    const std::string saved{std::istreambuf_iterator<char>(input), {}};
    if (saved.find("[12:34:56][main][git-cli][info]") == std::string::npos ||
        saved.find("disk-secret") != std::string::npos) {
        std::cerr << "disk event log format or redaction failed\n";
        return 1;
    }
    std::filesystem::remove(log_path, ignored);
    return 0;
}
