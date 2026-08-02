#include "baas_installer/workflow.hpp"

#include <future>
#include <stdexcept>

namespace baas_installer {
namespace {
void emit(const WorkflowServices& services, const std::string& task, const std::string& detail) {
    if (services.progress) services.progress(task, detail);
}
}

WorkflowResult install_or_update(InstallerConfig& config, const InstallPaths& paths, const WorkflowServices& services) {
    if (!services.prepare_main || !services.prepare_ocr || !services.verify_deployment || !services.sync_uv) {
        return {false, "installer services are incomplete"};
    }
    InstallTransaction transaction(paths);
    emit(services, "main", "downloading");
    auto main = std::async(std::launch::async, [&] { std::string error; return std::pair{services.prepare_main(transaction, error), error}; });
    emit(services, "ocr", "downloading");
    auto ocr = std::async(std::launch::async, [&] { std::string error; return std::pair{services.prepare_ocr(transaction, error), error}; });
    const auto main_result = main.get();
    const auto ocr_result = ocr.get();
    if (!main_result.first || !ocr_result.first) {
        const auto& error = !main_result.first ? main_result.second : ocr_result.second;
        emit(services, "deployment", "preparation failed; no live files changed");
        return {false, error.empty() ? "repository preparation failed" : error};
    }
    if (services.on_prepared) services.on_prepared();
    try {
        emit(services, "main", "ready; waiting for parallel task");
        emit(services, "deployment", "deploying main repository");
        transaction.deploy_main();
        emit(services, "deployment", "deploying OCR repository");
        transaction.deploy_ocr();
        std::string error;
        emit(services, "verify", "verifying deployment");
        if (!services.verify_deployment(paths, config, error)) throw std::runtime_error(error.empty() ? "deployment verification failed" : error);
        emit(services, "verify", "deployment verified");
        transaction.write_ocr_managed_marker();
        emit(services, "uv", "synchronizing dependencies");
        if (!services.sync_uv(paths, config, error)) throw std::runtime_error(error.empty() ? "uv synchronization failed" : error);
        emit(services, "uv", "dependencies synchronized");
        // The configuration is deliberately the final durable state change.
        save_config_atomic(config, paths);
        transaction.commit();
        emit(services, "complete", "installation completed");
        return {true, {}};
    } catch (const std::exception& error) {
        transaction.rollback();
        emit(services, "deployment", "rolled back");
        return {false, error.what()};
    }
}

}  // namespace baas_installer
