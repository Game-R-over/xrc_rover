#include <string>

#include "rclcpp/rclcpp.hpp"
#include "custom_msg/msg/ultrasonic_distance.hpp"

#include "serial_link.hxx"

/*
 * Ultrasonic Sensors 1-8
 * MPU
 */

class SensorsSerialLink : public SerialLinkNode {
public:
	SensorsSerialLink() :
		SerialLinkNode("sensors_serial_link", "/dev/ttyUSB2")
	{
		this->_ultrasonic_sensors_publisher = this->create_subscription<custom_msg::msg::UltrasonicDistance>(
			"ultrasonic_distance_feedback",
			10
		);
		
		RCLCPP_INFO(this->get_logger(), "START");
	}

	void on_async_read(std::string data) override {
		if(data.substr(0, 2) != "OK") {
			RCLCPP_ERROR(this->get_logger(), "[ERROR] Received: \"%s\"", data.c_str());
			return;
		}
		// TODO: Add something
    }

private:
	rclcpp::Publisher<custom_msg::msg::UltrasonicDistance>::SharedPtr	_ultrasonic_sensors_publisher;
	rclcpp::Publisher<custom_msg::msg::MPUData>::SharedPtr				_mpu_sensor_publisher;
};

int main(int argc, char * argv[]) {
	rclcpp::init(argc, argv);
	rclcpp::spin(std::make_shared<ServosSerialLink>());
	rclcpp::shutdown();
	return 0;
}
