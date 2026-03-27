#include <memory>
#include <thread>
#include <string>

#include "rclcpp/rclcpp.hpp"

#include "serial/serial.hxx"

class SerialLinkNode : public rclcpp::Node {
public:
	SerialLinkNode(std::string name, std::string file) :
		Node(name),
		_serial(std::make_shared<Serial>(file)),
		_running(true)
	{
		auto result = this->_serial->spin();
		if(!result) {
			RCLCPP_ERROR(this->get_logger(), result.error().c_str());
			throw "No";
		}
        this->_serial_read_thread = std::thread([this]() { this->async_read(); });
	}

	~SerialLinkNode() {
        this->_running = false;
        if(_serial_read_thread.joinable()) {
            _serial_read_thread.join();
        }
    }

	void async_read() {
        while(rclcpp::ok() && this->_running) {
            auto result = this->_serial->sread();
            if(result.has_value()) {
				this->on_async_read(result.value());
            }
        }
    }

	virtual void on_async_read(std::string data) {
		(void)data;
		RCLCPP_ERROR(this->get_logger(), "Trying to use bare SerialLinkNode");
	}

protected:
	std::shared_ptr<Serial> _serial;
	std::thread _serial_read_thread;
	std::atomic<bool> _running;
};
