#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include <filesystem>
#include <iostream>

int main(const int argc, const char* argv[]) {
    if (argc != 2) {
        std::cerr << "expected installer executable path\n";
        return 1;
    }
    const auto executable = std::filesystem::absolute(argv[1]);
    const auto image = LoadLibraryExW(executable.c_str(), nullptr, LOAD_LIBRARY_AS_DATAFILE);
    if (image == nullptr) {
        std::cerr << "could not load installer resources\n";
        return 1;
    }
    const auto icon = FindResourceW(image, MAKEINTRESOURCEW(101), MAKEINTRESOURCEW(14));
    FreeLibrary(image);
    if (icon == nullptr) {
        std::cerr << "installer does not contain BAAS icon resource 101\n";
        return 1;
    }
    return 0;
}
