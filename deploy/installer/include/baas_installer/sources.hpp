#pragma once

#include "baas_installer/config.hpp"

#include <filesystem>
#include <functional>
#include <string>
#include <vector>

namespace baas_installer {

enum class SourceKind { MainGit, OcrGit, Uv, Cpython, Pypi };

std::vector<std::string> default_sources(SourceKind kind, const InstallerConfig& config);

struct RankedSource {
    std::string url;
    long long latency_ms{};
    unsigned int failures{};
    std::string commit;
    bool preferred{};
    bool available{true};
};

// Probe callbacks return a non-negative latency on success, or -1 when the
// probe cannot verify the resource. Failed probes remain at the end of the
// ranking so an advisory speed test can never suppress a real transfer attempt.
using SourceProbe = std::function<long long(const std::string&)>;

std::vector<RankedSource> rank_sources(
    const std::vector<std::string>& candidates, const SourceProbe& probe);
std::string source_kind_name(SourceKind kind);
std::vector<RankedSource> load_source_ranking(
    const std::filesystem::path& path, SourceKind kind, const std::vector<std::string>& candidates);
void save_source_ranking(
    const std::filesystem::path& path, SourceKind kind, const std::vector<RankedSource>& ranking);
void record_source_failure(std::vector<RankedSource>& ranking, const std::string& url);

}  // namespace baas_installer
