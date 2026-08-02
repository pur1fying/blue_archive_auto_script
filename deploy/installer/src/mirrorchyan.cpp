#include "baas_installer/mirrorchyan.hpp"
#include "baas_installer/curl_runtime.hpp"
#include "baas_installer/process.hpp"

#include <array>
#include <cctype>
#include <fstream>
#include <iomanip>
#include <sstream>

#include <nlohmann/json.hpp>

#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#endif

#ifdef BAAS_INSTALLER_HAS_CURL
#include <curl/curl.h>
#endif

#ifdef BAAS_INSTALLER_HAS_LIBARCHIVE
#include <archive.h>
#include <archive_entry.h>
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

fs::path path_from_utf8(const std::string& value) {
#ifdef _WIN32
    if (value.empty()) return {};
    const int size = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, value.data(), static_cast<int>(value.size()), nullptr, 0);
    if (size <= 0) return {};
    std::wstring wide(static_cast<std::size_t>(size), L'\0');
    MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, value.data(), static_cast<int>(value.size()), wide.data(), size);
    return fs::path(wide);
#else
    return fs::path(value);
#endif
}

bool path_is_within(const fs::path& base, const fs::path& candidate) {
    const auto normalized_base = fs::absolute(base).lexically_normal();
    const auto normalized_candidate = fs::absolute(candidate).lexically_normal();
    auto base_it = normalized_base.begin();
    auto candidate_it = normalized_candidate.begin();
    for (; base_it != normalized_base.end(); ++base_it, ++candidate_it) {
        if (candidate_it == normalized_candidate.end() || *candidate_it != *base_it) return false;
    }
    return true;
}

bool normalize_change_path(const std::string& encoded, const fs::path& source_root, const bool source_required,
                           fs::path& destination, std::string& error) {
    std::string portable = encoded;
    std::replace(portable.begin(), portable.end(), '\\', '/');
    if (portable.empty() || portable.front() == '/' ||
        (portable.size() >= 2 && std::isalpha(static_cast<unsigned char>(portable[0])) && portable[1] == ':')) {
        error = "incremental manifest contains an absolute path";
        return false;
    }
    const auto raw = path_from_utf8(portable);
    if (raw.empty() || raw.is_absolute() || raw.has_root_name()) {
        error = "incremental manifest contains an invalid path";
        return false;
    }
    std::vector<fs::path> components;
    for (const auto& component : raw) {
        if (component == "..") {
            error = "incremental manifest contains path traversal";
            return false;
        }
        if (component != "." && !component.empty()) components.push_back(component);
    }
    if (components.size() < 2) {
        error = "incremental manifest path has no repository prefix";
        return false;
    }
    destination.clear();
    for (std::size_t index = 1; index < components.size(); ++index) destination /= components[index];
    const auto source = source_root / raw;
    if (!path_is_within(source_root, source)) {
        error = "incremental manifest path escapes staging";
        return false;
    }
    if (source_required && !fs::is_regular_file(source)) {
        error = "incremental manifest source file is missing";
        return false;
    }
    return true;
}

#ifdef BAAS_INSTALLER_HAS_CURL
size_t write_file(const char* data, const size_t size, const size_t count, void* context) { return std::fwrite(data, size, count, static_cast<FILE*>(context)); }
size_t write_string(const char* data, const size_t size, const size_t count, void* context) {
    const auto bytes = size * count;
    static_cast<std::string*>(context)->append(data, bytes);
    return bytes;
}
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
    if (result.status == CdkStatus::Valid && result.download_url.empty()) {
        result.status = result.version.empty() ? CdkStatus::Malformed : CdkStatus::UpToDate;
    } else if (result.status == CdkStatus::Valid && !is_sha256(result.sha256)) {
        result.status = CdkStatus::Malformed;
    }
    return result;
}

MirrorRelease request_mirror_release(const std::string& request_url, std::string& error, const long timeout_seconds) {
    error.clear();
#ifdef BAAS_INSTALLER_HAS_CURL
    if (!ensure_curl_initialized()) {
        error = "could not initialize MirrorChyan HTTP runtime";
        MirrorRelease failed; failed.status = CdkStatus::ServerError; return failed;
    }
    CURL* curl = curl_easy_init();
    if (!curl) {
        error = "could not initialize MirrorChyan HTTP client";
        MirrorRelease failed; failed.status = CdkStatus::ServerError; return failed;
    }
    std::string response;
    curl_easy_setopt(curl, CURLOPT_URL, request_url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_string);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_setopt(curl, CURLOPT_FAILONERROR, 1L);
    curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT, timeout_seconds);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, timeout_seconds);
    const auto status = curl_easy_perform(curl);
    curl_easy_cleanup(curl);
    if (status != CURLE_OK) {
        error = "MirrorChyan request failed";
        MirrorRelease failed; failed.status = CdkStatus::ServerError; return failed;
    }
    auto release = parse_mirror_response(response);
    if (release.status == CdkStatus::Malformed) error = "MirrorChyan returned a malformed response";
    return release;
