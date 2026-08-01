cmake_minimum_required(VERSION 3.25)

project(BAASInstaller VERSION 2.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(baas-installer-core STATIC
    src/paths.cpp
)
target_include_directories(baas-installer-core PUBLIC include)

add_executable(BlueArchiveAutoScript src/main.cpp)
target_link_libraries(BlueArchiveAutoScript PRIVATE baas-installer-core)

include(CTest)
if(BUILD_TESTING)
    add_executable(baas-installer-test-paths tests/test_paths.cpp)
    target_link_libraries(baas-installer-test-paths PRIVATE baas-installer-core)
    add_test(NAME paths COMMAND baas-installer-test-paths)
endif()
