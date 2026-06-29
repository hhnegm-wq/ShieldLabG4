cmake_minimum_required(VERSION 3.16)
project(ShieldLabG4)

option(WITH_GEANT4_UIVIS "Build with Geant4 UI and visualization drivers" ON)
if(WITH_GEANT4_UIVIS)
  find_package(Geant4 REQUIRED ui_all vis_all)
else()
  find_package(Geant4 REQUIRED)
endif()

include(${Geant4_USE_FILE})

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(${PROJECT_SOURCE_DIR}/include ${Geant4_INCLUDE_DIR})
file(GLOB sources ${PROJECT_SOURCE_DIR}/src/*.cc)
file(GLOB headers ${PROJECT_SOURCE_DIR}/include/*.hh)

add_executable(ShieldLabG4 app/ShieldLabG4.cc ${sources} ${headers})
target_link_libraries(ShieldLabG4 ${Geant4_LIBRARIES})

set(ShieldLabG4_SCRIPTS
  macros/examples/gamma_lead_slab.mac
)

foreach(_script ${ShieldLabG4_SCRIPTS})
  configure_file(${PROJECT_SOURCE_DIR}/${_script} ${PROJECT_BINARY_DIR}/${_script} COPYONLY)
endforeach()

install(TARGETS ShieldLabG4 DESTINATION bin)