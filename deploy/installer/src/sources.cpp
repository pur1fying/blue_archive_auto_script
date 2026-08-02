#include "baas_installer/sources.hpp"

#include <algorithm>
#include <fstream>
#include <future>
#include <iomanip>
#include <sstream>

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
        ranked.push_back({candidate, latency, 0});
    }
    std::stable_sort(ranked.begin(), ranked.end(), [](const RankedSource& a, const RankedSource& b) {
        if (a.latency_ms < 0) return false;
        if (b.latency_ms < 0) return true;
        return a.latency_ms < b.latency_ms;
    });
    return ranked;
}

namespace {

// The cache is deliberately small and dependency-free: URL lines are quoted
// JSON strings, so paths survive moving a portable installation unchanged.
std::string quoted(const std::string& value) {
    std::ostringstream out;
    out << std::quoted(value);
    return out.str();
}

std::string json_field(const std::string& line, const std::string& name) {
    const auto marker = "\"" + name + "\": \"";
    const auto begin = line.find(marker);
    if (begin == std::string::npos) return {};
    const auto start = begin + marker.size();
    const auto end = line.find('"', start);
    return end == std::string::npos ? std::string{} : line.substr(start, end - start);
}

long long integer_field(const std::string& line, const std::string& name) {
    const auto marker = "\"" + name + "\": ";
    const auto begin = line.find(marker);
    if (begin == std::string::npos) return 0;
    try { return std::stoll(line.substr(begin + marker.size())); } catch (...) { return 0; }
}

}  // namespace

std::vector<RankedSource> load_source_ranking(const std::filesystem::path& path) {
    std::ifstream input(path);
    std::vector<RankedSource> result;
    std::string line;
    while (std::getline(input, line)) {
        const auto url = json_field(line, "url");
        if (!url.empty()) result.push_back({url, integer_field(line, "latency_ms"), static_cast<unsigned int>(integer_field(line, "failures"))});
    }
    return result;
}

void save_source_ranking(const std::filesystem::path& path, const std::vector<RankedSource>& ranking) {
    std::filesystem::create_directories(path.parent_path());
    const auto temporary = path.string() + ".new";
    std::ofstream output(temporary, std::ios::trunc);
    output << "[\n";
    for (std::size_t index = 0; index < ranking.size(); ++index) {
        const auto& item = ranking[index];
        output << "  {\"url\": " << quoted(item.url) << ", \"latency_ms\": " << item.latency_ms
               << ", \"failures\": " << item.failures << "}" << (index + 1 == ranking.size() ? "\n" : ",\n");
    }
    output << "]\n";
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
