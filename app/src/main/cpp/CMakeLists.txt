cmake_minimum_required(VERSION 3.22.1)

project("offlinelicensingmodel")

# Biên dịch thư viện native C++ kèm module xác thực Ed25519 thuần C
add_library(${CMAKE_PROJECT_NAME} SHARED
        native-lib.cpp
        ed25519/fe.c
        ed25519/ge.c
        ed25519/sc.c
        ed25519/sha512.c
        ed25519/verify.c
)

target_include_directories(${CMAKE_PROJECT_NAME} PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}/ed25519
)

target_link_libraries(${CMAKE_PROJECT_NAME}
        android
        log
)
