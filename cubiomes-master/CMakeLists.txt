cmake_minimum_required(VERSION 3.1)
project(cubiomes C)

if (NOT CMAKE_BUILD_TYPE)
	set(CMAKE_BUILD_TYPE Release)
endif()
if (WIN32)
	add_definitions(-D_WIN32)
endif()

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra")
set(CMAKE_C_FLAGS_DEBUG "-O0 -g3 -DDEBUG")

find_package(Threads REQUIRED)

set(HEADERS
	finders.h
	generator.h
	layers.h
	biomenoise.h
	biomes.h
	noise.h
	rng.h
	util.h
	quadbase.h
)
set(SOURCES
	finders.c
	generator.c
	layers.c
	biomenoise.c
	biomes.c
	noise.c
	util.c
	quadbase.c
)

add_library(objects OBJECT ${SOURCES})
set_property(TARGET objects PROPERTY POSITION_INDEPENDENT_CODE 1)

add_library(cubiomes SHARED $<TARGET_OBJECTS:objects>)
add_library(cubiomes_static STATIC $<TARGET_OBJECTS:objects>)
add_executable(cubiomes_tests tests.c)

if (NOT WIN32)
	target_link_libraries(cubiomes PRIVATE m Threads::Threads)
	target_link_libraries(cubiomes_static PUBLIC m Threads::Threads)
	target_link_libraries(cubiomes_tests PRIVATE cubiomes_static m Threads::Threads)
else()
	target_link_libraries(cubiomes_tests PRIVATE cubiomes_static)
endif()

install(TARGETS cubiomes cubiomes_static DESTINATION lib)
install(FILES ${HEADERS} DESTINATION include)


