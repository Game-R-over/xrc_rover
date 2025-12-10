import serial
import threading

class SerialBridge():

    get_logger = None
    data_callback = None

    serial_conn = None

    def __init__(self, logger_callback, data_callback, port = '/dev/ttyUSB0'):

        self.get_logger = logger_callback
        self.data_callback = data_callback

        try:
            self.serial_conn = serial.Serial(
                port=port,
                baudrate=115200,
                timeout=1.0
            )
            self.get_logger().info(f"Connected to {port}")
        except Exception as e:
            self.get_logger().error(f"Failed to connect to serial port: {e}")
            return

        self.read_thread = threading.Thread(target=self.read_serial)
        self.read_thread.daemon = True
        self.read_thread.start()
        
        self.get_logger().info("Serial bridge node started")
    
    def send_motor(self, speed: int, motor: int = 1):
        self.send(f'M {motor} {speed}')
        self.send(f'E {motor}')
 
    def send_servo(self, angle: float, servo: int = 1):
        self.send(f'S {servo} {angle}')

    def send(self, data):
        try:
            self.serial_conn.write(f'{data}\n'.encode())
            self.get_logger().info(f"Sent command: {data}")
        except Exception as e:
            self.get_logger().error(f"Failed to send command: {e}")
    
    def read_serial(self):
        data = ''
        while True: 
            try:
                if self.serial_conn.in_waiting > 0:
                    data_fragement = self.serial_conn.read().decode()
                    data += data_fragement
                    if data_fragement == '\n' and len(data) > 1:
                        self.get_logger().info(f'Recieved "{data}" from ESP')
                        self.data_callback(data)
                        data = ''

            except Exception as e:
                self.get_logger().error(f"Serial read error: {e}")
                break
    
    def __del__(self):
        try:
            self.serial_conn.close()
        except:
            ...