#else
    (void)request_url; (void)timeout_seconds;
    error = "installer was built without libcurl";
    MirrorRelease failed; failed.status = CdkStatus::ServerError; return failed;
#endif
}

std::string mirror_latest_url(const std::string& cdk, const std::string& current_sha, const std::string& channel) {
    return mirror_latest_url(MirrorResource::Main, {}, {}, cdk, current_sha, channel);
}

std::string mirror_latest_url(const MirrorResource resource, const std::string& os, const std::string& arch,
                              const std::string& cdk, const std::string& current_version,
                              const std::string& channel) {
    std::string url = "https://mirrorchyan.com/api/resources/";
    url += resource == MirrorResource::Main ? "BAAS_repo" : "BAAS_Cpp";
    url += "/latest?channel=" + url_encode(channel) + "&current_version=" + url_encode(current_version) +
           "&user_agent=BAAS_GUI";
    if (resource == MirrorResource::Ocr) url += "&os=" + url_encode(os) + "&arch=" + url_encode(arch);
    return url + "&cdk=" + url_encode(cdk);
}

MirrorChanges parse_mirror_changes(const std::string& json_text, const fs::path& source_root, std::string& error) {
    MirrorChanges result;
    error.clear();
    try {
        const auto document = nlohmann::json::parse(json_text);
        for (const auto& [name, required, output] : {
                 std::tuple{"deleted", false, &result.deleted},
                 std::tuple{"added", true, &result.added},
                 std::tuple{"modified", true, &result.modified}}) {
            if (!document.contains(name) || !document.at(name).is_array()) {
                error = std::string("incremental manifest field is not an array: ") + name;
                return {};
            }
            for (const auto& entry : document.at(name)) {
                if (!entry.is_string()) {
                    error = std::string("incremental manifest path is not a string: ") + name;
                    return {};
                }
                fs::path normalized;
                if (!normalize_change_path(entry.get<std::string>(), source_root, required, normalized, error)) return {};
                output->push_back(std::move(normalized));
            }
        }
    } catch (const std::exception& exception) {
        error = std::string("invalid incremental manifest: ") + exception.what();
        return {};
    }
    return result;
}

MirrorPackage inspect_mirror_staging(const MirrorRelease& release, const fs::path& extracted_root,
                                     std::string& error) {
    MirrorPackage package;
    package.version = release.version;
    error.clear();
    if (release.status == CdkStatus::UpToDate) {
        package.mode = MirrorPackageMode::UpToDate;
        return package;
    }
    if (release.status != CdkStatus::Valid) {
        error = "MirrorChyan release is not usable";
        return {};
    }
    if (release.update_type == "incremental") {
        const auto manifest = extracted_root / "changes.json";
        std::ifstream input(manifest, std::ios::binary);
        if (!input) {
            error = "incremental package has no changes.json";
            return {};
        }
        const std::string contents{std::istreambuf_iterator<char>(input), {}};
        package.changes = parse_mirror_changes(contents, extracted_root, error);
        if (!error.empty()) return {};
        package.mode = MirrorPackageMode::Incremental;
        for (const auto& entry : fs::directory_iterator(extracted_root)) {
            if (!entry.is_directory()) continue;
            if (!package.content_root.empty()) {
                error = "incremental package contains more than one root directory";
                return {};
            }
            package.content_root = entry.path();
        }
        if (package.content_root.empty()) {
            error = "incremental package has no content root";
            return {};
        }
        return package;
    }
    if (release.update_type == "full") {
        std::error_code filesystem_error;
        for (const auto& entry : fs::directory_iterator(extracted_root, filesystem_error)) {
            if (filesystem_error) break;
            if (!entry.is_directory()) continue;
            if (!package.content_root.empty()) {
                error = "full package contains more than one root directory";
                return {};
            }
            package.content_root = entry.path();
        }
        if (filesystem_error || package.content_root.empty()) {
            error = "full package has no content root";
            return {};
        }
        package.mode = MirrorPackageMode::Full;
        return package;
    }
    error = "MirrorChyan returned an unknown update type";
    return {};
}

