cmake_minimum_required(VERSION 3.26)
project(pyWilsonSimulation)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

include(ExternalProject)

set(DEPENDENCIES_PREFIX_PATH "${CMAKE_CURRENT_LIST_DIR}/dependencies")

if (MSVC)
    if (NOT EXISTS "${DEPENDENCIES_PREFIX_PATH}/swigwin-4.1.1/swig.exe")
        execute_process(COMMAND unzip.exe ${CMAKE_CURRENT_LIST_DIR}/swigwin-4.1.1.zip WORKING_DIRECTORY ${DEPENDENCIES_PREFIX_PATH})
    endif()
    set(SWIG_DIR "${DEPENDENCIES_PREFIX_PATH}/swigwin-4.1.1/Lib")
    set(SWIG_EXECUTABLE "${DEPENDENCIES_PREFIX_PATH}/swigwin-4.1.1/swig.exe")

# TODO: it should be build anyway so it is not applicable
#    if (NOT EXISTS "${DEPENDENCIES_PREFIX_PATH}/boost_1_82_0.zip")
#        set(BOOST_URL https://boostorg.jfrog.io/artifactory/main/release/1.82.0/source/boost_1_82_0.zip)
#        file(DOWNLOAD ${BOOST_URL} ${DEPENDENCIES_PREFIX_PATH}/boost_1_82_0.zip SHOW_PROGRESS)
#        execute_process(COMMAND unzip.exe ${DEPENDENCIES_PREFIX_PATH}/boost_1_82_0.zip WORKING_DIRECTORY ${DEPENDENCIES_PREFIX_PATH})
#    endif()

    if (NOT EXISTS "${DEPENDENCIES_PREFIX_PATH}/boost")
        message(STATUS "NOT EXISTS DIRECTORY")
        set(BOOST_URL "https://boostorg.jfrog.io/artifactory/main/release/1.82.0/source/boost_1_82_0.zip")

        ExternalProject_Add(external_boost
                PREFIX ${DEPENDENCIES_PREFIX_PATH}/boost-tmp
                URL ${BOOST_URL}
                BUILD_IN_SOURCE 1
                CONFIGURE_COMMAND ./bootstrap.bat --with-libraries=system link=shared variant=release threading=multi runtime-link=static --prefix=<INSTALL_DIR>
                BUILD_COMMAND ./b2.exe --prefix=<INSTALL_DIR> address-model=64 --with-system --with-exception link=static variant=release threading=multi runtime-link=static install
                INSTALL_COMMAND ""
                INSTALL_DIR ${DEPENDENCIES_PREFIX_PATH}/boost)
        list(APPEND DEPENDENCIES_LIST external_boost)
        return() # main dependency nothing should be done before ths will be resolved
    else()
        if ("${BOOST_ROOT}" STREQUAL "")
            set(BOOST_ROOT ${DEPENDENCIES_PREFIX_PATH}/boost)
        endif()
        message(STATUS "BOOST_ROOT=${BOOST_ROOT}")
        find_package(Boost REQUIRED)
    endif()

    message(STATUS "Boost_INCLUDE_DIR=${Boost_INCLUDE_DIR}")
    message(STATUS "Boost_LIBRARIES=${Boost_LIBRARIES}")
    message(STATUS "Boost_LIBS=${Boost_LIBS}")
else()
    find_package(Boost REQUIRED)
endif()

if (NOT EXISTS "${DEPENDENCIES_PREFIX_PATH}/bayesopt/lib/${CMAKE_STATIC_LIBRARY_PREFIX}bayesopt${CMAKE_STATIC_LIBRARY_SUFFIX}")
    ExternalProject_Add(bayesopt_external
            PREFIX ${DEPENDENCIES_PREFIX_PATH}/bayesopt-tmp
            GIT_REPOSITORY "https://github.com/rmcantin/bayesopt.git"
            CMAKE_ARGS
            -DCMAKE_INSTALL_PREFIX=${DEPENDENCIES_PREFIX_PATH}/bayesopt
            -DCMAKE_BUILD_TYPE=Release
            -DHAVE_GETTIMEOFDAY=OFF
            -DBAYESOPT_BUILD_EXAMPLES=OFF
            -DBoost_INCLUDE_DIR=${Boost_INCLUDE_DIR}
            -DCMAKE_CXX_FLAGS="-std=c++11")
    set(BAYESOPT_ROOT ${DEPENDENCIES_PREFIX_PATH}/bayesopt)
    list(APPEND DEPENDENCIES_LIST bayesopt_external)
