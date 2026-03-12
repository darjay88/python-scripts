#include <iostream>
#include <string>
#include <filesystem>
#include <cstdlib>
#include <array>
#include <memory>

namespace fs = std::filesystem;

std::string executeCommand(const std::string& command) {
    std::array<char, 128> buffer;
    std::string result;
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(command.c_str(), "r"), &pclose);
    if (!pipe) {
        throw std::runtime_error("popen() failed!");
    }
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        result += buffer.data();
    }
    return result;
}

void sendFileViaAdb(const fs::path& filePath, const std::string& deviceId) {
    try {
        std::string command = "adb push \"" + filePath.string() + "\" \"/storage/self/primary/Arch-Files/" + filePath.filename().string() + "\"";
        std::cout << "Sending " << filePath << " to Android device " << deviceId << "..." << std::endl;
        
        std::string output = executeCommand(command);
        std::cout << output;
        
        int returnCode = system(command.c_str());
        if (returnCode == 0) {
            std::cout << "Successfully sent " << filePath.filename() << " to " << deviceId << "." << std::endl;
        } else {
            std::cout << "Error sending " << filePath.filename() << std::endl;
        }
    } catch (const std::exception& e) {
        std::cerr << "An unexpected error occurred: " << e.what() << std::endl;
    }
}

void sendDirectoryViaAdb(const fs::path& directoryPath, const std::string& deviceId) {
    try {
        for (const auto& entry : fs::recursive_directory_iterator(directoryPath)) {
            if (fs::is_regular_file(entry)) {
                sendFileViaAdb(entry.path(), deviceId);
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "An unexpected error occurred: " << e.what() << std::endl;
    }
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cout << "Usage: " << argv[0] << " <file_or_directory_path> <device_id>" << std::endl;
        return 1;
    }

    std::string path = argv[1];
    std::string deviceId = argv[2];

    try {
        if (fs::is_regular_file(path)) {
            sendFileViaAdb(fs::path(path), deviceId);
        } else if (fs::is_directory(path)) {
            sendDirectoryViaAdb(fs::path(path), deviceId);
        } else {
            std::cout << "Provided path is neither a file nor a directory." << std::endl;
        }
    } catch (const std::exception& e) {
        std::cerr << "An error occurred: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}