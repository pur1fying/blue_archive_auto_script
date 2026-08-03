#include "baas_installer/uv_environment.hpp"

#include <algorithm>
#include <atomic>
#include <filesystem>
#include <fstream>
#include <iostream>

namespace {

std::filesystem::path managed_python(const baas_installer::InstallPaths& paths) {
#ifdef _WIN32
    return paths.toolkit_dir / "uv" / "cpython" / "cpython-3.9.0-windows-x86_64-none" / "python.exe";
#else
    return paths.toolkit_dir / "uv" / "cpython" / "cpython-3.9.0-linux-x86_64-none" / "bin" / "python3";
#endif
}

std::filesystem::path venv_python(const baas_installer::InstallPaths& paths) {
#ifdef _WIN32
    return paths.venv_dir / "Scripts" / "python.exe";
#else
    return paths.venv_dir / "bin" / "python";
#endif
}

std::vector<std::filesystem::path> disposable_uv_caches(
    const baas_installer::InstallPaths& paths) {
    return {
        paths.toolkit_dir / "uv" / "cache",
        paths.toolkit_dir / "uv" / "python-cache",
        paths.toolkit_dir / "uv" / "xdg" / "cache",
        paths.tmp_dir / "uv",
    };
}

void seed_cache_sentinels(const baas_installer::InstallPaths& paths) {
    for (const auto& directory : disposable_uv_caches(paths)) {
        std::filesystem::create_directories(directory);
        std::ofstream(directory / "download.cache") << "cached";
    }
}

std::vector<std::filesystem::path> preserved_uv_state(const baas_installer::InstallPaths& paths) {
    return {
        paths.toolkit_dir / "uv" / "credentials" / "credentials.json",
        paths.toolkit_dir / "uv" / "xdg" / "config" / "uv" / "config.toml",
        paths.toolkit_dir / "uv" / "xdg" / "data" / "uv" / "state.json",
    };
}

void seed_preserved_uv_state(const baas_installer::InstallPaths& paths) {
    for (const auto& path : preserved_uv_state(paths)) {
        std::filesystem::create_directories(path.parent_path());
        std::ofstream(path) << "preserve";
    }
}

bool cache_sentinels_exist(const baas_installer::InstallPaths& paths) {
    const auto caches = disposable_uv_caches(paths);
    return std::all_of(caches.begin(), caches.end(),
        [](const auto& directory) { return std::filesystem::is_regular_file(directory / "download.cache"); });
}

}  // namespace

