cmake_minimum_required(VERSION 3.25)

project(BAASInstaller VERSION 2.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(baas-installer-core STATIC
    src/paths.cpp
    src/config.cpp
    src/sources.cpp
    src/git.cpp
    src/transaction.cpp
)
target_include_directories(baas-installer-core PUBLIC include)

find_package(libgit2 CONFIG QUIET)
if(TARGET libgit2::libgit2)
    target_link_libraries(baas-installer-core PRIVATE libgit2::libgit2)
    target_compile_definitions(baas-installer-core PRIVATE BAAS_INSTALLER_HAS_LIBGIT2=1)
endif()

add_executable(BlueArchiveAutoScript src/main.cpp)
target_link_libraries(BlueArchiveAutoScript PRIVATE baas-installer-core)

include(CTest)
if(BUILD_TESTING)
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
    add_test(NAME git COMMAND baas-installer-test-git)

    add_executable(baas-installer-test-transaction tests/test_transaction.cpp)
    target_link_libraries(baas-installer-test-transaction PRIVATE baas-installer-core)
    add_test(NAME transaction COMMAND baas-installer-test-transaction)
endif()
