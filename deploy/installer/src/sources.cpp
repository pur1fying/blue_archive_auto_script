#include "baas_installer/sources.hpp"

#include <algorithm>
#include <fstream>
#include <future>
#include <mutex>

#include <nlohmann/json.hpp>

namespace baas_installer {

std::vector<std::string> default_sources(const SourceKind kind, const InstallerConfig& config) {
    std::vector<std::string> result;
    const auto add = [&](const std::vector<std::string>& sources) {
        for (const auto& source : sources) {
            if (!source.empty() && std::find(result.begin(), result.end(), source) == result.end()) result.push_back(source);
        }
    };
    switch (kind) {
        case SourceKind::MainGit:
            add(config.main_sources);
            add({
                "https://github.com/pur1fying/blue_archive_auto_script.git",
                "https://gitee.com/pur1fy/blue_archive_auto_script.git",
                "https://gitcode.com/m0_74686738/blue_archive_auto_script.git",
                "https://v4.gh-proxy.org/https://github.com/pur1fying/blue_archive_auto_script.git",
                "https://v6.gh-proxy.org/https://github.com/pur1fying/blue_archive_auto_script.git",
                "https://cdn.gh-proxy.org/https://github.com/pur1fying/blue_archive_auto_script.git",
                "https://gh-proxy.org/https://github.com/pur1fying/blue_archive_auto_script.git",
                "https://gh.sevencdn.com/https://github.com/pur1fying/blue_archive_auto_script.git",
                "https://githubfast.com/pur1fying/blue_archive_auto_script.git",
            });
            break;
        case SourceKind::OcrGit:
            add(config.ocr_sources);
            add({
                "https://github.com/pur1fying/BAAS_Cpp_prebuild.git",
                "https://gitee.com/pur1fy/baas_-cpp_prebuild.git",
                "https://v4.gh-proxy.org/https://github.com/pur1fying/BAAS_Cpp_prebuild.git",
                "https://v6.gh-proxy.org/https://github.com/pur1fying/BAAS_Cpp_prebuild.git",
                "https://cdn.gh-proxy.org/https://github.com/pur1fying/BAAS_Cpp_prebuild.git",
                "https://gh-proxy.org/https://github.com/pur1fying/BAAS_Cpp_prebuild.git",
                "https://gh.sevencdn.com/https://github.com/pur1fying/BAAS_Cpp_prebuild.git",
                "https://githubfast.com/pur1fying/BAAS_Cpp_prebuild.git",
            });
            break;
        case SourceKind::Pypi:
            add(config.pypi_sources);
            add({
                "https://mirrors.aliyun.com/pypi/simple", "https://pypi.doubanio.com/simple",
                "https://mirrors.huaweicloud.com/repository/pypi/simple", "https://mirrors.cloud.tencent.com/pypi/simple",
                "https://mirrors.163.com/pypi/simple", "https://pypi.tuna.tsinghua.edu.cn/simple",
                "https://mirrors.ustc.edu.cn/pypi/web/simple", "https://pypi.org/simple",
            });
            break;
        case SourceKind::Uv:
            add({
                "https://cnb.cool/kiramei/baas-tauri/-/releases/download/uv-down",
                "https://github.com/Kiramei/baas-tauri/releases/download/uv-down",
                "https://gitee.com/kiramei/blue_archive_auto_script_assets/releases/download/UVDownload",
                "https://v4.gh-proxy.org/https://github.com/Kiramei/baas-tauri/releases/download/uv-down",
                "https://v6.gh-proxy.org/https://github.com/Kiramei/baas-tauri/releases/download/uv-down",
                "https://cdn.gh-proxy.org/https://github.com/Kiramei/baas-tauri/releases/download/uv-down",
                "https://gh-proxy.org/https://github.com/Kiramei/baas-tauri/releases/download/uv-down",
                "https://gh.sevencdn.com/https://github.com/Kiramei/baas-tauri/releases/download/uv-down",
            });
            break;
        case SourceKind::Cpython:
            add({
                "https://cnb.cool/kiramei/baas-tauri/-/releases/download",
                "https://github.com/Kiramei/baas-tauri/releases/download",
                "https://gitee.com/kiramei/blue_archive_auto_script_assets/releases/download",
                "https://v4.gh-proxy.org/https://github.com/Kiramei/baas-tauri/releases/download",
                "https://v6.gh-proxy.org/https://github.com/Kiramei/baas-tauri/releases/download",
                "https://cdn.gh-proxy.org/https://github.com/Kiramei/baas-tauri/releases/download",
                "https://gh-proxy.org/https://github.com/Kiramei/baas-tauri/releases/download",
                "https://gh.sevencdn.com/https://github.com/Kiramei/baas-tauri/releases/download",
            });
            break;
    }
    return result;
}

std::vector<RankedSource> rank_sources(
    const std::vector<std::string>& candidates, const SourceProbe& probe) {
    std::vector<RankedSource> ranked;
    ranked.reserve(candidates.size());
    std::vector<std::future<long long>> probes;
    probes.reserve(candidates.size());
    for (const auto& candidate : candidates) {
        probes.push_back(std::async(std::launch::async, [probe, candidate] {
            try {
                return probe(candidate);
            } catch (...) {
                return -1LL;
            }
        }));
    }
    for (std::size_t index = 0; index < candidates.size(); ++index) {
        const auto latency = probes[index].get();
        const auto& candidate = candidates[index];
        ranked.push_back({candidate, latency, 0, {}, false, latency >= 0});
    }
    std::stable_sort(ranked.begin(), ranked.end(), [](const RankedSource& a, const RankedSource& b) {
        if (a.latency_ms < 0) return false;
        if (b.latency_ms < 0) return true;
        return a.latency_ms < b.latency_ms;
    });
    return ranked;
}

namespace {

std::mutex ranking_cache_mutex;

std::vector<std::string> sorted_urls(const std::vector<std::string>& values) {
    auto result = values;
    std::sort(result.begin(), result.end());
    return result;
}

std::vector<std::string> sorted_urls(const std::vector<RankedSource>& values) {
    std::vector<std::string> result;
    result.reserve(values.size());
    for (const auto& value : values) result.push_back(value.url);
    return sorted_urls(result);
}

nlohmann::json read_cache(const std::filesystem::path& path) {
    std::ifstream input(path);
    if (!input) return nlohmann::json{{"schema_version", 1}, {"categories", nlohmann::json::object()}};
    try {
        auto value = nlohmann::json::parse(input);
        if (value.value("schema_version", 0) != 1 || !value.contains("categories") ||
            !value["categories"].is_object()) throw std::runtime_error("unsupported source cache");
        return value;
    } catch (...) {
        return nlohmann::json{{"schema_version", 1}, {"categories", nlohmann::json::object()}};
    }
}

}  // namespace

std::string source_kind_name(const SourceKind kind) {
    switch (kind) {
        case SourceKind::MainGit: return "main_git";
        case SourceKind::OcrGit: return "ocr_git";
        case SourceKind::Uv: return "uv";
        case SourceKind::Cpython: return "cpython";
        case SourceKind::Pypi: return "pypi";
    }
    return "unknown";
}

std::vector<RankedSource> load_source_ranking(
    const std::filesystem::path& path, const SourceKind kind, const std::vector<std::string>& candidates) {
    std::scoped_lock lock(ranking_cache_mutex);
    const auto cache = read_cache(path);
    const auto name = source_kind_name(kind);
    if (!cache["categories"].contains(name)) return {};
    const auto& category = cache["categories"][name];
    if (!category.contains("candidates") || !category["candidates"].is_array() ||
        sorted_urls(category["candidates"].get<std::vector<std::string>>()) != sorted_urls(candidates) ||
        !category.contains("ranking") || !category["ranking"].is_array()) return {};
    std::vector<RankedSource> result;
    try {
        for (const auto& item : category["ranking"]) {
            const auto url = item.value("url", std::string{});
            if (url.empty()) continue;
            result.push_back({url, item.value("latency_ms", -1LL), item.value("failures", 0U),
                              item.value("commit", std::string{}), item.value("preferred", false),
                              item.value("available", false)});
        }
    } catch (...) {
        return {};
    }
    return result;
}

void save_source_ranking(
    const std::filesystem::path& path, const SourceKind kind, const std::vector<RankedSource>& ranking) {
    std::scoped_lock lock(ranking_cache_mutex);
    std::filesystem::create_directories(path.parent_path());
    auto cache = read_cache(path);
    nlohmann::json values = nlohmann::json::array();
    for (const auto& item : ranking) {
        values.push_back({{"url", item.url}, {"latency_ms", item.latency_ms}, {"failures", item.failures},
                          {"commit", item.commit}, {"preferred", item.preferred}, {"available", item.available}});
    }
    cache["categories"][source_kind_name(kind)] = {
        {"candidates", sorted_urls(ranking)}, {"ranking", std::move(values)}};
    auto temporary = path;
    temporary += ".new";
    std::ofstream output(temporary, std::ios::trunc);
    output << cache.dump(2) << '\n';
    output.close();
    std::error_code error;
    std::filesystem::rename(temporary, path, error);
    if (error) {
        std::filesystem::remove(path, error);
        error.clear();
        std::filesystem::rename(temporary, path, error);
    }
}

void record_source_failure(std::vector<RankedSource>& ranking, const std::string& url) {
    for (auto& item : ranking) {
        if (item.url == url) {
            ++item.failures;
            return;
        }
    }
}

}  // namespace baas_installer
