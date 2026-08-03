#pragma once

#include "baas_installer/paths.hpp"

#include <filesystem>
#include <functional>
#include <cstdint>
#include <vector>

namespace baas_installer {

class InstallTransaction {
public:
    explicit InstallTransaction(const InstallPaths& paths);
    ~InstallTransaction();

    [[nodiscard]] const std::filesystem::path& staging_root() const { return staging_root_; }
    [[nodiscard]] std::filesystem::path main_staging_path() const;
    [[nodiscard]] std::filesystem::path ocr_staging_path() const;

    // Call only after both parallel download tasks are completely verified.
    void deploy_main();
    void deploy_ocr();
    void deploy_main_from(const std::filesystem::path& source);
    void deploy_ocr_from(const std::filesystem::path& source);
    void replace_file(const std::filesystem::path& source, const std::filesystem::path& destination);
    void replace_directory(const std::filesystem::path& source, const std::filesystem::path& destination);
    void remove_path(const std::filesystem::path& destination);
    void add_rollback_action(std::function<void()> action);
    void add_commit_action(std::function<void()> action);
    void add_post_commit_action(std::function<void()> action);
    void write_ocr_managed_marker(const std::string& branch, const std::string& commit);
    void prepare_commit();
    // The live files are durable even when a post-commit maintenance action
    // fails. The returned message lets the workflow report that retriable
    // failure without attempting an invalid rollback.
    [[nodiscard]] std::string commit();
    void rollback() noexcept;

private:
    struct Change { std::filesystem::path destination; std::filesystem::path backup; bool existed{}; bool directory{}; };
    void deploy_tree(const std::filesystem::path& source, const std::filesystem::path& destination, bool skip_ocr_bin);
    void journal(const std::string& event) const;
    void release_lock() noexcept;

    InstallPaths paths_;
    std::filesystem::path staging_root_;
    std::vector<Change> changes_;
    std::vector<std::function<void()>> rollback_actions_;
    std::vector<std::function<void()>> commit_actions_;
    std::vector<std::function<void()>> post_commit_actions_;
    std::intptr_t lock_handle_{-1};
    bool commit_prepared_{};
    bool settled_{};
};

}  // namespace baas_installer
