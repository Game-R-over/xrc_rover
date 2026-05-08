#include <string>

#include "rclcpp/rclcpp.hpp"
#include "custom_msg/msg/servo_angle.hpp"
#include "custom_msg/msg/dc_speed.hpp"
#include "custom_msg/msg/mpu_data.hpp"
#include "std_msgs/msg/int32.hpp"

#include "serial_link.hxx"

/*
 * All servos
 * DC 5, 6
 * MPU
 */

class ServosSerialLink : public SerialLinkNode {
public:
	ServosSerialLink() :
		SerialLinkNode("servos_serial_link", "/dev/ttyUSB0")
	{
		this->_servo_subscription = this->create_subscription<custom_msg::msg::ServoAngle>(
			"servo_angle_update",
			10,
			[this](const custom_msg::msg::ServoAngle& msg) {
				this->_serial->swrite(
					std::string("S ") + std::to_string(msg.servo) + " " + std::to_string(msg.angle)
				);
			}
		);
		this->_dc_subscription = this->create_subscription<custom_msg::msg::DCSpeed>(
			"dc_speed_update",
			10,
			[this](const custom_msg::msg::DCSpeed& msg) {
				if(msg.dc < 5) { return; }

				this->_serial->swrite(
					std::string("M ") + std::to_string(msg.dc) + " " + std::to_string(msg.speed)
				);
			}
		);
		this->_encoder_subscription = this->create_subscription<std_msgs::msg::Int32>(
			"encoder_request",
			10,
			[this](const std_msgs::msg::Int32& msg) {
				if(msg.data < 5) { return; }
				
				this->_serial->swrite(
					std::string("E ") + std::to_string(msg.data)
				);
			}
		);
		this->_dc_publisher = this->create_publisher<custom_msg::msg::DCSpeed>(
			"dc_speed_feedback",
			10
		);
		this->_mpu_sensor_publisher = this->create_publisher<custom_msg::msg::MPUData>(
			"mpu_data_feedback",
			10
		);


		auto res = this->_serial->swrite("E 1\n");
		RCLCPP_INFO(this->get_logger(), "\"%s\"", res.has_value() ? "YES" : "NO");
		
		if(!res.has_value()) {
			RCLCPP_INFO(this->get_logger(), res.error().c_str());
		}

		RCLCPP_INFO(this->get_logger(), "START");
	}

	void on_async_read(std::string data) override {
		if(data == "") { return; }
		if(data.substr(0, 2) != "OK") {
			RCLCPP_ERROR(this->get_logger(), "[ERROR] Received: \"%s\"", data.c_str());
			return;
		}
		// TODO: Add handling for MPU
		if(data.substr(3, 3) != "RPM") {
			RCLCPP_INFO(this->get_logger(), "[DISCARD] Received: \"%s\"", data.c_str());
			return;
		}
		int dc = data.at(7) - '0';
		int speed = std::stoi(data.substr(9));

		RCLCPP_INFO(this->get_logger(), "[INFO] Received dc: %d, speed: %d\"", dc, speed);
    }

private:
	rclcpp::Subscription<custom_msg::msg::ServoAngle>::SharedPtr	_servo_subscription;
	rclcpp::Subscription<custom_msg::msg::DCSpeed>::SharedPtr		_dc_subscription;
	rclcpp::Publisher<custom_msg::msg::DCSpeed>::SharedPtr			_dc_publisher;
	rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr			_encoder_subscription;
	rclcpp::Publisher<custom_msg::msg::MPUData>::SharedPtr			_mpu_sensor_publisher;
};

int main(int argc, char * argv[]) {
	rclcpp::init(argc, argv);
	rclcpp::spin(std::make_shared<ServosSerialLink>());
	rclcpp::shutdown();
	return 0;
}
