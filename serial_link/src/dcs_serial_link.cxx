#include <string>

#include "rclcpp/rclcpp.hpp"
#include "custom_msg/msg/dc_speed.hpp"
#include "std_msgs/msg/int32.hpp"

#include "serial_link.hxx"

/*
 * DC 1-4
 */

class DCSSerialLink : public SerialLinkNode {
public:
	DCSSerialLink() :
		SerialLinkNode("dcs_serial_link", "/dev/ttyUSB1")
	{
		this->_dc_subscription = this->create_subscription<custom_msg::msg::DCSpeed>(
			"dc_speed_update",
			10,
			[this](const custom_msg::msg::DCSpeed& msg) {
				if(msg.dc > 4) { return; }
				
				this->_serial->swrite(
					std::string("M ") + std::to_string(msg.dc) + " " + std::to_string(msg.speed)
				);
			}
		);
		this->_encoder_subscription = this->create_subscription<std_msgs::msg::Int32>(
			"encoder_request",
			10,
			[this](const std_msgs::msg::Int32& msg) {
				if(msg.data > 4) { return; }
				
				this->_serial->swrite(
					std::string("E ") + std::to_string(msg.data)
				);
			}
		);
		this->_dc_publisher = this->create_publisher<custom_msg::msg::DCSpeed>(
			"dc_speed_feedback",
			10
		);

		RCLCPP_INFO(this->get_logger(), "START");
	}

	void on_async_read(std::string data) override {
		if(data.substr(0, 2) != "OK") {
			RCLCPP_ERROR(this->get_logger(), "[ERROR] Received: \"%s\"", data.c_str());
			return;
		}
		if(data.substr(3, 3) != "RPM") {
			RCLCPP_INFO(this->get_logger(), "[DISCARD] Received: \"%s\"", data.c_str());
			return;
		}
		int dc = data.at(7) - '0';
		int speed = std::stoi(data.substr(9));

		RCLCPP_INFO(this->get_logger(), "[INFO] Received dc: %d, speed: %d\"", dc, speed);
    }

private:
	rclcpp::Subscription<custom_msg::msg::DCSpeed>::SharedPtr		_dc_subscription;
	rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr			_encoder_subscription;
	rclcpp::Publisher<custom_msg::msg::DCSpeed>::SharedPtr			_dc_publisher;
};

int main(int argc, char * argv[]) {
	rclcpp::init(argc, argv);
	rclcpp::spin(std::make_shared<DCSSerialLink>());
	rclcpp::shutdown();
	return 0;
}
