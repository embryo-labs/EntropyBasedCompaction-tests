cmake_minimum_required(VERSION 3.2)
project(main)

IF (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Release" CACHE STRING
        "Choose the type of build, options are: Debug Release RelWithDebInfo MinSizeRel." FORCE)
ENDIF()
add_compile_options(-Wall -Wextra -fexceptions)

aux_source_directory(src SRCS)
add_executable(${PROJECT_NAME} ${SRCS})
target_include_directories(${PROJECT_NAME}
	PRIVATE
		${PROJECT_SOURCE_DIR}/include
)
target_link_libraries(${PROJECT_NAME}
	PRIVATE
)
# target_compile_features can omit -std flag in compile_commands.json
# https://gitlab.kitware.com/cmake/cmake/-/issues/23397
set_target_properties(${PROJECT_NAME} PROPERTIES CXX_STANDARD 17)

#target_compile_features(${PROJECT_NAME} PRIVATE c_auto_type)
set(CMAKE_C_STANDARD 11)
