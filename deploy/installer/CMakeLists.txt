cmake_minimum_required(VERSION 3.25)

project(BAASInstaller VERSION 2.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(MSVC AND VCPKG_TARGET_TRIPLET MATCHES "-static$")
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
endif()

if(MSVC)
    add_compile_options(/utf-8)
elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    add_compile_options(-finput-charset=UTF-8 -fexec-charset=UTF-8)
endif()

find_package(ftxui CONFIG QUIET)
if(NOT TARGET ftxui::component)
    include(FetchContent)
    set(FTXUI_BUILD_DOCS OFF CACHE BOOL "" FORCE)
    set(FTXUI_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
    set(FTXUI_BUILD_TESTS OFF CACHE BOOL "" FORCE)
    FetchContent_Declare(ftxui
        URL https://github.com/ArthurSonzogni/FTXUI/archive/refs/tags/v6.1.9.tar.gz
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    )
    FetchContent_MakeAvailable(ftxui)
endif()

find_package(nlohmann_json CONFIG QUIET)
if(NOT TARGET nlohmann_json::nlohmann_json)
    include(FetchContent)
    FetchContent_Declare(nlohmann_json
        URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.tar.xz
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    )
    FetchContent_MakeAvailable(nlohmann_json)
endif()

add_library(baas-installer-core STATIC
    src/curl_runtime.cpp
    src/digest.cpp
    src/dependency_state.cpp
    src/paths.cpp
    src/config.cpp
    src/sources.cpp
    src/git.cpp
    src/transaction.cpp
    src/uv_environment.cpp
    src/process.cpp
    src/mirrorchyan.cpp
    src/workflow.cpp
    src/tui.cpp
    src/localization.cpp
    src/logging.cpp
)
target_include_directories(baas-installer-core PUBLIC include)
target_link_libraries(baas-installer-core PUBLIC ftxui::component ftxui::dom ftxui::screen nlohmann_json::nlohmann_json)

if(UNIX)
    find_library(BAAS_INSTALLER_UTIL_LIBRARY util)
    if(BAAS_INSTALLER_UTIL_LIBRARY)
        target_link_libraries(baas-installer-core PRIVATE ${BAAS_INSTALLER_UTIL_LIBRARY})
    endif()
endif()

find_package(CURL QUIET)
if(TARGET CURL::libcurl)
    target_link_libraries(baas-installer-core PRIVATE CURL::libcurl)
    target_compile_definitions(baas-installer-core PRIVATE BAAS_INSTALLER_HAS_CURL=1)
endif()

find_package(LibArchive QUIET)
if(TARGET LibArchive::LibArchive)
    if(WIN32 AND DEFINED VCPKG_INSTALLED_DIR AND DEFINED VCPKG_TARGET_TRIPLET)
        set(_baas_archive_root "${VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}")
        if(EXISTS "${_baas_archive_root}/lib/archive.lib" AND EXISTS "${_baas_archive_root}/debug/lib/archive.lib")
            set_target_properties(LibArchive::LibArchive PROPERTIES
                IMPORTED_LOCATION_RELEASE "${_baas_archive_root}/lib/archive.lib"
                IMPORTED_LOCATION_RELWITHDEBINFO "${_baas_archive_root}/lib/archive.lib"
                IMPORTED_LOCATION_MINSIZEREL "${_baas_archive_root}/lib/archive.lib"
                IMPORTED_LOCATION_DEBUG "${_baas_archive_root}/debug/lib/archive.lib")
        endif()
        unset(_baas_archive_root)
    endif()
    target_link_libraries(baas-installer-core PRIVATE LibArchive::LibArchive)
    target_compile_definitions(baas-installer-core PRIVATE BAAS_INSTALLER_HAS_LIBARCHIVE=1)
endif()

find_package(libgit2 CONFIG QUIET)
if(TARGET libgit2::libgit2)
    target_link_libraries(baas-installer-core PRIVATE libgit2::libgit2)
    target_compile_definitions(baas-installer-core PRIVATE BAAS_INSTALLER_HAS_LIBGIT2=1)
elseif(TARGET libgit2::libgit2package)
    target_link_libraries(baas-installer-core PRIVATE libgit2::libgit2package)
    target_compile_definitions(baas-installer-core PRIVATE BAAS_INSTALLER_HAS_LIBGIT2=1)
endif()

add_executable(BlueArchiveAutoScript src/main.cpp)
target_link_libraries(BlueArchiveAutoScript PRIVATE baas-installer-core)
if(WIN32)
    enable_language(RC)
    target_sources(BlueArchiveAutoScript PRIVATE src/installer.manifest src/installer.rc)
endif()

include(CTest)
if(BUILD_TESTING)
    add_executable(baas-installer-test-digest tests/test_digest.cpp)
    target_link_libraries(baas-installer-test-digest PRIVATE baas-installer-core)
    add_test(NAME digest COMMAND baas-installer-test-digest)

    add_executable(baas-installer-test-dependency-state tests/test_dependency_state.cpp)
    target_link_libraries(baas-installer-test-dependency-state PRIVATE baas-installer-core)
    add_test(NAME dependency-state COMMAND baas-installer-test-dependency-state)

    add_executable(baas-installer-test-paths tests/test_paths.cpp)
    target_link_libraries(baas-installer-test-paths PRIVATE baas-installer-core)
    add_test(NAME paths COMMAND baas-installer-test-paths)

    add_executable(baas-installer-test-config tests/test_config.cpp)
    target_link_libraries(baas-installer-test-config PRIVATE baas-installer-core)
    add_test(NAME config COMMAND baas-installer-test-config)

    add_executable(baas-installer-test-sources tests/test_sources.cpp)
    target_link_libraries(baas-installer-test-sources PRIVATE baas-installer-core)
    add_test(NAME sources COMMAND baas-installer-test-sources)

    add_executable(baas-installer-test-git tests/test_git.cpp)
    target_link_libraries(baas-installer-test-git PRIVATE baas-installer-core)
    if(TARGET libgit2::libgit2 OR TARGET libgit2::libgit2package)
        target_compile_definitions(baas-installer-test-git PRIVATE BAAS_INSTALLER_TEST_HAS_LIBGIT2=1)
    endif()
    add_test(NAME git COMMAND baas-installer-test-git)

    add_executable(baas-installer-test-transaction tests/test_transaction.cpp)
    target_link_libraries(baas-installer-test-transaction PRIVATE baas-installer-core)
    add_test(NAME transaction COMMAND baas-installer-test-transaction)

    add_executable(baas-installer-test-uv tests/test_uv_environment.cpp)
    target_link_libraries(baas-installer-test-uv PRIVATE baas-installer-core)
    add_test(NAME uv COMMAND baas-installer-test-uv)

    add_executable(baas-installer-test-mirrorchyan tests/test_mirrorchyan.cpp)
    target_link_libraries(baas-installer-test-mirrorchyan PRIVATE baas-installer-core)
    if(TARGET CURL::libcurl)
        target_compile_definitions(baas-installer-test-mirrorchyan PRIVATE BAAS_INSTALLER_TEST_HAS_CURL=1)
    endif()
    add_test(NAME mirrorchyan COMMAND baas-installer-test-mirrorchyan)

    add_executable(baas-installer-test-workflow tests/test_workflow.cpp)
    target_link_libraries(baas-installer-test-workflow PRIVATE baas-installer-core)
    add_test(NAME workflow COMMAND baas-installer-test-workflow)

    add_executable(baas-installer-test-tui tests/test_tui.cpp)
    target_link_libraries(baas-installer-test-tui PRIVATE baas-installer-core)
    add_test(NAME tui COMMAND baas-installer-test-tui)

    add_executable(baas-installer-test-process tests/test_process.cpp)
    target_link_libraries(baas-installer-test-process PRIVATE baas-installer-core)
    add_test(NAME process COMMAND baas-installer-test-process)

    add_executable(baas-installer-test-localization tests/test_localization.cpp)
    target_link_libraries(baas-installer-test-localization PRIVATE baas-installer-core)
    add_test(NAME localization COMMAND baas-installer-test-localization)

    add_executable(baas-installer-test-logging tests/test_logging.cpp)
    target_link_libraries(baas-installer-test-logging PRIVATE baas-installer-core)
    add_test(NAME logging COMMAND baas-installer-test-logging)

    if(WIN32)
        add_executable(baas-installer-test-icon tests/test_icon.cpp)
        add_test(NAME icon COMMAND baas-installer-test-icon $<TARGET_FILE:BlueArchiveAutoScript>)
    endif()

    find_package(Python3 COMPONENTS Interpreter QUIET)
    if(Python3_Interpreter_FOUND)
        add_test(NAME ocr-managed-marker COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tests/test_ocr_managed_marker.py)
    endif()
endif()
