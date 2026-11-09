cmake_minimum_required(VERSION 3.10)

if(NOT DEFINED CMAKE_TOOLCHAIN_FILE)
  if(DEFINED ENV{VITASDK})
    set(CMAKE_TOOLCHAIN_FILE "$ENV{VITASDK}/share/vita.toolchain.cmake" CACHE PATH "toolchain file")
  else()
    message(FATAL_ERROR "Please define VITASDK to point to your SDK installation path!")
  endif()
endif()

project(vita_port)

include("${VITASDK}/share/vita.cmake" REQUIRED)

set(VITA_APP_NAME "My Vita Port")
set(VITA_TITLEID "VITA00001")
set(VITA_VERSION "01.00")

# Source files
set(SOURCES main.c)

# Create ELF executable
add_executable(vita_port ${SOURCES})

# Include directories
target_include_directories(vita_port PRIVATE ${CMAKE_SOURCE_DIR})

# Libraries to link (vitaGL, kubridge, math, system libs)
target_link_libraries(vita_port
  vitaGL
  kuBridge_stub
  SceTouch_stub
  SceCtrl_stub
  SceDisplay_stub
  SceGxm_stub
  SceSysmodule_stub
  m
)

# Generate VPK package
vita_create_stubs(vita_port)
vita_make_vpk(vita_port.vpk ${VITA_TITLEID} vita_port
  NAME ${VITA_APP_NAME}
  VERSION ${VITA_VERSION}
)
