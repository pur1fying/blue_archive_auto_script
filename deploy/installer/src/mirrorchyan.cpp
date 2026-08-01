#include "baas_installer/mirrorchyan.hpp"

#include <array>
#include <cctype>
#include <fstream>
#include <iomanip>
#include <sstream>

#ifdef BAAS_INSTALLER_HAS_CURL
#include <curl/curl.h>
#endif

namespace fs = std::filesystem;

namespace baas_installer {
namespace {

std::string string_field(const std::string& text, const std::string& field) {
    const auto marker = "\"" + field + "\"";
    const auto key = text.find(marker);
    if (key == std::string::npos) return {};
    const auto colon = text.find(':', key + marker.size());
    const auto first = text.find('"', colon + 1);
    const auto last = first == std::string::npos ? std::string::npos : text.find('"', first + 1);
    return last == std::string::npos ? std::string{} : text.substr(first + 1, last - first - 1);
}

int number_field(const std::string& text, const std::string& field, const int missing) {
    const auto marker = "\"" + field + "\"";
    const auto key = text.find(marker);
    const auto colon = key == std::string::npos ? std::string::npos : text.find(':', key + marker.size());
    if (colon == std::string::npos) return missing;
    try { return std::stoi(text.substr(colon + 1)); } catch (...) { return missing; }
}

std::string url_encode(const std::string& value) {
    std::ostringstream out;
    for (const unsigned char ch : value) {
        if (std::isalnum(ch) || ch == '-' || ch == '_' || ch == '.') out << ch;
        else out << '%' << std::uppercase << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(ch) << std::nouppercase << std::dec;
    }
    return out.str();
}

// Compact SHA-256 implementation so integrity verification remains available
// even before optional package dependencies have been initialized.
class Sha256 {
public:
    Sha256() : state_{0x6a09e667U,0xbb67ae85U,0x3c6ef372U,0xa54ff53aU,0x510e527fU,0x9b05688cU,0x1f83d9abU,0x5be0cd19U} {}
    void update(const unsigned char* data, std::size_t size) {
        bit_count_ += static_cast<std::uint64_t>(size) * 8;
        while (size != 0) {
            const auto take = std::min<std::size_t>(size, 64 - used_);
            std::copy_n(data, take, block_.begin() + used_);
            used_ += take; data += take; size -= take;
            if (used_ == 64) { transform(); used_ = 0; }
        }
    }
    std::string finish() {
        const auto bits = bit_count_;
        const unsigned char one = 0x80; update(&one, 1);
        const unsigned char zero = 0;
        while (used_ != 56) update(&zero, 1);
        std::array<unsigned char, 8> length{};
        for (int i = 0; i != 8; ++i) length[7 - i] = static_cast<unsigned char>(bits >> (i * 8));
        update(length.data(), length.size());
        std::ostringstream out;
        for (const auto word : state_) for (int shift = 24; shift >= 0; shift -= 8) out << std::hex << std::setw(2) << std::setfill('0') << ((word >> shift) & 0xff);
        return out.str();
    }
private:
    static constexpr std::array<std::uint32_t, 64> k_{
        0x428a2f98U,0x71374491U,0xb5c0fbcfU,0xe9b5dba5U,0x3956c25bU,0x59f111f1U,0x923f82a4U,0xab1c5ed5U,0xd807aa98U,0x12835b01U,0x243185beU,0x550c7dc3U,0x72be5d74U,0x80deb1feU,0x9bdc06a7U,0xc19bf174U,0xe49b69c1U,0xefbe4786U,0x0fc19dc6U,0x240ca1ccU,0x2de92c6fU,0x4a7484aaU,0x5cb0a9dcU,0x76f988daU,0x983e5152U,0xa831c66dU,0xb00327c8U,0xbf597fc7U,0xc6e00bf3U,0xd5a79147U,0x06ca6351U,0x14292967U,0x27b70a85U,0x2e1b2138U,0x4d2c6dfcU,0x53380d13U,0x650a7354U,0x766a0abbU,0x81c2c92eU,0x92722c85U,0xa2bfe8a1U,0xa81a664bU,0xc24b8b70U,0xc76c51a3U,0xd192e819U,0xd6990624U,0xf40e3585U,0x106aa070U,0x19a4c116U,0x1e376c08U,0x2748774cU,0x34b0bcb5U,0x391c0cb3U,0x4ed8aa4aU,0x5b9cca4fU,0x682e6ff3U,0x748f82eeU,0x78a5636fU,0x84c87814U,0x8cc70208U,0x90befffaU,0xa4506cebU,0xbef9a3f7U,0xc67178f2U};
    static std::uint32_t rotr(const std::uint32_t x, const int n) { return (x >> n) | (x << (32 - n)); }
    void transform() {
        std::array<std::uint32_t, 64> w{};
        for (int i = 0; i < 16; ++i) w[i] = (std::uint32_t(block_[i*4]) << 24) | (std::uint32_t(block_[i*4+1]) << 16) | (std::uint32_t(block_[i*4+2]) << 8) | block_[i*4+3];
        for (int i = 16; i < 64; ++i) { const auto s0 = rotr(w[i-15],7)^rotr(w[i-15],18)^(w[i-15]>>3); const auto s1 = rotr(w[i-2],17)^rotr(w[i-2],19)^(w[i-2]>>10); w[i] = w[i-16]+s0+w[i-7]+s1; }
        auto a=state_[0],b=state_[1],c=state_[2],d=state_[3],e=state_[4],f=state_[5],g=state_[6],h=state_[7];
        for (int i=0;i<64;++i) { const auto s1=rotr(e,6)^rotr(e,11)^rotr(e,25); const auto choice=(e&f)^((~e)&g); const auto t1=h+s1+choice+k_[i]+w[i]; const auto s0=rotr(a,2)^rotr(a,13)^rotr(a,22); const auto majority=(a&b)^(a&c)^(b&c); const auto t2=s0+majority; h=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2; }
        state_[0]+=a;state_[1]+=b;state_[2]+=c;state_[3]+=d;state_[4]+=e;state_[5]+=f;state_[6]+=g;state_[7]+=h;
    }
    std::array<unsigned char,64> block_{}; std::array<std::uint32_t,8> state_{}; std::uint64_t bit_count_{}; std::size_t used_{};
};

#ifdef BAAS_INSTALLER_HAS_CURL
size_t write_file(const char* data, const size_t size, const size_t count, void* context) { return std::fwrite(data, size, count, static_cast<FILE*>(context)); }
#endif

}  // namespace

MirrorRelease parse_mirror_response(const std::string& json) {
    MirrorRelease result;
    result.message = string_field(json, "msg");
    switch (number_field(json, "code", -9999)) {
        case 0: result.status = CdkStatus::Valid; break;
        case 1: result.status = CdkStatus::Invalid; break;
        case 2: result.status = CdkStatus::Expired; break;
        case 3: result.status = CdkStatus::Exhausted; break;
        case 4: result.status = CdkStatus::Mismatched; break;
        case 5: result.status = CdkStatus::Blocked; break;
        default: result.status = CdkStatus::ServerError; break;
    }
    result.version = string_field(json, "version_name"); result.download_url = string_field(json, "url");
    result.sha256 = string_field(json, "sha256"); result.update_type = string_field(json, "update_type");
    if (result.status == CdkStatus::Valid && (result.download_url.empty() || !is_sha256(result.sha256))) result.status = CdkStatus::Malformed;
    return result;
}

std::string mirror_latest_url(const std::string& cdk, const std::string& current_sha, const std::string& channel) {
    return "https://mirrorchyan.com/api/resources/BAAS_repo/latest?channel=" + url_encode(channel) + "&current_version=" + url_encode(current_sha) + "&user_agent=BAAS_GUI&cdk=" + url_encode(cdk);
}

bool is_sha256(const std::string& digest) {
    return digest.size() == 64 && std::all_of(digest.begin(), digest.end(), [](unsigned char ch) { return std::isxdigit(ch); });
}

bool verify_sha256(const fs::path& file, const std::string& expected_digest) {
    if (!is_sha256(expected_digest)) return false;
    std::ifstream input(file, std::ios::binary); if (!input) return false;
    Sha256 hash; std::array<unsigned char, 8192> bytes{};
    while (input) { input.read(reinterpret_cast<char*>(bytes.data()), bytes.size()); hash.update(bytes.data(), static_cast<std::size_t>(input.gcount())); }
    auto actual = hash.finish(); auto expected = expected_digest;
    std::transform(actual.begin(), actual.end(), actual.begin(), ::tolower); std::transform(expected.begin(), expected.end(), expected.begin(), ::tolower);
    return actual == expected;
}

bool download_mirror_package(const MirrorRelease& release, const fs::path& archive, std::string& error) {
    if (release.status != CdkStatus::Valid || !is_sha256(release.sha256)) { error = "MirrorChyan response has no verifiable package"; return false; }
#ifdef BAAS_INSTALLER_HAS_CURL
    fs::create_directories(archive.parent_path());
    FILE* output = std::fopen(archive.string().c_str(), "wb"); if (!output) { error = "cannot create staging archive"; return false; }
    CURL* curl = curl_easy_init();
    if (!curl) { std::fclose(output); error = "cannot initialize HTTP client"; return false; }
    curl_easy_setopt(curl, CURLOPT_URL, release.download_url.c_str()); curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_file); curl_easy_setopt(curl, CURLOPT_WRITEDATA, output); curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L); curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT, 5L); curl_easy_setopt(curl, CURLOPT_TIMEOUT, 600L);
    const auto status = curl_easy_perform(curl); curl_easy_cleanup(curl); std::fclose(output);
    if (status != CURLE_OK || !verify_sha256(archive, release.sha256)) { fs::remove(archive); error = status == CURLE_OK ? "MirrorChyan SHA-256 mismatch" : "MirrorChyan download failed"; return false; }
    return true;
#else
    (void)archive; error = "installer was built without libcurl"; return false;
#endif
}

}  // namespace baas_installer
