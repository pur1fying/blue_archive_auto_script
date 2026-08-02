#include "baas_installer/sources.hpp"

#include <algorithm>
#include <filesystem>
#include <iostream>

int main() {
    baas_installer::InstallerConfig config;
    const auto urls = baas_installer::default_sources(baas_installer::SourceKind::MainGit, config);
    const auto retired = std::any_of(urls.begin(), urls.end(), [](const auto& url) {
        return url.find("baas-cdn.kiramei.workers.dev") != std::string::npos ||
               url.find("Kiramei/baas-dev") != std::string::npos;
    });
    if (retired) { std::cerr << "retired source included\n"; return 1; }
    if (urls.empty() || urls.front() != "https://github.com/pur1fying/blue_archive_auto_script.git") {
        std::cerr << "unexpected main source order\n"; return 1;
    }
    const auto uv_sources = baas_installer::default_sources(baas_installer::SourceKind::Uv, config);
    const auto cpython_sources = baas_installer::default_sources(baas_installer::SourceKind::Cpython, config);
    const auto pypi_sources = baas_installer::default_sources(baas_installer::SourceKind::Pypi, config);
    const auto contains_retired = [](const auto& list) {
        return std::any_of(list.begin(), list.end(), [](const auto& url) {
            return url.find("baas-cdn.kiramei.workers.dev") != std::string::npos;
        });
    };
    if (uv_sources.size() < 5 || cpython_sources.size() < 5 || pypi_sources.size() < 5 ||
        contains_retired(uv_sources) || contains_retired(cpython_sources)) {
        std::cerr << "environment fallback source set is incomplete\n"; return 1;
    }

    const auto ranked = baas_installer::rank_sources(urls, [](const std::string& url) {
        if (url.find("gitee") != std::string::npos) return 8LL;
        if (url == "https://github.com/pur1fying/blue_archive_auto_script.git") return 20LL;
        return -1LL;
    });
    if (ranked.size() != 2 || ranked.front().latency_ms != 8) {
        std::cerr << "source probe ranking failed\n"; return 1;
    }
    const auto cache = std::filesystem::temp_directory_path() / "baas-installer-source-ranking.json";
    baas_installer::save_source_ranking(cache, ranked);
    auto restored = baas_installer::load_source_ranking(cache);
    baas_installer::record_source_failure(restored, ranked.front().url);
    std::error_code ignored;
    std::filesystem::remove(cache, ignored);
    if (restored.size() != ranked.size() || restored.front().url != ranked.front().url || restored.front().failures != 1) {
        std::cerr << "source ranking persistence failed\n"; return 1;
    }
    return 0;
}
