cmake_minimum_required(VERSION 3.8)
project(serial_link)

set(CMAKE_CXX_COMPILER "/usr/bin/g++-12")
set(CMAKE_CXX_STANDARD 23)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
	add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(custom_msg REQUIRED)

add_executable(servos_serial_link
	src/servos_serial_link.cxx
	src/serial/serial.cxx
)
target_include_directories(servos_serial_link PUBLIC
	$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
	$<INSTALL_INTERFACE:include>
)
target_compile_features(servos_serial_link PUBLIC c_std_99 cxx_std_23)
ament_target_dependencies(servos_serial_link rclcpp std_msgs custom_msg)
install(TARGETS servos_serial_link
	DESTINATION lib/${PROJECT_NAME}
)

add_executable(dcs_serial_link
	src/dcs_serial_link.cxx
	src/serial/serial.cxx
)
target_include_directories(dcs_serial_link PUBLIC
	$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
	$<INSTALL_INTERFACE:include>
)
target_compile_features(dcs_serial_link PUBLIC c_std_99 cxx_std_23)
ament_target_dependencies(dcs_serial_link rclcpp std_msgs custom_msg)
install(TARGETS dcs_serial_link
	DESTINATION lib/${PROJECT_NAME}
)

add_executable(sensors_serial_link
	src/sensors_serial_link.cxx
	src/serial/serial.cxx
)
target_include_directories(sensors_serial_link PUBLIC
	$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
	$<INSTALL_INTERFACE:include>
)
target_compile_features(sensors_serial_link PUBLIC c_std_99 cxx_std_23)
ament_target_dependencies(sensors_serial_link rclcpp std_msgs custom_msg)
install(TARGETS sensors_serial_link
	DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
	find_package(ament_lint_auto REQUIRED)
	set(ament_cmake_copyright_FOUND TRUE)
	set(ament_cmake_cpplint_FOUND TRUE)
	ament_lint_auto_find_test_dependencies()
endif()

ament_package()
