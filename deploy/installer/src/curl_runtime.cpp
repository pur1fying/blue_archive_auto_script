#include "baas_installer/curl_runtime.hpp"

#ifdef BAAS_INSTALLER_HAS_CURL
#include <curl/curl.h>
#endif

namespace baas_installer {

bool ensure_curl_initialized() {
#ifdef BAAS_INSTALLER_HAS_CURL
    class CurlRuntime {
      public:
        CurlRuntime() : initialized_(curl_global_init(CURL_GLOBAL_DEFAULT) == CURLE_OK) {}
        ~CurlRuntime() {
            if (initialized_) curl_global_cleanup();
        }
        bool initialized() const { return initialized_; }

      private:
        bool initialized_;
    };
    static const CurlRuntime runtime;
    return runtime.initialized();
#else
    return false;
#endif
}

}  // namespace baas_installer
