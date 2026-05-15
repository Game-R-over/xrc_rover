#include "serial.hxx"

Serial::Serial(
	std::string file
) :
	m_serial_port(
		open(file.c_str(), O_RDWR | O_NOCTTY /*| O_NONBLOCK*/)
	)
{}

std::expected<
	Empty,
	std::string
> Serial::spin() {
	if(tcgetattr(m_serial_port, &m_tty) != 0) {
		return std::unexpected(
			std::string("Error ") + std::to_string(errno) + " from tcgetattr: " + strerror(errno)
		);
	}
	this->set_tty_cflags();
	this->set_tty_lflags();
	this->set_tty_iflags();
	this->set_tty_oflags();
	this->set_c_cc();
	this->set_baud_rate();
	if(tcsetattr(m_serial_port, TCSANOW, &m_tty) != 0) {
		return std::unexpected(
			std::string("Error ") + std::to_string(errno) + " from tcsetattr: " + strerror(errno)
		);
	}
	return Empty{};
}

std::expected<
	Empty,
	std::string
> Serial::swrite(std::string data) {
	data += "\n";
	if(write(m_serial_port, data.c_str(), data.size()) == -1) {
		return std::unexpected("Error trying to write to serial.");
	}
	return Empty{};
}

std::expected<
	Result,
	std::string
> Serial::sread() {
	char read_buf[64];

	int num_bytes = read(
		m_serial_port,
		read_buf,
		sizeof(read_buf)
	);

	if(num_bytes < 0) {
		return std::unexpected(
			std::string("Error reading: ") + strerror(errno)
		);
	}

	// Append only actual bytes read
	m_rx_buffer.append(read_buf, num_bytes);

	// Look for newline
	size_t pos = m_rx_buffer.find('\n');

	if(pos == std::string::npos) {
		return std::unexpected("No complete line yet");
	}

	// Extract line including/excluding newline
	std::string line = m_rx_buffer.substr(0, pos);

	// Remove processed data (+1 removes '\n')
	m_rx_buffer.erase(0, pos + 1);

	return line;
}

void Serial::sclose() {
	if (m_serial_port >= 0) {
        close(m_serial_port);
        m_serial_port = -1;
    }
}

Serial::~Serial() {
	this->sclose();
}

void Serial::set_tty_cflags() {
	m_tty.c_cflag &= ~PARENB;			// Clear parity bit, disabling parity (most common)
	m_tty.c_cflag &= ~CSTOPB;			// Clear stop field, only one stop bit used in communication (most common)
	m_tty.c_cflag &= ~CSIZE;			// Clear all bits that set the data size
	m_tty.c_cflag |= CS8;				// 8 bits per byte (most common)
	m_tty.c_cflag &= ~CRTSCTS;			// Disable RTS/CTS hardware flow control (most common)
	m_tty.c_cflag |= CREAD | CLOCAL;	// Turn on READ & ignore ctrl lines (CLOCAL = 1)
}
void Serial::set_tty_lflags() {
	//m_tty.c_lflag &= ~ICANON;
	m_tty.c_lflag |= ICANON;
	m_tty.c_lflag &= ~ECHO;		// Disable echo
	m_tty.c_lflag &= ~ECHOE;	// Disable erasure
	m_tty.c_lflag &= ~ECHONL;	// Disable new-line echo
	m_tty.c_lflag &= ~ISIG;		// Disable interpretation of INTR, QUIT and SUSP
}
void Serial::set_tty_iflags() {
	m_tty.c_iflag &= ~(IXON | IXOFF | IXANY);							// Turn off s/w flow ctrl
	m_tty.c_iflag &= ~(IGNBRK|BRKINT|PARMRK|ISTRIP|INLCR|IGNCR|ICRNL);	// Disable any special handling of received bytes
}
void Serial::set_tty_oflags() {
	m_tty.c_oflag &= ~OPOST;	// Prevent special interpretation of output bytes (e.g. newline chars)
	m_tty.c_oflag &= ~ONLCR;	// Prevent conversion of newline to carriage return/line feed
}
void Serial::set_c_cc() {
	m_tty.c_cc[VTIME] = 1;	// Wait for up to .1s, returning as soon as any data is received.
	m_tty.c_cc[VMIN] = 0;
}
void Serial::set_baud_rate() {
	cfsetispeed(&m_tty, BAUD_RATE);
	cfsetospeed(&m_tty, BAUD_RATE);
}
