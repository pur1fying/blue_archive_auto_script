#include "baas_installer/digest.hpp"

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <sstream>

namespace baas_installer {
namespace {

class Sha256 {
public:
    Sha256() : state_{0x6a09e667U, 0xbb67ae85U, 0x3c6ef372U, 0xa54ff53aU,
                       0x510e527fU, 0x9b05688cU, 0x1f83d9abU, 0x5be0cd19U} {}

    void update(const unsigned char* data, std::size_t size) {
        bit_count_ += static_cast<std::uint64_t>(size) * 8;
        while (size != 0) {
            const auto take = std::min<std::size_t>(size, 64 - used_);
            std::copy_n(data, take, block_.begin() + used_);
            used_ += take;
            data += take;
            size -= take;
            if (used_ == 64) {
                transform();
                used_ = 0;
            }
        }
    }

    std::string finish() {
        const auto bits = bit_count_;
        const unsigned char one = 0x80;
        update(&one, 1);
        const unsigned char zero = 0;
        while (used_ != 56) update(&zero, 1);
        std::array<unsigned char, 8> length{};
        for (int index = 0; index != 8; ++index) {
            length[7 - index] = static_cast<unsigned char>(bits >> (index * 8));
        }
        update(length.data(), length.size());
        std::ostringstream output;
        for (const auto word : state_) {
            for (int shift = 24; shift >= 0; shift -= 8) {
                output << std::hex << std::setw(2) << std::setfill('0') << ((word >> shift) & 0xff);
            }
        }
        return output.str();
    }

private:
    static constexpr std::array<std::uint32_t, 64> constants_{
        0x428a2f98U,0x71374491U,0xb5c0fbcfU,0xe9b5dba5U,0x3956c25bU,0x59f111f1U,0x923f82a4U,0xab1c5ed5U,
        0xd807aa98U,0x12835b01U,0x243185beU,0x550c7dc3U,0x72be5d74U,0x80deb1feU,0x9bdc06a7U,0xc19bf174U,
        0xe49b69c1U,0xefbe4786U,0x0fc19dc6U,0x240ca1ccU,0x2de92c6fU,0x4a7484aaU,0x5cb0a9dcU,0x76f988daU,
        0x983e5152U,0xa831c66dU,0xb00327c8U,0xbf597fc7U,0xc6e00bf3U,0xd5a79147U,0x06ca6351U,0x14292967U,
        0x27b70a85U,0x2e1b2138U,0x4d2c6dfcU,0x53380d13U,0x650a7354U,0x766a0abbU,0x81c2c92eU,0x92722c85U,
        0xa2bfe8a1U,0xa81a664bU,0xc24b8b70U,0xc76c51a3U,0xd192e819U,0xd6990624U,0xf40e3585U,0x106aa070U,
        0x19a4c116U,0x1e376c08U,0x2748774cU,0x34b0bcb5U,0x391c0cb3U,0x4ed8aa4aU,0x5b9cca4fU,0x682e6ff3U,
        0x748f82eeU,0x78a5636fU,0x84c87814U,0x8cc70208U,0x90befffaU,0xa4506cebU,0xbef9a3f7U,0xc67178f2U};

    static std::uint32_t rotate_right(const std::uint32_t value, const int count) {
        return (value >> count) | (value << (32 - count));
    }

    void transform() {
        std::array<std::uint32_t, 64> words{};
        for (int index = 0; index < 16; ++index) {
            words[index] = (std::uint32_t(block_[index * 4]) << 24) |
                           (std::uint32_t(block_[index * 4 + 1]) << 16) |
                           (std::uint32_t(block_[index * 4 + 2]) << 8) |
                           block_[index * 4 + 3];
        }
        for (int index = 16; index < 64; ++index) {
            const auto first = rotate_right(words[index - 15], 7) ^ rotate_right(words[index - 15], 18) ^
                               (words[index - 15] >> 3);
            const auto second = rotate_right(words[index - 2], 17) ^ rotate_right(words[index - 2], 19) ^
                                (words[index - 2] >> 10);
            words[index] = words[index - 16] + first + words[index - 7] + second;
        }
        auto a = state_[0], b = state_[1], c = state_[2], d = state_[3];
        auto e = state_[4], f = state_[5], g = state_[6], h = state_[7];
        for (int index = 0; index < 64; ++index) {
            const auto first = rotate_right(e, 6) ^ rotate_right(e, 11) ^ rotate_right(e, 25);
            const auto choice = (e & f) ^ ((~e) & g);
            const auto temporary_one = h + first + choice + constants_[index] + words[index];
            const auto second = rotate_right(a, 2) ^ rotate_right(a, 13) ^ rotate_right(a, 22);
            const auto majority = (a & b) ^ (a & c) ^ (b & c);
            const auto temporary_two = second + majority;
            h = g; g = f; f = e; e = d + temporary_one;
            d = c; c = b; b = a; a = temporary_one + temporary_two;
        }
        state_[0] += a; state_[1] += b; state_[2] += c; state_[3] += d;
        state_[4] += e; state_[5] += f; state_[6] += g; state_[7] += h;
    }

    std::array<unsigned char, 64> block_{};
    std::array<std::uint32_t, 8> state_{};
    std::uint64_t bit_count_{};
    std::size_t used_{};
};

std::string lower(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](const unsigned char character) {
        return static_cast<char>(std::tolower(character));
    });
    return value;
}

}  // namespace

bool is_sha256(const std::string_view digest) {
    return digest.size() == 64 && std::all_of(digest.begin(), digest.end(), [](const unsigned char character) {
        return std::isxdigit(character) != 0;
    });
}

std::string sha256_bytes(const std::string_view bytes) {
    Sha256 hash;
    hash.update(reinterpret_cast<const unsigned char*>(bytes.data()), bytes.size());
    return hash.finish();
}

std::string sha256_file(const std::filesystem::path& file) {
    std::ifstream input(file, std::ios::binary);
    if (!input) return {};
    Sha256 hash;
    std::array<unsigned char, 8192> bytes{};
    while (input) {
        input.read(reinterpret_cast<char*>(bytes.data()), bytes.size());
        hash.update(bytes.data(), static_cast<std::size_t>(input.gcount()));
    }
    return hash.finish();
}

bool verify_sha256(const std::filesystem::path& file, const std::string_view expected_digest) {
    if (!is_sha256(expected_digest)) return false;
    const auto actual = sha256_file(file);
    return !actual.empty() && lower(actual) == lower(std::string(expected_digest));
}

}  // namespace baas_installer