endif()

message(STATUS DEPENDENCIES_LIST="${DEPENDENCIES_LIST}")
add_custom_target(dependencies DEPENDS ${DEPENDENCIES_LIST})

if (NOT EXISTS "${DEPENDENCIES_PREFIX_PATH}/bayesopt/lib/${CMAKE_STATIC_LIBRARY_PREFIX}bayesopt${CMAKE_STATIC_LIBRARY_SUFFIX}")
  return()
endif()

add_subdirectory(src)

set(CMAKE_SWIG_FLAGS)
find_package(SWIG REQUIRED)
include(${SWIG_USE_FILE})

if(${SWIG_VERSION} VERSION_GREATER_EQUAL 4)
    list(APPEND CMAKE_SWIG_FLAGS "-doxygen")
endif()

if(UNIX AND NOT APPLE)
    list(APPEND CMAKE_SWIG_FLAGS "-DSWIGWORDSIZE64")
endif()

find_package(Python 3.9 REQUIRED COMPONENTS Interpreter Development) #NumPy)
if(Python_VERSION VERSION_GREATER_EQUAL 3)
    list(APPEND CMAKE_SWIG_FLAGS "-py3;-DPY3")
endif()

#set(PYTHON_PROJECT cmakeswig)

set_property(SOURCE src/interface/WilsonSimulation.i PROPERTY CPLUSPLUS ON)
set_property(SOURCE src/interface/WilsonSimulation.i PROPERTY SWIG_MODULE_NAME ${PROJECT_NAME})
swig_add_library(${PROJECT_NAME}
        TYPE SHARED
        LANGUAGE python
        SOURCES src/interface/WilsonSimulation.i
        OUTPUT_DIR ${CMAKE_CURRENT_LIST_DIR}/python/pyWilsonSimulation)

swig_link_libraries(${PROJECT_NAME}
        WilsonSimulation
        ${Python_LIBRARIES})

set_property(TARGET ${PROJECT_NAME} PROPERTY SWIG_USE_TARGET_INCLUDE_DIRECTORIES ON)
set_target_properties(${PROJECT_NAME} PROPERTIES SUFFIX .so)
set_target_properties(${PROJECT_NAME} PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_LIST_DIR}/python/${PROJECT_NAME})

# note: macOS is APPLE and also UNIX !
#if(APPLE)
#    set_target_properties(${PROJECT_NAME} PROPERTIES
#            SUFFIX ".so"
#            INSTALL_RPATH "@loader_path;@loader_path/../../${PYTHON_PROJECT}/.libs")
#    set_property(TARGET ${PROJECT_NAME} APPEND PROPERTY
#            LINK_FLAGS "-flat_namespace -undefined suppress")
#elseif(UNIX)
#    set_target_properties(${PROJECT_NAME} PROPERTIES
#            INSTALL_RPATH "$ORIGIN:$ORIGIN/../../${PYTHON_PROJECT}/.libs")
#endif()

target_include_directories(${PROJECT_NAME} PRIVATE
        ${Python_INCLUDE_DIRS}
        ${Python_NumPy_INCLUDE_DIRS}
        WilsonSimulation/include)

# Files to install with Python
#set(PYTHON_INSTALL_FILES
#        ${CMAKE_CURRENT_BINARY_DIR}/pyWilsonSimulation.py
#        ${CMAKE_CURRENT_BINARY_DIR}/_pyWilsonSimulation.so)

# Configure setup.py and copy to output directory
configure_file(src/setup.py.in ${CMAKE_CURRENT_BINARY_DIR}/setup.py)

add_custom_target(${PROJECT_NAME}_copy ALL
        COMMAND rm -rf ${CMAKE_CURRENT_LIST_DIR}/python/${PROJECT_NAME}/*.h ${CMAKE_CURRENT_LIST_DIR}/python/${PROJECT_NAME}/*.cxx
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        COMMENT "Copying pyWilsonSimulation"
        DEPENDS ${PROJECT_NAME})

add_dependencies(${PROJECT_NAME}_copy ${PROJECT_NAME})

message(STATUS "Python_EXECUTABLE=${Python_EXECUTABLE}")

# Build target to call setup.py
add_custom_target(install_python
        DEPENDS ${PROJECT_NAME}_copy
        COMMAND ${Python_EXECUTABLE} ${CMAKE_CURRENT_BINARY_DIR}/setup.py bdist_wheel)

add_subdirectory(tests)