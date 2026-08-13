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
    const auto original_config = config;
    try {
    InstallTransaction transaction(paths);
    try {
        save_config_atomic(config, paths);
    } catch (const std::exception& error) {
        return {false, error.what()};
    }
    emit(services, "main", "checking");
    auto main = std::async(std::launch::async, [&] { return services.prepare_main(transaction); });
    emit(services, "ocr", "checking");
    auto ocr = std::async(std::launch::async, [&] { return services.prepare_ocr(transaction); });
    const auto main_result = main.get();
    const auto ocr_result = ocr.get();
    if (!main_result.success || !ocr_result.success) {
        const auto& error = !main_result.success ? main_result.error : ocr_result.error;
        emit(services, "deployment", "preparation failed; no live files changed");
        return {false, error.empty() ? "repository preparation failed" : error};
    }
    try {
        emit(services, "main", "ready; waiting for parallel task");
        std::string error;
        if (main_result.mode != RepositoryMode::Unchanged) {
            emit(services, "deployment", "deploying main repository");
            if (!main_result.apply || !main_result.apply(transaction, error)) {
                throw std::runtime_error(error.empty() ? "main repository apply failed" : error);
            }
        } else {
            emit(services, "main", "already current");
        }
        if (ocr_result.mode != RepositoryMode::Unchanged) {
            emit(services, "deployment", "deploying OCR repository");
            if (!ocr_result.apply || !ocr_result.apply(transaction, error)) {
                throw std::runtime_error(error.empty() ? "OCR repository apply failed" : error);
            }
        } else {
            emit(services, "ocr", "already current");
        }
        emit(services, "verify", "verifying deployment");
        if (!services.verify_deployment(paths, config, error)) throw std::runtime_error(error.empty() ? "deployment verification failed" : error);
        emit(services, "verify", "deployment verified");
        transaction.write_ocr_managed_marker(ocr_result.revision, ocr_result.version);
        emit(services, "uv", "synchronizing dependencies");
        if (!services.sync_uv(paths, config, error)) throw std::runtime_error(error.empty() ? "uv synchronization failed" : error);
        emit(services, "uv", "dependencies synchronized");
        // The configuration is deliberately the final durable state change.
        config.main_sha = main_result.version;
        config.ocr_sha = ocr_result.version;
        transaction.prepare_commit();
        save_config_atomic(config, paths);
        const auto maintenance_error = transaction.commit();
        if (!maintenance_error.empty()) {
            emit(services, "deployment", "installation committed; maintenance will be retried");
            return {false, maintenance_error};
        }
        emit(services, "complete", "installation completed");
        return {true, {}};
    } catch (const std::exception& error) {
        config = original_config;
        transaction.rollback();
        std::string message = error.what();
        try {
            save_config_atomic(config, paths);
        } catch (const std::exception& restore_error) {
            message += "; setup.toml restore failed: ";
            message += restore_error.what();
        }
        emit(services, "deployment", "rolled back");
        return {false, message};
    }
    } catch (const std::exception& error) {
        return {false, error.what()};
    }
}

}  // namespace baas_installer
