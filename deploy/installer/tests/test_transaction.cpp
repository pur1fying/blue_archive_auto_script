#include "baas_installer/transaction.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>

namespace fs = std::filesystem;

static void write(const fs::path& path, const std::string& text) {
    fs::create_directories(path.parent_path());
    std::ofstream(path) << text;
}

static std::string read(const fs::path& path) { std::ifstream input(path); return {std::istreambuf_iterator<char>(input), {}}; }

int main() {
    const auto fixture = fs::temp_directory_path() / "baas-installer-transaction";
    std::error_code ignored;
    fs::remove_all(fixture, ignored);
    baas_installer::InstallPaths paths;
    paths.root = fixture / "install";
    paths.tmp_dir = paths.root / "tmp";
    write(paths.root / "core/ocr/baas_ocr_client/bin/keep.txt", "old-ocr");
    write(paths.root / "app.txt", "old-main");
    {
        baas_installer::InstallTransaction transaction(paths);
        write(transaction.main_staging_path() / "app.txt", "new-main");
        write(transaction.main_staging_path() / "core/ocr/baas_ocr_client/bin/keep.txt", "bad-main-ocr");
        write(transaction.ocr_staging_path() / "keep.txt", "new-ocr");
        transaction.deploy_main();
        if (read(paths.root / "core/ocr/baas_ocr_client/bin/keep.txt") != "old-ocr") { std::cerr << "main overwrote OCR\n"; return 1; }
        transaction.deploy_ocr();
        transaction.rollback();
    }
    const bool good = read(paths.root / "app.txt") == "old-main" && read(paths.root / "core/ocr/baas_ocr_client/bin/keep.txt") == "old-ocr";
    fs::remove_all(fixture, ignored);
    if (!good) { std::cerr << "rollback failed\n"; return 1; }
    return 0;
}
