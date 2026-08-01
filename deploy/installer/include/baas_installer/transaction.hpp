#pragma once

#include "baas_installer/paths.hpp"

#include <filesystem>
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
    void write_ocr_managed_marker();
    void commit();
    void rollback() noexcept;

private:
    struct Change { std::filesystem::path destination; std::filesystem::path backup; bool existed{}; };
    void deploy_tree(const std::filesystem::path& source, const std::filesystem::path& destination, bool skip_ocr_bin);
    void journal(const std::string& event) const;

    InstallPaths paths_;
    std::filesystem::path staging_root_;
    std::vector<Change> changes_;
    bool settled_{};
};

}  // namespace baas_installer