int main() {
    const auto paths = baas_installer::InstallPaths::from_executable("E:/tmp/BAAS/BlueArchiveAutoScript.exe");
    baas_installer::InstallerConfig config;
    const auto environment = baas_installer::make_uv_environment(paths, config);
    for (const auto& [name, value] : environment.variables) {
        if (name.rfind("UV_", 0) == 0 || name.rfind("XDG_", 0) == 0 || name == "TMPDIR" || name == "TMP" || name == "TEMP") {
            if (value != "1" && value != "0" && value.rfind("E:/tmp/BAAS", 0) != 0) {
                std::cerr << name << " escaped portable root: " << value << '\n'; return 1;
            }
        }
    }
    if (!environment.managed || environment.variables.at("UV_VENV_RELOCATABLE") != "1" ||
        environment.variables.at("UV_NO_CONFIG") != "1" || environment.variables.at("UV_PYTHON_INSTALL_REGISTRY") != "0") {
        std::cerr << "managed uv flags missing\n"; return 1;
    }
    config.runtime_path = "D:/Python";
    const auto custom_environment = baas_installer::make_uv_environment(paths, config);
    if (custom_environment.managed || custom_environment.variables.contains("UV_PROJECT_ENVIRONMENT")) {
        std::cerr << "custom runtime not respected\n"; return 1;
    }
    config.runtime_path = "default";
    const auto commands = baas_installer::managed_uv_commands(environment, config, paths.root / "requirements.txt");
    if (commands.size() != 4 || commands[1].arguments[1] != "--relocatable" ||
        commands[3].arguments[2] != "--link-mode" || commands[3].arguments[3] != "copy") {
        std::cerr << "relocatable uv commands missing\n"; return 1;
    }

    const auto acceptance_root = std::filesystem::temp_directory_path() / "baas-installer-uv-acceptance-test";
    std::error_code ignored;
    std::filesystem::remove_all(acceptance_root, ignored);
    const auto acceptance_paths = baas_installer::InstallPaths::from_executable(
        acceptance_root / "BlueArchiveAutoScript.exe");
    const auto acceptance_environment = baas_installer::make_uv_environment(acceptance_paths, config);
    std::filesystem::create_directories(acceptance_root);
    int archive_downloads = 0;
    int version_checks = 0;
    const auto acceptance_executor = [&](const baas_installer::ProcessSpec& spec) {
        if (!spec.arguments.empty() && spec.arguments.front() == "curl") {
            ++archive_downloads;
            std::filesystem::create_directories(std::filesystem::path(spec.arguments[8]).parent_path());
            std::ofstream(spec.arguments[8], std::ios::binary) << "valid archive with an intentionally different digest";
            return baas_installer::ProcessResult{0, {}};
        }
        if (!spec.arguments.empty() && spec.arguments.front() == "tar") {
            const auto nested = std::filesystem::path(spec.arguments[4]) / "package" /
                                acceptance_environment.executable.filename();
            std::filesystem::create_directories(nested.parent_path());
            std::ofstream(nested, std::ios::binary) << "usable uv";
            return baas_installer::ProcessResult{0, {}};
        }
        if (!spec.arguments.empty() && std::filesystem::path(spec.arguments.front()) == acceptance_environment.executable &&
            spec.arguments.size() == 2 && spec.arguments[1] == "--version") {
            ++version_checks;
            return baas_installer::ProcessResult{0, "uv 1.0"};
        }
        return baas_installer::ProcessResult{1, {}};
    };
    std::string acceptance_error;
    if (!baas_installer::ensure_portable_uv(
            acceptance_paths, config, acceptance_error, {}, acceptance_executor,
            [](const baas_installer::SourceKind, const std::string&) { return 5LL; }) ||
        archive_downloads != 1 || version_checks != 1 || !std::filesystem::exists(acceptance_environment.executable)) {
        std::cerr << "a downloaded UV archive must be accepted by executable behavior, not a pinned digest: "
                  << acceptance_error << " downloads=" << archive_downloads << " checks=" << version_checks << '\n';
        return 1;
    }
    std::filesystem::remove_all(acceptance_root, ignored);

    const auto test_root = std::filesystem::temp_directory_path() / "baas-installer-uv-pty-test";
    std::filesystem::remove_all(test_root, ignored);
    const auto test_paths = baas_installer::InstallPaths::from_executable(test_root / "BlueArchiveAutoScript.exe");
    const auto test_environment = baas_installer::make_uv_environment(test_paths, config);
    std::filesystem::create_directories(test_environment.executable.parent_path());
    std::ofstream(test_environment.executable) << "fake";
    std::ofstream(baas_installer::dependency_requirements(test_paths)) << "example==1\n";
    std::vector<baas_installer::ProcessSpec> visible;
    int chunks = 0;
    bool caches_available_during_compile = false;
    std::atomic<int> uv_probes{0};
    std::atomic<int> cpython_probes{0};
    std::atomic<int> pypi_probes{0};
    const auto fake_terminal = [&](const baas_installer::ProcessSpec& spec) {
        visible.push_back(spec);
        if (spec.arguments.size() > 2 && spec.arguments[1] == "python" && spec.arguments[2] == "install") {
            std::filesystem::create_directories(managed_python(test_paths).parent_path());
            std::ofstream(managed_python(test_paths)) << "managed python";
        }
        if (spec.arguments.size() > 1 && spec.arguments[1] == "venv") {
            std::filesystem::create_directories(test_paths.venv_dir);
            std::ofstream(test_paths.venv_dir / "pyvenv.cfg")
                << "home = " << managed_python(test_paths).parent_path().string() << "\nversion_info = 3.9.0\n";
            std::filesystem::create_directories(venv_python(test_paths).parent_path());
            std::ofstream(venv_python(test_paths)) << "venv python";
        }
        if (spec.arguments.size() > 2 && spec.arguments[1] == "pip" && spec.arguments[2] == "compile") {
            caches_available_during_compile = cache_sentinels_exist(test_paths);
            std::ofstream(test_paths.root / ".baas-installer-requirements.txt") << "example==1.0\n";
        }
        if (spec.on_chunk) spec.on_chunk("pty chunk\r");
        return baas_installer::ProcessResult{0, {}};
    };
    const auto fake_probe = [&](const baas_installer::SourceKind kind, const std::string&) {
        if (kind == baas_installer::SourceKind::Uv) ++uv_probes;
        else if (kind == baas_installer::SourceKind::Cpython) ++cpython_probes;
        else if (kind == baas_installer::SourceKind::Pypi) ++pypi_probes;
        return 10LL;
    };
    std::string sync_error;
    seed_cache_sentinels(test_paths);
    seed_preserved_uv_state(test_paths);
    std::filesystem::create_directories(test_paths.state_dir);
    std::ofstream(test_paths.state_dir / "uv-cache-cleanup-v1.pending") << "pending\n";
    const bool synced = baas_installer::sync_portable_uv(
        test_paths, config, sync_error,
        [&](std::string_view task, std::string_view backend, std::string_view chunk) {
            if (task == "uv" && backend == "uv" && !chunk.empty()) ++chunks;
        }, fake_terminal, fake_probe);
    if (!synced || visible.size() != 4 || chunks != 4 || !caches_available_during_compile || uv_probes.load() != 0 ||
        cpython_probes.load() == 0 || pypi_probes.load() == 0) {
        std::cerr << "visible uv commands did not use the shared PTY observer or stale pending state cleared retry caches\n";
        return 1;
    }
    const auto successful_caches = disposable_uv_caches(test_paths);
    const auto durable_uv_state = preserved_uv_state(test_paths);
    if (std::any_of(successful_caches.begin(), successful_caches.end(),
            [](const auto& directory) { return std::filesystem::exists(directory); }) ||
        !std::filesystem::is_regular_file(test_environment.executable) ||
        !std::filesystem::is_regular_file(managed_python(test_paths)) ||
        !std::filesystem::is_directory(test_paths.venv_dir) ||
        !std::filesystem::is_regular_file(test_paths.root / ".baas-installer-requirements.txt") ||
        !std::filesystem::is_regular_file(test_paths.state_dir / "source-ranking-v1.json") ||
        !std::filesystem::is_regular_file(test_paths.state_dir / "dependencies-v1.sha256") ||
        !std::all_of(durable_uv_state.begin(), durable_uv_state.end(),
            [](const auto& path) { return std::filesystem::is_regular_file(path); })) {
        std::cerr << "successful dependency synchronization retained disposable UV caches or removed durable state\n";
        return 1;
    }
    for (const auto& spec : visible) {
        if (!spec.use_pty || spec.working_directory != test_paths.root || spec.environment.empty() ||
            spec.arguments.size() < 2 || spec.arguments[1] == "--no-progress") {
            std::cerr << "uv PTY specification is incomplete\n"; return 1;
        }
        for (const auto& [name, value] : spec.environment) {
            const bool remote_setting = name.find("INDEX") != std::string::npos || name.find("MIRROR") != std::string::npos;
            if (!remote_setting && (name.rfind("UV_", 0) == 0 || name.rfind("XDG_", 0) == 0 || name == "TMP" ||
                 name == "TEMP" || name == "TMPDIR") && value != "1" && value != "0" &&
                value.rfind(test_root.generic_string(), 0) != 0) {
                std::cerr << name << " escaped the disposable installation root\n"; return 1;
            }
        }
    }
    visible.clear();
    chunks = 0;
    uv_probes = cpython_probes = pypi_probes = 0;
    seed_cache_sentinels(test_paths);
    if (!baas_installer::sync_portable_uv(test_paths, config, sync_error,
            [&](std::string_view, std::string_view, std::string_view) { ++chunks; }, fake_terminal, fake_probe) ||
        !visible.empty() || chunks == 0 || uv_probes.load() != 0 || cpython_probes.load() != 0 ||
        pypi_probes.load() != 0 || !cache_sentinels_exist(test_paths)) {
        std::cerr << "an unchanged managed environment should skip every uv command and source probe\n";
        return 1;
    }
    const auto cleanup_pending = test_paths.state_dir / "uv-cache-cleanup-v1.pending";
    std::ofstream(cleanup_pending) << "pending\n";
    visible.clear();
    chunks = 0;
    if (!baas_installer::sync_portable_uv(test_paths, config, sync_error,
            [&](std::string_view, std::string_view, std::string_view) { ++chunks; }, fake_terminal, fake_probe) ||
        !visible.empty() || std::any_of(successful_caches.begin(), successful_caches.end(),
            [](const auto& directory) { return std::filesystem::exists(directory); }) ||
        std::filesystem::exists(cleanup_pending)) {
        std::cerr << "pending UV cache cleanup must be retried before a dependency SHA cache hit\n";
        return 1;
    }

    const auto moved_root = test_root.parent_path() / "baas-installer-uv-renamed-test";
    std::filesystem::remove_all(moved_root, ignored);
    std::filesystem::rename(test_root, moved_root);
    const auto moved_paths = baas_installer::InstallPaths::from_executable(moved_root / "BlueArchiveAutoScript.exe");
    visible.clear();
    chunks = 0;
    uv_probes = cpython_probes = pypi_probes = 0;
    if (!baas_installer::sync_portable_uv(moved_paths, config, sync_error,
            [&](std::string_view, std::string_view, std::string_view) { ++chunks; }, fake_terminal, fake_probe) ||
        !visible.empty() || uv_probes.load() != 0 || cpython_probes.load() != 0 || pypi_probes.load() != 0) {
        std::cerr << "renamed managed environment must repair metadata and keep its dependency cache hit\n";
        return 1;
    }
    std::string moved_config_text;
    {
        std::ifstream moved_config(moved_paths.venv_dir / "pyvenv.cfg", std::ios::binary);
        moved_config_text.assign(std::istreambuf_iterator<char>(moved_config), {});
    }
    if (moved_config_text.find(moved_root.string()) == std::string::npos ||
        moved_config_text.find(test_root.string()) != std::string::npos) {
        std::cerr << "renamed virtual environment retained the previous installation root\n";
        return 1;
    }
    std::filesystem::rename(moved_root, test_root);

    std::ofstream(baas_installer::dependency_requirements(test_paths), std::ios::trunc) << "example==2\n";
    chunks = 0;
    uv_probes = cpython_probes = pypi_probes = 0;
    if (!baas_installer::sync_portable_uv(test_paths, config, sync_error,
            [&](std::string_view, std::string_view, std::string_view) { ++chunks; }, fake_terminal, fake_probe) ||
        visible.size() != 2 || uv_probes.load() != 0 || cpython_probes.load() != 0 || pypi_probes.load() == 0) {
        std::cerr << "changed requirements must resolve/sync without rechecking installed uv or CPython\n";
        return 1;
    }
    std::filesystem::remove_all(test_root, ignored);

    const auto failure_root = std::filesystem::temp_directory_path() / "baas-installer-uv-failure-cache-test";
    std::filesystem::remove_all(failure_root, ignored);
    const auto failure_paths = baas_installer::InstallPaths::from_executable(
        failure_root / "BlueArchiveAutoScript.exe");
    baas_installer::InstallerConfig failure_config;
    failure_config.runtime_path = "D:/Custom Python/python.exe";
    const auto failure_uv = baas_installer::make_uv_environment(failure_paths, failure_config);
    std::filesystem::create_directories(failure_uv.executable.parent_path());
    std::ofstream(failure_uv.executable) << "fake";
    std::ofstream(baas_installer::dependency_requirements(failure_paths)) << "example==1\n";
    seed_cache_sentinels(failure_paths);
    const auto failed_compile_executor = [&](const baas_installer::ProcessSpec& spec) {
        if (spec.arguments.size() > 2 && spec.arguments[1] == "pip" && spec.arguments[2] == "compile") {
            return baas_installer::ProcessResult{1, {}};
        }
        return baas_installer::ProcessResult{0, {}};
    };
    if (baas_installer::sync_portable_uv(
            failure_paths, failure_config, sync_error, {}, failed_compile_executor, fake_probe) ||
        !cache_sentinels_exist(failure_paths)) {
        std::cerr << "failed dependency compilation must retain disposable UV caches for retry\n";
        return 1;
    }
    const auto failed_sync_executor = [&](const baas_installer::ProcessSpec& spec) {
        if (spec.arguments.size() > 2 && spec.arguments[1] == "pip" && spec.arguments[2] == "compile") {
            std::ofstream(failure_paths.root / ".baas-installer-requirements.txt") << "example==1.0\n";
            return baas_installer::ProcessResult{0, {}};
        }
        if (spec.arguments.size() > 2 && spec.arguments[1] == "pip" && spec.arguments[2] == "sync") {
            return baas_installer::ProcessResult{1, {}};
        }
        return baas_installer::ProcessResult{0, {}};
    };
    if (baas_installer::sync_portable_uv(
            failure_paths, failure_config, sync_error, {}, failed_sync_executor, fake_probe) ||
        !cache_sentinels_exist(failure_paths)) {
        std::cerr << "failed dependency synchronization must retain disposable UV caches for retry\n";
        return 1;
    }
    std::filesystem::remove_all(failure_root, ignored);

    const auto custom_root = std::filesystem::temp_directory_path() / "baas-installer-uv-custom-test";
    std::filesystem::remove_all(custom_root, ignored);
    const auto custom_paths = baas_installer::InstallPaths::from_executable(custom_root / "BlueArchiveAutoScript.exe");
    baas_installer::InstallerConfig custom_config;
    custom_config.runtime_path = "D:/Custom Python/python.exe";
    const auto custom_uv = baas_installer::make_uv_environment(custom_paths, custom_config);
    std::filesystem::create_directories(custom_uv.executable.parent_path());
    std::ofstream(custom_uv.executable) << "fake";
    std::filesystem::create_directories(custom_paths.root);
    std::ofstream(baas_installer::dependency_requirements(custom_paths)) << "example==1\n";
    std::vector<baas_installer::ProcessSpec> custom_commands;
    const auto custom_executor = [&](const baas_installer::ProcessSpec& spec) {
        custom_commands.push_back(spec);
        if (spec.arguments.size() > 2 && spec.arguments[1] == "pip" && spec.arguments[2] == "compile") {
            std::ofstream(custom_paths.root / ".baas-installer-requirements.txt") << "example==1.0\n";
        }
        return baas_installer::ProcessResult{0, {}};
    };
    if (!baas_installer::sync_portable_uv(custom_paths, custom_config, sync_error, {}, custom_executor, fake_probe) ||
        custom_commands.size() != 2) {
        std::cerr << "custom Python dependencies were not synchronized through uv\n"; return 1;
    }
    for (const auto& spec : custom_commands) {
        if (std::find(spec.arguments.begin(), spec.arguments.end(), "install") != spec.arguments.end() ||
            std::find(spec.arguments.begin(), spec.arguments.end(), "venv") != spec.arguments.end()) {
            std::cerr << "custom runtime attempted portable Python creation\n"; return 1;
        }
    }
    const auto& sync_arguments = custom_commands.back().arguments;
    const auto python = std::find(sync_arguments.begin(), sync_arguments.end(), "--python");
    if (python == sync_arguments.end() || std::next(python) == sync_arguments.end() ||
        *std::next(python) != custom_config.runtime_path) {
        std::cerr << "custom runtime was not passed to uv pip sync\n"; return 1;
    }

    std::filesystem::remove(custom_paths.state_dir / "dependencies-v1.sha256", ignored);
    std::filesystem::remove(custom_paths.root / ".baas-installer-requirements.txt", ignored);
    custom_commands.clear();
    const auto failed_probe = [](const baas_installer::SourceKind, const std::string&) { return -1LL; };
    if (!baas_installer::sync_portable_uv(custom_paths, custom_config, sync_error, {}, custom_executor, failed_probe) ||
        custom_commands.size() != 2) {
        std::cerr << "probe failures must not prevent real uv source attempts\n";
        return 1;
    }
#ifdef _WIN32
    if (baas_installer::dependency_requirements(custom_paths).filename() != "requirements.txt") return 1;
#else
    if (baas_installer::dependency_requirements(custom_paths).filename() != "requirements-linux.txt") return 1;
#endif
    std::filesystem::remove_all(custom_root, ignored);
    return 0;
}
