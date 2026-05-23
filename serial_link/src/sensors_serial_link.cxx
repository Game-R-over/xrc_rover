#include <string>

#include "rclcpp/rclcpp.hpp"
#include "custom_msg/msg/ultrasonic_distance.hpp"

#include "serial_link.hxx"

/*
 * Ultrasonic Sensors 1-8
 */

class SensorsSerialLink : public SerialLinkNode {
public:
	SensorsSerialLink() :
		SerialLinkNode("sensors_serial_link", "/dev/ttyUSB2")
	{
		this->_ultrasonic_sensors_publisher = this->create_publisher<custom_msg::msg::UltrasonicDistance>(
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
		if(data.substr(3, 2) == "US") { 
        auto msg = custom_msg::msg::UltrasonicDistance();
        std::istringstream iss(data.substr(6));
        iss >> msg.sensor >> msg.distance;
        this->_ultrasonic_sensors_publisher->publish(msg);
        RCLCPP_INFO(this->get_logger(), "[US] sensor:%d distance:%.2f", msg.sensor, msg.distance);
        return;
    	}
    	RCLCPP_INFO(this->get_logger(), "[DISCARD] Received: \"%s\"", data.c_str());
	}

private:
	rclcpp::Publisher<custom_msg::msg::UltrasonicDistance>::SharedPtr	_ultrasonic_sensors_publisher;
};

int main(int argc, char * argv[]) {
	rclcpp::init(argc, argv);
	rclcpp::spin(std::make_shared<SensorsSerialLink>());
	rclcpp::shutdown();
	return 0;
}
