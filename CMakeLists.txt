# SPDX-License-Identifier: BSD-2-Clause

# Copyright (c) 2021 NKI/AVL, Netherlands Cancer Institute

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

cmake_minimum_required(VERSION 3.25)

# set the project name
project(tortoize VERSION 2.0.16 LANGUAGES CXX)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

include(FindOrFetch)
include(GNUInstallDirs)
include(CheckFunctionExists)
include(CheckIncludeFiles)
include(CheckLibraryExists)
include(CMakePackageConfigHelpers)
include(GenerateExportHeader)
include(CTest)

set(CXX_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)  # needed to build dynamic libraries for python

# For pixi/pip builds, make sure the pixi path comes first.
if(DEFINED ENV{PREFIX})
	list(PREPEND CMAKE_PREFIX_PATH "$ENV{PREFIX}")
endif()

if("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wno-unused-parameter -Wno-missing-field-initializers")
elseif(MSVC)
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /W4")
endif()

if(MSVC)
	# make msvc standards compliant...
	add_compile_options(/permissive-)
	add_link_options(/NODEFAULTLIB:library)

	macro(get_WIN32_WINNT version)
		if(WIN32 AND CMAKE_SYSTEM_VERSION)
			set(ver ${CMAKE_SYSTEM_VERSION})
			string(REPLACE "." "" ver ${ver})
			string(REGEX REPLACE "([0-9])" "0\\1" ver ${ver})

			set(${version} "0x${ver}")
		endif()
	endmacro()

	get_WIN32_WINNT(ver)
	add_definitions(-D_WIN32_WINNT=${ver})
endif()

# Create a revision file, containing the current git version info, if any
include(VersionString)
write_version_header(${PROJECT_SOURCE_DIR}/src/cpp)

# Optionally build a webservice
option(BUILD_WEBSERVICE "Build a version with a webservice daemon" OFF)

# libraries
set(CMAKE_THREAD_PREFER_PTHREAD)
set(THREADS_PREFER_PTHREAD_FLAG)
find_package(Threads)

find_package(nlohmann_json REQUIRED)

find_or_fetch_package(cifpp VERSION 9 GIT_REPOSITORY https://github.com/PDB-REDO/libcifpp.git GIT_TAG v9.0.5 VARIABLES "CIFPP_SHARE_DIR")

# Pybind11 and passing JSON into Python
set(PYBIND11_FINDPYTHON ON)
find_package(pybind11 CONFIG REQUIRED)
add_subdirectory(extern/pybind11_json)
include_directories(extern/pybind11_json/include)

set(Python3_FIND_STRATEGY LOCATION)
find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)

pybind11_add_module(py_tortoize ${PROJECT_SOURCE_DIR}/src/py_tortoize/python-bindings.cpp
		${PROJECT_SOURCE_DIR}/src/cpp/tortoize.cpp
		${PROJECT_SOURCE_DIR}/src/cpp/tortoize.hpp
)
include(GNUInstallDirs)
install(TARGETS py_tortoize
		LIBRARY DESTINATION .
)
if (NOT TARGET dssp)
	add_subdirectory(dssp EXCLUDE_FROM_ALL)
endif()

target_link_libraries(py_tortoize PRIVATE nlohmann_json dssp::dssp cifpp::cifpp Python3::Module)

install(FILES
		${PROJECT_SOURCE_DIR}/rsrc/rama-data.bin
		${PROJECT_SOURCE_DIR}/rsrc/torsion-data.bin
		${PROJECT_SOURCE_DIR}/rsrc/components.cif
		DESTINATION ${CIFPP_SHARE_DIR}
)

# manual
install(FILES doc/tortoize.1 DESTINATION ${CMAKE_INSTALL_MANDIR}/man1)

# Test code
if(BUILD_TESTING)
	add_subdirectory(test)
endif()
