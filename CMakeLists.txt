cmake_minimum_required(VERSION 3.14)

if(NOT EXISTS "${CMAKE_SOURCE_DIR}/vendor/soloader/CMakeLists.txt")
  message(FATAL_ERROR "The Android-to-Vita loader framework is missing. Run the GitHub Actions workflow or clone vendor/soloader with its submodules.")
endif()

add_subdirectory(vendor/soloader)
