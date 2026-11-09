cmake_minimum_required(VERSION 3.10)

if(NOT DEFINED CMAKE_TOOLCHAIN_FILE)
  if(DEFINED ENV{VITASDK})
    set(CMAKE_TOOLCHAIN_FILE "$ENV{VITASDK}/share/vita.toolchain.cmake" CACHE PATH "toolchain file")
  else()
    message(FATAL_ERROR "Please define VITASDK to point to your SDK installation path!")
  endif()
endif()

project(mightymicros)

include("${VITASDK}/share/vita.cmake" REQUIRED)

set(VITA_APP_NAME "LEGO DC Mighty Micros")
set(VITA_TITLEID "MTHMICROS")
set(VITA_VERSION "01.00")

# Source files
set(SOURCES main.c)

# Create ELF executable
add_executable(${PROJECT_NAME} ${SOURCES})

# Include directories
target_include_directories(${PROJECT_NAME} PRIVATE ${CMAKE_SOURCE_DIR})

# Libraries to link
target_link_libraries(${PROJECT_NAME}
  vitaGL
  mathneon
  vitashark
  SceShaccCgExt
  kubridge_stub
  SceTouch_stub
  SceCtrl_stub
  SceDisplay_stub
  SceIofilemgr_stub
  SceGxm_stub
  SceSysmodule_stub
  taihen_stub
  stdc++
  m
)

# Generate VPK package using the modern vitasdk macro
vita_create_vpk(${PROJECT_NAME}.vpk ${VITA_TITLEID} ${PROJECT_NAME}
  NAME ${VITA_APP_NAME}
  VERSION ${VITA_VERSION}
)