MirrorPlatform current_mirror_platform() {
#ifdef _WIN32
    return {"windows", "amd64"};
#elif defined(__APPLE__) && (defined(__aarch64__) || defined(__arm64__))
    return {"darwin", "arm64"};
#elif defined(__APPLE__)
    return {"darwin", "amd64"};
#elif defined(__aarch64__) || defined(__arm64__)
    return {"linux", "arm64"};
#else
    return {"linux", "amd64"};
#endif
}

bool validate_archive_entries(const std::vector<std::string>& entries, std::string& error) {
    error.clear();
    for (const auto& entry : entries) {
        std::string portable = entry;
        std::replace(portable.begin(), portable.end(), '\\', '/');
        if (portable.empty() || portable.front() == '/' ||
            (portable.size() >= 2 && std::isalpha(static_cast<unsigned char>(portable[0])) && portable[1] == ':')) {
            error = "archive contains an absolute path";
            return false;
        }
        const auto path = path_from_utf8(portable);
        if (path.empty() || path.is_absolute() || path.has_root_name()) {
            error = "archive contains an invalid path";
            return false;
        }
        for (const auto& component : path) {
            if (component == "..") {
                error = "archive contains path traversal";
                return false;
            }
        }
    }
    return true;
}

bool extract_mirror_archive(const fs::path& archive, const fs::path& destination, std::string& error,
                            const std::function<void(std::string_view)>& on_chunk) {
    error.clear();
#ifdef BAAS_INSTALLER_HAS_LIBARCHIVE
    struct archive* reader = archive_read_new();
    if (!reader) {
        error = "could not initialize archive reader";
        return false;
    }
    archive_read_support_filter_all(reader);
    archive_read_support_format_all(reader);
#ifdef _WIN32
    const auto opened = archive_read_open_filename_w(reader, archive.c_str(), 10240);
#else
    const auto opened = archive_read_open_filename(reader, archive.c_str(), 10240);
#endif
    if (opened != ARCHIVE_OK) {
        error = "could not open MirrorChyan archive";
        archive_read_free(reader);
        return false;
    }
    std::error_code ignored;
    fs::remove_all(destination, ignored);
    fs::create_directories(destination, ignored);
    if (ignored) {
        error = "could not create archive extraction directory";
        archive_read_free(reader);
        return false;
    }
    archive_entry* entry = nullptr;
    std::array<char, 65536> buffer{};
    int header_status = ARCHIVE_OK;
    while ((header_status = archive_read_next_header(reader, &entry)) == ARCHIVE_OK) {
        fs::path relative;
#ifdef _WIN32
        if (const auto* utf8 = archive_entry_pathname_utf8(entry)) relative = path_from_utf8(utf8);
        else if (const auto* wide = archive_entry_pathname_w(entry)) relative = fs::path(wide);
#else
        if (const auto* utf8 = archive_entry_pathname_utf8(entry)) relative = fs::path(utf8);
        else if (const auto* native = archive_entry_pathname(entry)) relative = fs::path(native);
#endif
        const auto encoded = relative.generic_u8string();
        const std::string portable(encoded.begin(), encoded.end());
        if (!validate_archive_entries({portable}, error)) {
            archive_read_free(reader);
            return false;
        }
        if (archive_entry_symlink(entry) || archive_entry_hardlink(entry)) {
            error = "archive contains an unsupported link";
            archive_read_free(reader);
            return false;
        }
        const auto output = destination / relative;
        const auto type = archive_entry_filetype(entry);
        if (type == AE_IFDIR) {
            fs::create_directories(output, ignored);
            archive_read_data_skip(reader);
        } else if (type == AE_IFREG) {
            fs::create_directories(output.parent_path(), ignored);
            std::ofstream stream(output, std::ios::binary | std::ios::trunc);
            if (!stream) {
                error = "could not create extracted archive file";
                archive_read_free(reader);
                return false;
            }
            for (;;) {
                const auto count = archive_read_data(reader, buffer.data(), buffer.size());
                if (count == 0) break;
                if (count < 0) {
                    error = "could not read MirrorChyan archive data";
                    archive_read_free(reader);
                    return false;
                }
                stream.write(buffer.data(), count);
            }
            if (!stream) {
                error = "could not write extracted archive file";
                archive_read_free(reader);
                return false;
            }
#ifndef _WIN32
            const auto mode = static_cast<fs::perms>(archive_entry_perm(entry) & 0777);
            fs::permissions(output, mode, fs::perm_options::replace, ignored);
            if (ignored) {
                error = "could not preserve extracted archive permissions";
                archive_read_free(reader);
                return false;
            }
#endif
        } else {
            error = "archive contains an unsupported entry type";
            archive_read_free(reader);
            return false;
        }
        if (on_chunk) on_chunk("Extracting " + portable + "\r");
    }
    if (header_status != ARCHIVE_EOF) {
        error = "could not finish reading MirrorChyan archive";
        archive_read_free(reader);
        return false;
    }
    archive_read_free(reader);
    return true;
#else
    ProcessSpec listing;
    listing.arguments = {"tar", "-tf", archive.string()};
    const auto listed = run_process(listing);
    if (listed.exit_code != 0) {
        error = "could not list MirrorChyan archive";
        return false;
    }
    std::vector<std::string> entries;
    std::istringstream lines(listed.output);
    for (std::string line; std::getline(lines, line);) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (!line.empty()) entries.push_back(std::move(line));
    }
    if (entries.empty() || !validate_archive_entries(entries, error)) return false;
    std::error_code ignored;
    fs::remove_all(destination, ignored);
    fs::create_directories(destination, ignored);
    if (ignored) {
        error = "could not create MirrorChyan extraction directory";
        return false;
    }
    ProcessSpec extraction;
    extraction.arguments = {"tar", "-xf", archive.string(), "-C", destination.string()};
    extraction.use_pty = true;
    extraction.on_chunk = on_chunk;
    extraction.timeout = std::chrono::minutes(5);
    if (run_terminal_process(extraction).exit_code != 0) {
        fs::remove_all(destination, ignored);
        error = "could not extract MirrorChyan archive";
        return false;
    }
    return true;
