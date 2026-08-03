#include "baas_installer/digest.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>

int main() {
    using baas_installer::sha256_bytes;
    if (sha256_bytes("") != "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" ||
        sha256_bytes("abc") != "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad") {
        std::cerr << "standard SHA-256 vectors failed\n";
        return 1;
    }
    const auto file = std::filesystem::temp_directory_path() / "baas-installer-digest-test.txt";
    std::ofstream(file, std::ios::binary | std::ios::trunc) << "abc";
    const auto expected = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
    const bool valid = baas_installer::sha256_file(file) == expected &&
                       baas_installer::verify_sha256(file, expected) &&
                       !baas_installer::verify_sha256(file, std::string(64, '0'));
    std::error_code ignored;
    std::filesystem::remove(file, ignored);
    if (!valid) {
        std::cerr << "file SHA-256 contract failed\n";
        return 1;
    }
    return 0;
}
