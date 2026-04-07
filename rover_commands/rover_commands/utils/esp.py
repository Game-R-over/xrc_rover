import serial
import threading

class SerialBridge():

    '''
    Servos Layout

        1       : Arm claw
        2, 3    : Arm in R^2
        4       : Arm in θ
        5 - 8   : Wheels (FR, FL, BR, BL)
    '''
    '''
    DSs Layout

        1, 2    : Middle (separate)
        3, 4    : Front
        5, 6    : Back
    '''

    WHEEL_SERVO_OFFSET = 4
    ARM_SERVO_OFFSET = 1

    get_logger = None
    data_callbacks = {
        'motor': ('RPM', None),
    }

    serial_conn = None

    def __init__(self, logger_callback, data_callbacks, port = '/dev/ttyUSB0'):

        self.get_logger = logger_callback
        self.data_callbacks = data_callbacks

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
    
    def send_move_motor(self, speed: int, motor: int = 1):
        self.send(f'M {motor} {speed}')
        self.send(f'E {motor}')
     
    def send_move_servo(self, angle: float, servo: int = 1):
        self.send(f'S {servo + self.MOVE_SERVO_OFFSET} {angle}')

    def send_arm_servo(self, angle: float, servo: int = 1):
        self.send(f'S {servo + self.ARM_SERVO_OFFSET} {angle}')

    def send_claw_servo(self, angle: float):
        self.send(f'S 1 {angle}')

    def send(self, data):
        try:
            self.serial_conn.write(f'{data}\n'.encode())
            self.get_logger().info(f"Sent command: {data}")
        except Exception as e:
            self.get_logger().error(f"Failed to send command: {e}")
    
    def send_data_to_right_callback(self, data: str):
        datas = data.split(' ')
        if datas[0] == 'ERR':
            self.get_logger().error(' '.join(datas[1:]))
        for (prefix, callback) in self.data_callbacks.values():
            if prefix == datas[1]:
                callback(datas[2:])
                break

        self.get_logger().error('Unknown prefix ' + datas[1])


    def read_serial(self):
        data = ''
        while True: 
            try:
                if self.serial_conn.in_waiting > 0:
                    data_fragement = self.serial_conn.read().decode()
                    data += data_fragement
                    if data_fragement == '\n' and len(data) > 1:
                        self.get_logger().info(f'Recieved "{data}" from ESP')
                        self.send_data_to_right_callback(data)
                        data = ''

            except Exception as e:
                self.get_logger().error(f"Serial read error: {e}")
                break
    
    def __del__(self):
        try:
            self.serial_conn.close()
        except:
            ...
