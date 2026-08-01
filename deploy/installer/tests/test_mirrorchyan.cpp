#include "baas_installer/mirrorchyan.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>

int main() {
    const auto release = baas_installer::parse_mirror_response(R"({"code":0,"msg":"ok","data":{"version_name":"abc","url":"https://example.invalid/a.zip","sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","update_type":"full"}})");
    if (release.status != baas_installer::CdkStatus::Valid || release.version != "abc") { std::cerr << "valid response failed\n"; return 1; }
    const auto malformed = baas_installer::parse_mirror_response(R"({"code":0,"data":{"url":"https://x","sha256":"bad"}})");
    if (malformed.status != baas_installer::CdkStatus::Malformed || baas_installer::is_sha256("bad")) { std::cerr << "invalid digest accepted\n"; return 1; }
    const auto file = std::filesystem::temp_directory_path() / "baas-installer-sha-test";
    std::ofstream(file, std::ios::binary) << "abc";
    const auto good = baas_installer::verify_sha256(file, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    std::error_code ignored; std::filesystem::remove(file, ignored);
    if (!good) { std::cerr << "sha256 verification failed\n"; return 1; }
    if (baas_installer::mirror_latest_url("a b", "", "stable").find("cdk=a%20b") == std::string::npos) { std::cerr << "CDK escaping failed\n"; return 1; }
    return 0;
}
