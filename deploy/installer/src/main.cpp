#include "baas_installer/config.hpp"
#include "baas_installer/deployment_manifest.hpp"
#include "baas_installer/install_target.hpp"
#include "baas_installer/git.hpp"
#include "baas_installer/mirrorchyan.hpp"
#include "baas_installer/paths.hpp"
#include "baas_installer/process.hpp"
#include "baas_installer/sources.hpp"
#include "baas_installer/startup.hpp"
#include "baas_installer/tui.hpp"
#include "baas_installer/uv_environment.hpp"
#include "baas_installer/workflow.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <thread>
#include <algorithm>
#include <cctype>
#include <optional>

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

std::string short_revision(const std::string& revision) {
    static const std::string prefix = "refs/heads/";
    return revision.starts_with(prefix) ? revision.substr(prefix.size()) : revision;
}

std::string ocr_executable_name() {
#ifdef _WIN32
    return "BAAS_ocr_server.exe";
#else
    return "BAAS_ocr_server";
#endif
}

bool is_git_commit(const std::string& value) {
    return value.size() == 40 && std::all_of(value.begin(), value.end(), [](const unsigned char character) {
        return std::isxdigit(character) != 0;
    });
}

}

#ifdef _WIN32
int wmain(int argc, wchar_t* argv[]) {
#else
int main(int argc, char* argv[]) {
#endif
    baas_installer::configure_utf8_terminal();
    const auto executable = baas_installer::current_executable_path();
    std::vector<std::string> raw_arguments;
    for (int index = 1; index < argc; ++index) {
#ifdef _WIN32
        raw_arguments.push_back(baas_installer::path_to_utf8(std::filesystem::path(argv[index])));
#else
        raw_arguments.emplace_back(argv[index]);
#endif
    }
    const auto options = baas_installer::parse_startup_arguments(raw_arguments);
    if (!options.valid) {
        std::cerr << options.error << '\n';
        return 2;
    }
    if (options.help) {
        std::cout << "BAAS portable installer\n\nOptions:\n"
                     "  --help                 show this help\n"
                     "  --print-root           print the safe existing/selected install root\n"
                     "  --install-dir <path>   choose an absolute or installer-relative directory\n"
                     "  --auto-exit            run non-interactively\n"
                     "  --no-launch            do not launch BAAS (verification only)\n";
        return 0;
    }
    const auto startup = baas_installer::decide_startup(executable, options);
    if (startup.mode == baas_installer::StartupMode::Invalid) {
        std::cerr << startup.error << '\n';
        return 2;
    }
    if (options.print_root) {
        std::cout << baas_installer::path_to_utf8(startup.target_root) << '\n';
        return 0;
    }
    for (;;) {
    std::optional<baas_installer::InstallPaths> selected_paths;
    std::string selected_configured_root = startup.configured_root;
    if (startup.mode == baas_installer::StartupMode::SelectInstallTarget) {
        const auto select = [&](const std::filesystem::path& requested_root) {
            const auto target = baas_installer::validate_install_target(executable, requested_root);
            if (!target.accepted) return std::pair{false, target.error};
            selected_paths = baas_installer::InstallPaths::from_install_root(target.root, executable);
            selected_configured_root = requested_root.empty() ? "." : baas_installer::path_to_utf8(requested_root);
            return std::pair{true, std::string{}};
        };
        if (options.auto_exit) {
            const auto [success, error] = select(baas_installer::path_from_utf8(startup.configured_root));
            if (!success && !error.empty()) std::cerr << error << '\n';
            if (!success) return 1;
        } else if (baas_installer::run_install_target_tui(
                       baas_installer::path_from_utf8(startup.configured_root), select) != 0) {
            return 1;
        }
    } else {
        selected_paths = startup.paths;
    }

    if (!selected_paths) {
        std::cerr << "installation directory was not selected\n";
        return 1;
    }
    const auto paths = *selected_paths;
    const bool auto_exit = options.auto_exit;
    const bool no_launch = options.no_launch;
    const bool first_start = !std::filesystem::exists(paths.setup_toml);
    auto config = baas_installer::load_config(paths);
    config.baas_root_path = selected_configured_root.empty() ? "." : selected_configured_root;
    const auto validate_cdk = [&](const std::string& candidate) {
        std::string error;
        const auto url = baas_installer::mirror_latest_url(
            baas_installer::MirrorResource::Main, {}, {}, candidate, {}, config.channel);
        const auto release = baas_installer::request_mirror_release(url, error, 10);
        const bool accepted = release.status == baas_installer::CdkStatus::Valid ||
                              release.status == baas_installer::CdkStatus::UpToDate;
        return std::pair{accepted, accepted ? std::string{} :
            baas_installer::mirror_failure_reason(release, error)};
    };
    const auto log_path = paths.logs_dir / "installer.log";
    baas_installer::set_default_process_log(log_path);
    const auto install = [&](const std::string& selected_cdk, baas_installer::InstallerViewModel& model,
                             const std::function<void()>& wake) -> baas_installer::InstallAttemptResult {
        model.set_log_sink(baas_installer::path_to_utf8(log_path));
        model.add_log_secret(selected_cdk);
        model.append_event({{}, "installer", "installer", baas_installer::LogSeverity::Info, "installer started"});
        try {
            // Establish the installation identity before any download,
            // repository preparation, cache operation, or deployment.  The
            // interactive path reaches this point only after CDK preflight.
            baas_installer::begin_install_session_config(config, paths, selected_cdk);
        } catch (const std::exception& error) {
            return {.success = false, .error = error.what()};
        }
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
            const auto maintenance_marker = paths.state_dir /
                (main_repository ? "main-git-maintenance-v1.pending" : "ocr-git-maintenance-v1.pending");
            const baas_installer::ProcessObserver observer = [&](std::string_view, const std::string_view backend,
                                                                  const std::string_view chunk) {
                model.append_process_chunk(task, std::string(backend), chunk);
                wake();
            };

            if (std::filesystem::exists(maintenance_marker)) {
                if (!std::filesystem::is_directory(live / ".git")) {
                    std::error_code ignored;
                    std::filesystem::remove(maintenance_marker, ignored);
                } else {
                    std::string maintenance_error;
                    if (!baas_installer::git_cli_available() ||
                        !baas_installer::compact_git_repository(
                            live, baas_installer::GitBackend::GitCli, maintenance_error)) {
                        return baas_installer::PreparedRepository{
                            .success = false, .backend = "git",
                            .error = "pending Git maintenance failed: " + maintenance_error};
                    }
                    std::error_code remove_error;
                    if (!std::filesystem::remove(maintenance_marker, remove_error) || remove_error) {
                        return baas_installer::PreparedRepository{
                            .success = false, .backend = "git",
                            .error = "could not clear completed Git maintenance marker"};
                    }
                    model.append_event({{}, task, "git", baas_installer::LogSeverity::Info,
                                        "pending repository maintenance completed"});
                }
            }

            const auto resource = main_repository ? baas_installer::MirrorResource::Main
                                                  : baas_installer::MirrorResource::Ocr;
            const bool mirror_selected = !selected_cdk.empty() &&
                baas_installer::mirror_manages_resource(resource);
            if (mirror_selected) {
                std::string mirror_error;
                const auto platform = baas_installer::current_mirror_platform();
                const auto deployment_tree = main_repository
                    ? baas_installer::DeploymentTree::Main
                    : baas_installer::DeploymentTree::Ocr;
                const bool incremental_owned =
                    baas_installer::load_deployment_manifest(paths, deployment_tree).valid;
                const auto mirror_current_version = incremental_owned
                    ? current_version
                    : std::string{};
                const auto request_url = baas_installer::mirror_latest_url(
                    resource, platform.os, platform.arch, selected_cdk,
                    mirror_current_version, config.channel);
                auto release = baas_installer::request_mirror_release(request_url, mirror_error);
                if (release.status == baas_installer::CdkStatus::UpToDate) {
                    model.append_event({{}, task, "mirrorchyan", baas_installer::LogSeverity::Info, "already current"});
                    return baas_installer::PreparedRepository{.success = true,
                        .mode = baas_installer::RepositoryMode::Unchanged, .backend = "mirrorchyan",
                        .version = release.version.empty() ? current_version : release.version,
                        .revision = short_revision(revision)};
                }
                if (release.status == baas_installer::CdkStatus::Valid && !mirror_current_version.empty()) {
                    release = baas_installer::wait_for_incremental_release(
                        std::move(release),
                        [&] { return baas_installer::request_mirror_release(request_url, mirror_error); },
                        [] { std::this_thread::sleep_for(std::chrono::milliseconds(500)); }, 10);
                }
                const bool compatible_release = main_repository || is_git_commit(release.version);
                if (release.status == baas_installer::CdkStatus::Valid && compatible_release) {
                    const auto prefix = main_repository ? "main" : "ocr";
                    const auto archive = transaction.staging_root() / (std::string(prefix) + "-mirror.zip");
                    const auto extracted = transaction.staging_root() / (std::string(prefix) + "-mirror-unpacked");
                    int last_download_percent = -1;
                    if (baas_installer::download_mirror_package(
                            release, archive, mirror_error,
                            [&](const std::uint64_t downloaded, const std::uint64_t total) {
                                if (total != 0) {
                                    const auto percent = static_cast<int>((100ULL * downloaded) / total);
                                    if (percent != last_download_percent) {
                                        last_download_percent = percent;
                                        observer(task, "mirrorchyan", "Downloading package " + std::to_string(percent) + "%\r");
                                    }
                                } else {
                                    observer(task, "mirrorchyan", "Downloading package " + std::to_string(downloaded) + " bytes\r");
                                }
                            }) &&
                        baas_installer::extract_mirror_archive(
                            archive, extracted, mirror_error,
                            [&](const std::string_view chunk) { observer(task, "mirrorchyan", chunk); })) {
                        auto package = baas_installer::inspect_mirror_staging(release, extracted, mirror_error);
                        if (mirror_error.empty() &&
                            package.mode == baas_installer::MirrorPackageMode::Incremental &&
                            !incremental_owned) {
                            mirror_error = "incremental MirrorChyan package requires a valid deployment ownership manifest";
                        }
                        if (mirror_error.empty()) {
                            if (!main_repository) {
                                const auto executable = std::filesystem::path(ocr_executable_name());
                                bool available = package.mode == baas_installer::MirrorPackageMode::Full
                                    ? std::filesystem::is_regular_file(package.content_root / executable)
                                    : std::filesystem::is_regular_file(live / executable);
                                if (package.mode == baas_installer::MirrorPackageMode::Incremental) {
                                    if (std::find(package.changes.deleted.begin(), package.changes.deleted.end(), executable) != package.changes.deleted.end()) available = false;
                                    if (std::find(package.changes.added.begin(), package.changes.added.end(), executable) != package.changes.added.end() ||
                                        std::find(package.changes.modified.begin(), package.changes.modified.end(), executable) != package.changes.modified.end()) available = true;
                                }
                                if (!available) mirror_error = "MirrorChyan OCR package does not provide the required BAAS_ocr_server executable";
                            }
                        }
                        if (mirror_error.empty()) {
                            model.append_event({{}, task, "mirrorchyan", baas_installer::LogSeverity::Info,
                                                "package prepared: " + package.version});
                            const auto mode = package.mode == baas_installer::MirrorPackageMode::Full
                                ? baas_installer::RepositoryMode::Full : baas_installer::RepositoryMode::Incremental;
                            return baas_installer::PreparedRepository{.success = true, .mode = mode,
                                .backend = "mirrorchyan", .version = package.version,
                                .revision = short_revision(revision),
                                .apply = [package = std::move(package), live, main_repository](
                                             baas_installer::InstallTransaction& current, std::string& error) {
                                    try {
                                        current.remove_path(live / ".git", baas_installer::RemovalOwnership::GitMetadata);
                                        if (package.mode == baas_installer::MirrorPackageMode::Full) {
                                            if (main_repository) current.deploy_main_from(package.content_root);
                                            else current.deploy_ocr_from(package.content_root);
                                        } else {
                                            for (const auto& path : package.changes.deleted) {
                                                current.remove_path(
                                                    live / path,
                                                    main_repository
                                                        ? baas_installer::RemovalOwnership::MainManifest
                                                        : baas_installer::RemovalOwnership::OcrManifest);
                                            }
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
                if (release.status == baas_installer::CdkStatus::Valid && !compatible_release) {
                    mirror_error = "MirrorChyan OCR resource is not a commit-versioned BAAS_Cpp_prebuild package";
                }
                const auto reason = baas_installer::mirror_failure_reason(release, mirror_error);
                model.append_event({{}, task, "mirrorchyan", baas_installer::LogSeverity::Error, reason});
                if (baas_installer::repository_source_decision(mirror_selected, false) ==
                    baas_installer::RepositorySourceDecision::Fail) {
                    return baas_installer::PreparedRepository{
                        .success = false,
                        .backend = "mirrorchyan",
                        .error = std::string(main_repository ? "main repository: " : "OCR repository: ") + reason,
                    };
                }
            }

            const auto git = baas_installer::prepare_git_repository(
                sources, live, staging, revision, observer,
                paths.state_dir / "source-ranking-v1.json",
                main_repository ? baas_installer::SourceKind::MainGit : baas_installer::SourceKind::OcrGit);
            if (!git.success) return baas_installer::PreparedRepository{.success = false, .backend = "git",
                .error = (main_repository ? "main repository: " : "OCR repository: ") + git.error};
            model.append_event({{}, task, "git", baas_installer::LogSeverity::Info,
                                git.mode == baas_installer::RepositoryMode::Unchanged
                                    ? "remote HEAD matches local HEAD; fetch skipped"
                                    : "repository update prepared at " + git.commit});
            return baas_installer::PreparedRepository{.success = true, .mode = git.mode,
                .backend = baas_installer::git_backend_name(git.backend), .version = git.commit,
                .revision = short_revision(revision),
                .apply = [git, live, main_repository, observer, maintenance_marker](
                             baas_installer::InstallTransaction& current, std::string& error) {
                    const auto finalize = [&] {
                        current.add_commit_action([live, backend = git.backend, maintenance_marker] {
                            std::string finalize_error;
                            if (!baas_installer::finalize_git_repository(live, backend, finalize_error)) {
                                throw std::runtime_error(finalize_error);
                            }
                            if (backend == baas_installer::GitBackend::GitCli) {
                                std::filesystem::create_directories(maintenance_marker.parent_path());
                                std::ofstream marker(maintenance_marker, std::ios::trunc);
                                marker << "pending\n";
                                marker.close();
                                if (!marker) throw std::runtime_error("could not persist Git maintenance marker");
                            }
                        });
                        current.add_rollback_action([maintenance_marker] {
                            std::error_code ignored;
                            std::filesystem::remove(maintenance_marker, ignored);
                        });
                        current.add_post_commit_action([live, backend = git.backend, maintenance_marker] {
                            std::string compact_error;
                            if (!baas_installer::compact_git_repository(live, backend, compact_error)) {
                                throw std::runtime_error(compact_error);
                            }
                            if (backend == baas_installer::GitBackend::GitCli) {
                                std::error_code remove_error;
                                if (!std::filesystem::remove(maintenance_marker, remove_error) || remove_error) {
                                    throw std::runtime_error("could not clear Git maintenance marker");
                                }
                            }
                        });
                    };
                    if (git.mode == baas_installer::RepositoryMode::Full) {
                        current.remove_path(live / ".git", baas_installer::RemovalOwnership::GitMetadata);
                        if (main_repository) current.deploy_main_from(git.staging_path);
                        else current.deploy_ocr_from(git.staging_path);
                        current.replace_directory(git.staging_path / ".git", live / ".git");
                        finalize();
                        return true;
                    }
                    if (git.mode == baas_installer::RepositoryMode::Incremental) {
                        current.add_rollback_action([git, live] {
                            auto restore = git;
                            restore.commit = git.previous_commit;
                            std::string ignored;
                            (void)baas_installer::apply_git_update(restore, live, ignored);
                        });
                        if (!baas_installer::apply_git_update(git, live, error, observer)) return false;
                        finalize();
                        return true;
                    }
                    return true;
                }};
        };
        services.prepare_main = [&](auto& transaction) { return prepare_repository(true, transaction); };
        services.prepare_ocr = [&](auto& transaction) { return prepare_repository(false, transaction); };
        services.verify_deployment = [](const baas_installer::InstallPaths& current, const baas_installer::InstallerConfig&, std::string& error) {
        if (!std::filesystem::exists(current.root / "main.py")) { error = "main repository did not contain main.py"; return false; }
        const auto ocr = current.root / "core" / "ocr" / "baas_ocr_client" / "bin";
        if (!std::filesystem::is_regular_file(ocr / ocr_executable_name())) { error = "OCR server executable is missing"; return false; }
        return true;
        };
        services.sync_uv = [&](const baas_installer::InstallPaths& current, const baas_installer::InstallerConfig& settings, std::string& error) {
            const baas_installer::ProcessObserver observer = [&](std::string_view task, std::string_view backend,
                                                                 std::string_view chunk) {
                model.append_process_chunk(std::string(task), std::string(backend), chunk);
                wake();
            };
            return baas_installer::sync_portable_uv(current, settings, error, observer);
        };
        const auto result = baas_installer::install_or_update(config, paths, services);
        if (!result.success) {
            if (result.failure_backend == "mirrorchyan") {
                try {
                    baas_installer::clear_mirror_cdk(config, paths);
                } catch (const std::exception& error) {
                    return {.success = false,
                            .failure_kind = baas_installer::InstallFailureKind::MirrorChyan,
                            .error = std::string("MirrorChyan failed and its CDK could not be cleared: ") +
                                     error.what()};
                }
            }
            model.append_event({{}, "installer", "installer", baas_installer::LogSeverity::Error, result.error});
            return {
                .success = false,
                .failure_kind = result.failure_backend == "mirrorchyan"
                    ? baas_installer::InstallFailureKind::MirrorChyan
                    : baas_installer::InstallFailureKind::General,
                .error = result.error,
            };
        }
        try {
            baas_installer::commit_successful_mirror_cdk(config, paths, selected_cdk);
        } catch (const std::exception& error) {
            return {.success = false, .error = error.what()};
        }
        if (!no_launch) {
            baas_installer::apply_workflow_progress(model, "launch", "launching BAAS");
            wake();
#ifdef _WIN32
            auto python = paths.venv_dir / "Scripts" / "pythonw.exe";
            if (!std::filesystem::exists(python)) python = paths.venv_dir / "Scripts" / "python.exe";
#else
            auto python = paths.venv_dir / "bin" / "python";
#endif
            if (!config.uses_portable_runtime()) python = baas_installer::path_from_utf8(config.runtime_path);
            auto environment = baas_installer::make_uv_environment(paths, config).variables;
            if (config.uses_portable_runtime()) environment["VIRTUAL_ENV"] = baas_installer::path_to_utf8(paths.venv_dir);
            if (!std::filesystem::exists(python) || !std::filesystem::exists(paths.root / "window.py") ||
                !baas_installer::launch_detached(
                    {baas_installer::path_to_utf8(python),
                     baas_installer::path_to_utf8(paths.root / "window.py")},
                    environment, paths.root)) {
                const std::string error = "installation succeeded, but BAAS could not be launched";
                model.update_task("launch", baas_installer::TaskStatus::Failed,
                                  model.localized(baas_installer::MessageId::LaunchFailed), 0.0);
                return {.success = false, .error = error};
            }
            baas_installer::apply_workflow_progress(model, "launch", "BAAS launched");
            wake();
        }
        model.append_event({{}, "installer", "installer", baas_installer::LogSeverity::Info, "installer completed"});
        return {.success = true};
    };
    if (auto_exit) return baas_installer::run_unattended(config.mirrorc_cdk, install);
    const auto tui_result = baas_installer::run_tui(
        first_start, config.mirrorc_cdk, install, validate_cdk,
        startup.mode == baas_installer::StartupMode::SelectInstallTarget);
    if (tui_result == baas_installer::kTuiBackToTarget) continue;
    return tui_result;
    }
}
