cmake_minimum_required( VERSION 2.8 )

project( cleveldb )

SET(CMAKE_CXX_FLAGS "-std=c++0x")

foreach(Boost_Python_Lib "python3" "python-py3" "python-py34" "python-py33" "python-py35" "python-py36")
    find_package(Boost COMPONENTS ${Boost_Python_Lib} QUIET )
    if(Boost_FOUND)
        break()
    endif()
endforeach()
# If boost-python3 not found, just find boost-python and hope that it is compatible with python3
if(NOT Boost_FOUND)
  find_package(Boost COMPONENTS python REQUIRED)
endif()

set(Python_ADDITIONAL_VERSIONS "3.2" "3.3" "3.4" "3.5" "3.6")
find_package(PythonLibs 3.2 REQUIRED)

include_directories( ${PYTHON_INCLUDE_DIRS} )
include_directories( ${Boost_INCLUDE_DIR} )

find_library(LEVELDB_LIBRARY leveldb)
find_path(LEVELDB_INCLUDE_DIR db.h PATH_SUFFIXES leveldb)
include_directories(${LEVELDB_INCLUDE_DIR})

# Build our library
file(GLOB source "*.h" "*.cpp")
add_library( cleveldb SHARED ${source} )
target_link_libraries(cleveldb ${Boost_LIBRARIES} ${LEVELDB_LIBRARY})

set_target_properties(cleveldb PROPERTIES PREFIX "")
