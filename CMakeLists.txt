cmake_minimum_required(VERSION 3.10)

if(NOT DEFINED CMAKE_TOOLCHAIN_FILE)
  if(DEFINED ENV{VITASDK})
    set(CMAKE_TOOLCHAIN_FILE "$ENV{VITASDK}/share/vita.toolchain.cmake" CACHE PATH "VitaSDK toolchain")
  else()
    message(FATAL_ERROR "VITASDK is not set")
  endif()
endif()

project(mightymicros C)

include("${VITASDK}/share/vita.cmake" REQUIRED)

set(VITA_APP_NAME "LEGO DC Mighty Micros")
set(VITA_TITLEID "MTHM00001")
set(VITA_VERSION "01.00")

add_executable(${PROJECT_NAME} main.c)
target_link_libraries(${PROJECT_NAME}
  vitaGL
  SceCtrl_stub
  SceIo_stub
  SceKernel_stub
  SceDisplay_stub
  SceGxm_stub
  SceSysmodule_stub
  m
)

vita_create_vpk(${PROJECT_NAME}.vpk ${VITA_TITLEID} ${PROJECT_NAME}
  NAME ${VITA_APP_NAME}
  VERSION ${VITA_VERSION}
  FILE data data
)
