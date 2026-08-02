#include "baas_installer/config.hpp"
#include "baas_installer/git.hpp"
#include "baas_installer/mirrorchyan.hpp"
#include "baas_installer/paths.hpp"
#include "baas_installer/process.hpp"
#include "baas_installer/sources.hpp"
#include "baas_installer/tui.hpp"
#include "baas_installer/uv_environment.hpp"
#include "baas_installer/workflow.hpp"

#include <filesystem>
#include <iostream>
#include <thread>

namespace {
std::string ocr_revision() {
#ifdef _WIN32
    return "windows-x64";
#elif defined(__APPLE__) && (defined(__aarch64__) || defined(__arm64__))
    return "macos-arm64";
#elif defined(__APPLE__)
    return "macos-x64";
#else
    return "linux-x64";
#endif
}

}

int main(int argc, char* argv[]) {
    baas_installer::configure_utf8_terminal();
    const auto executable = baas_installer::current_executable_path();
    const auto paths = baas_installer::InstallPaths::from_executable(executable);
    if (argc > 1 && std::string(argv[1]) == "--help") {
        std::cout << "BAAS portable installer\n\nOptions:\n  --help       show this help\n  --print-root print the executable-relative install root\n";
        return 0;
    }
    if (argc > 1 && std::string(argv[1]) == "--print-root") { std::cout << paths.root.string() << '\n'; return 0; }
    bool auto_exit = false;
    for (int index = 1; index < argc; ++index) if (std::string(argv[index]) == "--auto-exit") auto_exit = true;
    const bool first_start = !std::filesystem::exists(paths.setup_toml);
    auto config = baas_installer::load_config(paths);
    const auto log_path = paths.logs_dir / "installer.log";
    baas_installer::set_default_process_log(log_path);
    const auto install = [&](const std::string& selected_cdk, baas_installer::InstallerViewModel& model,
                             const std::function<void()>& wake) -> std::pair<bool, std::string> {
        model.set_log_sink(log_path.string());
        model.add_log_secret(selected_cdk);
        model.append_event({{}, "installer", "installer", baas_installer::LogSeverity::Info, "installer started"});
        config.mirrorc_cdk = selected_cdk;
        baas_installer::WorkflowServices services;
        services.progress = [&](const std::string& task, const std::string& detail) {
            baas_installer::apply_workflow_progress(model, task, detail);
            wake();
        };
        const auto prepare_repository = [&](const bool main_repository, baas_installer::InstallTransaction& transaction) {
            const std::string task = main_repository ? "main" : "ocr";
            const auto live = main_repository ? paths.root : paths.root / "core" / "ocr" / "baas_ocr_client" / "bin";
            const auto staging = main_repository ? transaction.main_staging_path() : transaction.ocr_staging_path();
            const auto current_version = main_repository ? config.main_sha : config.ocr_sha;
            const auto sources = baas_installer::default_sources(
                main_repository ? baas_installer::SourceKind::MainGit : baas_installer::SourceKind::OcrGit, config);
            const auto revision = main_repository ? std::string("refs/heads/master") : ocr_revision();
            const baas_installer::ProcessObserver observer = [&](std::string_view, const std::string_view backend,
                                                                  const std::string_view chunk) {
                model.append_process_chunk(task, std::string(backend), chunk);
                wake();
            };

            if (!config.mirrorc_cdk.empty()) {
                std::string mirror_error;
                const auto platform = baas_installer::current_mirror_platform();
                const auto resource = main_repository ? baas_installer::MirrorResource::Main : baas_installer::MirrorResource::Ocr;
                const auto request_url = baas_installer::mirror_latest_url(
                    resource, platform.os, platform.arch, config.mirrorc_cdk, current_version, config.channel);
                auto release = baas_installer::request_mirror_release(request_url, mirror_error);
                if (release.status == baas_installer::CdkStatus::UpToDate) {
                    return baas_installer::PreparedRepository{.success = true,
                        .mode = baas_installer::RepositoryMode::Unchanged, .backend = "mirrorchyan",
                        .version = release.version.empty() ? current_version : release.version};
                }
                if (release.status == baas_installer::CdkStatus::Valid && !current_version.empty()) {
                    release = baas_installer::wait_for_incremental_release(
                        std::move(release),
                        [&] { return baas_installer::request_mirror_release(request_url, mirror_error); },
                        [] { std::this_thread::sleep_for(std::chrono::milliseconds(500)); }, 10);
                }
                if (release.status == baas_installer::CdkStatus::Valid) {
                    const auto prefix = main_repository ? "main" : "ocr";
                    const auto archive = transaction.staging_root() / (std::string(prefix) + "-mirror.zip");
                    const auto extracted = transaction.staging_root() / (std::string(prefix) + "-mirror-unpacked");
                    if (baas_installer::download_mirror_package(release, archive, mirror_error) &&
                        baas_installer::extract_mirror_archive(
                            archive, extracted, mirror_error,
                            [&](const std::string_view chunk) { observer(task, "mirrorchyan", chunk); })) {
                        auto package = baas_installer::inspect_mirror_staging(release, extracted, mirror_error);
                        if (mirror_error.empty()) {
                            const auto mode = package.mode == baas_installer::MirrorPackageMode::Full
                                ? baas_installer::RepositoryMode::Full : baas_installer::RepositoryMode::Incremental;
                            return baas_installer::PreparedRepository{.success = true, .mode = mode,
                                .backend = "mirrorchyan", .version = package.version,
                                .apply = [package = std::move(package), live, main_repository](
                                             baas_installer::InstallTransaction& current, std::string& error) {
                                    try {
                                        current.remove_path(live / ".git");
                                        if (package.mode == baas_installer::MirrorPackageMode::Full) {
                                            if (main_repository) current.deploy_main_from(package.content_root);
                                            else current.deploy_ocr_from(package.content_root);
                                        } else {
                                            for (const auto& path : package.changes.deleted) current.remove_path(live / path);
                                            for (const auto& path : package.changes.added) current.replace_file(package.content_root / path, live / path);
                                            for (const auto& path : package.changes.modified) current.replace_file(package.content_root / path, live / path);
                                        }
                                        return true;
                                    } catch (const std::exception& exception) {
                                        error = exception.what();
                                        return false;
                                    }
                                }};
                        }
                    }
                }
                services.progress(task, "MirrorChyan failed; falling back to Git");
            }

            const auto git = baas_installer::prepare_git_repository(sources, live, staging, revision, observer);
            if (!git.success) return baas_installer::PreparedRepository{.success = false, .backend = "git",
                .error = (main_repository ? "main repository: " : "OCR repository: ") + git.error};
            return baas_installer::PreparedRepository{.success = true, .mode = git.mode,
                .backend = baas_installer::git_backend_name(git.backend), .version = git.commit,
                .apply = [git, live, main_repository, observer](baas_installer::InstallTransaction& current,
                                                                 std::string& error) {
                    if (git.mode == baas_installer::RepositoryMode::Full) {
                        if (main_repository) current.deploy_main();
                        else current.deploy_ocr();
                        return true;
                    }
                    if (git.mode == baas_installer::RepositoryMode::Incremental) {
                        current.add_rollback_action([git, live] {
                            auto restore = git;
                            restore.commit = git.previous_commit;
                            std::string ignored;
                            (void)baas_installer::apply_git_update(restore, live, ignored);
                        });
                        return baas_installer::apply_git_update(git, live, error, observer);
                    }
                    return true;
                }};
        };
        services.prepare_main = [&](auto& transaction) { return prepare_repository(true, transaction); };
        services.prepare_ocr = [&](auto& transaction) { return prepare_repository(false, transaction); };
        services.verify_deployment = [](const baas_installer::InstallPaths& current, const baas_installer::InstallerConfig&, std::string& error) {
        if (!std::filesystem::exists(current.root / "main.py")) { error = "main repository did not contain main.py"; return false; }
        const auto ocr = current.root / "core" / "ocr" / "baas_ocr_client" / "bin";
        if (!std::filesystem::is_directory(ocr) || std::filesystem::is_empty(ocr)) { error = "OCR repository placement is empty"; return false; }
        return true;
        };
        services.sync_uv = [](const baas_installer::InstallPaths& current, const baas_installer::InstallerConfig& settings, std::string& error) {
        return baas_installer::sync_portable_uv(current, settings, error);
        };
        const auto result = baas_installer::install_or_update(config, paths, services);
        if (!result.success) {
            model.append_event({{}, "installer", "installer", baas_installer::LogSeverity::Error, result.error});
            return {false, result.error};
        }
        if (!auto_exit) {
            baas_installer::apply_workflow_progress(model, "launch", "launching BAAS");
            wake();
#ifdef _WIN32
            auto python = paths.venv_dir / "Scripts" / "pythonw.exe";
            if (!std::filesystem::exists(python)) python = paths.venv_dir / "Scripts" / "python.exe";
#else
            auto python = paths.venv_dir / "bin" / "python";
#endif
            if (!config.uses_portable_runtime()) python = config.runtime_path;
            auto environment = baas_installer::make_uv_environment(paths, config).variables;
            environment["VIRTUAL_ENV"] = paths.venv_dir.string();
            if (!std::filesystem::exists(python) || !std::filesystem::exists(paths.root / "window.py") ||
                !baas_installer::launch_detached({python.string(), (paths.root / "window.py").string()}, environment, paths.root)) {
                const std::string error = "installation succeeded, but BAAS could not be launched";
                model.update_task("launch", baas_installer::TaskStatus::Failed,
                                  model.localized(baas_installer::MessageId::LaunchFailed), 0.0);
                return {false, error};
            }
            baas_installer::apply_workflow_progress(model, "launch", "BAAS launched");
            wake();
        }
        model.append_event({{}, "installer", "installer", baas_installer::LogSeverity::Info, "installer completed"});
        return {true, std::string{}};
    };
    if (auto_exit) return baas_installer::run_unattended(config.mirrorc_cdk, install);
    return baas_installer::run_tui(first_start, config.mirrorc_cdk, install);
}
