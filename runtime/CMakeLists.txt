cmake_minimum_required(VERSION 3.4)
project(cobra_runtime)

set(CMAKE_C_STANDARD 99)
set(CMAKE_BUILD_TYPE Release)

add_executable(cobra_runtime runtime_test.c)
target_include_directories(cobra_runtime
    PRIVATE
        "${PROJECT_SOURCE_DIR}/cobra/include"
        "${PROJECT_SOURCE_DIR}/cobra/demo/c/dr_libs"
)
target_link_libraries(cobra_runtime dl)
