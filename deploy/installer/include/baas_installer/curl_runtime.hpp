#pragma once

namespace baas_installer {

// Initializes libcurl once for the lifetime of the process. This must be
// called before easy handles are created from concurrent worker threads.
bool ensure_curl_initialized();

}  // namespace baas_installer
