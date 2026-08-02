#include "baas_installer/sources.hpp"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <filesystem>
#include <iostream>
#include <thread>

int main() {
    baas_installer::InstallerConfig config;
    config.main_sources = {"https://private.example/main.git"};
    config.ocr_sources = {"https://private.example/ocr.git"};
    config.pypi_sources = {"https://private.example/simple"};
    const auto urls = baas_installer::default_sources(baas_installer::SourceKind::MainGit, config);
    const auto retired = std::any_of(urls.begin(), urls.end(), [](const auto& url) {
        return url.find("baas-cdn.kiramei.workers.dev") != std::string::npos ||
               url.find("Kiramei/baas-dev") != std::string::npos;
    });
    if (retired) { std::cerr << "retired source included\n"; return 1; }
    if (urls.empty() || urls.front() != "https://private.example/main.git" ||
        urls[1] != "https://github.com/pur1fying/blue_archive_auto_script.git") {
        std::cerr << "unexpected main source order\n"; return 1;
    }
    const auto ocr_urls = baas_installer::default_sources(baas_installer::SourceKind::OcrGit, config);
    if (ocr_urls.empty() || ocr_urls.front() != "https://private.example/ocr.git") {
        std::cerr << "configured OCR source was not preferred\n"; return 1;
    }
    const auto uv_sources = baas_installer::default_sources(baas_installer::SourceKind::Uv, config);
    const auto cpython_sources = baas_installer::default_sources(baas_installer::SourceKind::Cpython, config);
    const auto pypi_sources = baas_installer::default_sources(baas_installer::SourceKind::Pypi, config);
    if (pypi_sources.empty() || pypi_sources.front() != "https://private.example/simple") {
        std::cerr << "configured PyPI source was not preferred\n"; return 1;
    }
    const auto contains_retired = [](const auto& list) {
        return std::any_of(list.begin(), list.end(), [](const auto& url) {
            return url.find("baas-cdn.kiramei.workers.dev") != std::string::npos;
        });
    };
    if (uv_sources.size() < 5 || cpython_sources.size() < 5 || pypi_sources.size() < 5 ||
        contains_retired(uv_sources) || contains_retired(cpython_sources)) {
        std::cerr << "environment fallback source set is incomplete\n"; return 1;
    }
    if (std::find(uv_sources.begin(), uv_sources.end(),
                  "https://cnb.cool/kiramei/baas-tauri/-/releases/download/uv-down") == uv_sources.end() ||
        std::find(cpython_sources.begin(), cpython_sources.end(),
                  "https://cnb.cool/kiramei/baas-tauri/-/releases/download") == cpython_sources.end()) {
        std::cerr << "CNB uv/CPython fallback sources are missing\n";
        return 1;
    }

    const auto ranked = baas_installer::rank_sources(urls, [](const std::string& url) {
        if (url.find("gitee") != std::string::npos) return 8LL;
        if (url == "https://github.com/pur1fying/blue_archive_auto_script.git") return 20LL;
        return -1LL;
    });
    if (ranked.size() != urls.size() || ranked.front().latency_ms != 8 ||
        ranked[1].latency_ms != 20 || ranked[2].url != "https://private.example/main.git" ||
        ranked[2].latency_ms != -1) {
        std::cerr << "source probe ranking failed\n"; return 1;
    }

    const auto all_failed = baas_installer::rank_sources({"first", "second", "third"},
                                                          [](const std::string&) { return -1LL; });
    if (all_failed.size() != 3 || all_failed[0].url != "first" || all_failed[1].url != "second" ||
        all_failed[2].url != "third") {
        std::cerr << "failed probes must remain available for real transfer attempts\n";
        return 1;
    }

    std::atomic<int> active{0};
    std::atomic<int> max_active{0};
    const auto concurrent = baas_installer::rank_sources({"slow", "fast", "failed"}, [&](const std::string& url) {
        const int current = ++active;
        auto maximum = max_active.load();
        while (current > maximum && !max_active.compare_exchange_weak(maximum, current)) {}
        std::this_thread::sleep_for(std::chrono::milliseconds(40));
        --active;
        if (url == "failed") return -1LL;
        return url == "fast" ? 5LL : 25LL;
    });
    if (max_active.load() <= 1 || concurrent.size() != 3 || concurrent.front().url != "fast" ||
        concurrent[1].url != "slow" || concurrent.back().url != "failed") {
        std::cerr << "source probes must run concurrently and retain latency order\n";
        return 1;
    }
    const auto cache_root = std::filesystem::temp_directory_path() / "baas-installer-source-ranking-root";
    const auto moved_cache_root = std::filesystem::temp_directory_path() / "baas-installer-source-ranking-moved";
    std::filesystem::remove_all(cache_root);
    std::filesystem::remove_all(moved_cache_root);
    const auto cache = cache_root / ".baas-installer" / "source-ranking-v1.json";
    auto main_ranking = ranked;
    main_ranking.front().preferred = true;
    main_ranking.front().commit = "0123456789012345678901234567890123456789";
    const std::vector<baas_installer::RankedSource> ocr_ranking{
        {"ocr-fast", 4, 0, "abcdefabcdefabcdefabcdefabcdefabcdefabcd", true, true}};
    std::thread save_main([&] {
        baas_installer::save_source_ranking(cache, baas_installer::SourceKind::MainGit, main_ranking);
    });
    std::thread save_ocr([&] {
        baas_installer::save_source_ranking(cache, baas_installer::SourceKind::OcrGit, ocr_ranking);
    });
    save_main.join();
    save_ocr.join();
    std::filesystem::rename(cache_root, moved_cache_root);
    const auto moved_cache = moved_cache_root / ".baas-installer" / "source-ranking-v1.json";
    auto restored = baas_installer::load_source_ranking(
        moved_cache, baas_installer::SourceKind::MainGit,
        [&] { std::vector<std::string> values; for (const auto& item : main_ranking) values.push_back(item.url); return values; }());
    const auto restored_ocr = baas_installer::load_source_ranking(
        moved_cache, baas_installer::SourceKind::OcrGit, {"ocr-fast"});
    baas_installer::record_source_failure(restored, ranked.front().url);
    std::error_code ignored;
    const auto invalidated = baas_installer::load_source_ranking(
        moved_cache, baas_installer::SourceKind::MainGit, {"changed-source"});
    std::filesystem::remove_all(moved_cache_root, ignored);
    if (restored.size() != ranked.size() || restored.front().url != ranked.front().url ||
        restored.front().failures != 1 || !restored.front().preferred || restored.front().commit.empty() ||
        restored_ocr.size() != 1 || restored_ocr.front().url != "ocr-fast" || !invalidated.empty()) {
        std::cerr << "source ranking persistence failed\n"; return 1;
    }
    return 0;
}
