cmake_minimum_required( VERSION 2.8 )

project( cmemory )

SET(CMAKE_CXX_FLAGS "-std=c++0x")

if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")
    message(WARNING "If you use GCC, the memory consumption will be higher because it doesn't support packing non-POD fields. You should try Clang :)")
endif()

# Find necessary packages
find_package( PythonLibs 3.2 REQUIRED )
include_directories( ${PYTHON_INCLUDE_DIRS} )

find_package( Boost COMPONENTS python3 REQUIRED )
include_directories( ${Boost_INCLUDE_DIR} )

# Build our library
file(GLOB source "*.h" "*.cpp")
add_library( cmemory SHARED ${source} )
target_link_libraries(cmemory ${Boost_LIBRARIES})

set_target_properties( cmemory PROPERTIES PREFIX "" )