#endif
}

MirrorRelease wait_for_incremental_release(MirrorRelease initial,
                                           const std::function<MirrorRelease()>& refresh,
                                           const std::function<void()>& wait,
                                           const int maximum_attempts) {
    if (initial.update_type != "full" || !refresh || maximum_attempts <= 0) return initial;
    for (int attempt = 0; attempt < maximum_attempts; ++attempt) {
        if (wait) wait();
        auto next = refresh();
        if (next.status != CdkStatus::Valid) return next;
        initial = std::move(next);
        if (initial.update_type == "incremental") break;
    }
    return initial;
}

bool download_mirror_package(const MirrorRelease& release, const fs::path& archive, std::string& error,
                             MirrorDownloadProgress on_progress) {
    if (release.status != CdkStatus::Valid || !is_sha256(release.sha256)) { error = "MirrorChyan response has no verifiable package"; return false; }
#ifdef BAAS_INSTALLER_HAS_CURL
    if (!ensure_curl_initialized()) { error = "cannot initialize HTTP runtime"; return false; }
    fs::create_directories(archive.parent_path());
    FILE* output = std::fopen(archive.string().c_str(), "wb"); if (!output) { error = "cannot create staging archive"; return false; }
    CURL* curl = curl_easy_init();
    if (!curl) { std::fclose(output); error = "cannot initialize HTTP client"; return false; }
    curl_easy_setopt(curl, CURLOPT_URL, release.download_url.c_str()); curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_file); curl_easy_setopt(curl, CURLOPT_WRITEDATA, output); curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L); curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT, 5L); curl_easy_setopt(curl, CURLOPT_TIMEOUT, 600L);
    if (on_progress) {
        curl_easy_setopt(curl, CURLOPT_NOPROGRESS, 0L);
        curl_easy_setopt(curl, CURLOPT_XFERINFODATA, &on_progress);
        curl_easy_setopt(curl, CURLOPT_XFERINFOFUNCTION,
            +[](void* payload, const curl_off_t total, const curl_off_t downloaded, curl_off_t, curl_off_t) -> int {
                auto* callback = static_cast<MirrorDownloadProgress*>(payload);
                (*callback)(downloaded > 0 ? static_cast<std::uint64_t>(downloaded) : 0,
                            total > 0 ? static_cast<std::uint64_t>(total) : 0);
                return 0;
            });
    }
    const auto status = curl_easy_perform(curl); curl_easy_cleanup(curl); std::fclose(output);
    if (status != CURLE_OK || !verify_sha256(archive, release.sha256)) { fs::remove(archive); error = status == CURLE_OK ? "MirrorChyan SHA-256 mismatch" : "MirrorChyan download failed"; return false; }
    if (on_progress) {
        std::error_code size_error;
        const auto size = fs::file_size(archive, size_error);
        if (!size_error) on_progress(size, size);
    }
    return true;
#else
    (void)archive; error = "installer was built without libcurl"; return false;
#endif
}

}  // namespace baas_installer
