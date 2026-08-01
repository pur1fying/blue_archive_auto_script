#pragma once

#include "baas_installer/config.hpp"
#include "baas_installer/paths.hpp"
#include "baas_installer/transaction.hpp"

#include <functional>
#include <string>

namespace baas_installer {

struct WorkflowServices {
    std::function<bool(InstallTransaction&, std::string&)> prepare_main;
    std::function<bool(InstallTransaction&, std::string&)> prepare_ocr;
    std::function<void()> on_prepared;
    std::function<bool(const InstallPaths&, const InstallerConfig&, std::string&)> verify_deployment;
    std::function<bool(const InstallPaths&, const InstallerConfig&, std::string&)> sync_uv;
    std::function<void(const std::string&, const std::string&)> progress;
};

struct WorkflowResult { bool success{}; std::string error; };

// Downloads are prepared concurrently.  Nothing is placed in the live tree
// until both preparation functions succeed; main is committed before OCR.
WorkflowResult install_or_update(InstallerConfig& config, const InstallPaths& paths, const WorkflowServices& services);

}  // namespace baas_installer
