#include <cstring>
#include <errno.h>
#include <expected>
#include <fcntl.h>
#include <termios.h>
#include <string>
#include <unistd.h>

typedef struct {} Empty;
typedef std::string Result;

class Serial {
public:
	Serial(std::string file);

	std::expected<
		Empty,
		std::string
	> spin();

	std::expected<
		Empty,
		std::string
	> swrite(std::string data);

	std::expected<
		Result,
		std::string
	> sread();

	void sclose();

	~Serial();

private:
	void set_tty_cflags();
	void set_tty_lflags();
	void set_tty_iflags();
	void set_tty_oflags();
	void set_c_cc();
	void set_baud_rate();

private:
	int m_serial_port;
	struct termios m_tty;
	const speed_t BAUD_RATE = B115200;
};
