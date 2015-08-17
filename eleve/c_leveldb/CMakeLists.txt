cmake_minimum_required( VERSION 2.8 )

project( cleveldb )

SET(CMAKE_CXX_FLAGS "-std=c++0x")

# Find necessary packages
find_package( PythonLibs 3.2 REQUIRED )
include_directories( ${PYTHON_INCLUDE_DIRS} )

find_package( Boost COMPONENTS python REQUIRED )
include_directories( ${Boost_INCLUDE_DIR} )

# Build our library
file(GLOB source "*.h" "*.cpp")
add_library( cleveldb SHARED ${source} )
target_link_libraries(cleveldb ${Boost_LIBRARIES})

set_target_properties( cleveldb PROPERTIES PREFIX "" )
