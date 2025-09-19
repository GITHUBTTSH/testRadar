import serial
import serial.tools.list_ports
import threading
import time

DATA_BITS_MAP = {"5": serial.FIVEBITS, "6": serial.SIXBITS, "7": serial.SEVENBITS, "8": serial.EIGHTBITS}
STOP_BITS_MAP = {"1": serial.STOPBITS_ONE, "1.5": serial.STOPBITS_ONE_POINT_FIVE, "2": serial.STOPBITS_TWO}
PARITY_MAP = {"None": serial.PARITY_NONE, "Odd": serial.PARITY_ODD, "Even": serial.PARITY_EVEN}

class serialManager:
    def __init__(self, buffer_size=4096):
        self.control_serial = serial.Serial()
        self.data_serial = serial.Serial()
        self.is_connected = False

        self._receive_thread = None
        self._stop_event = threading.Event()

        self.control_callback = None
        self.data_callback = None

        # 固定大小缓存区
        self._control_buffer = bytearray(buffer_size)
        self._control_index = 0
        self._data_buffer = bytearray(buffer_size)
        self._data_index = 0
        self._buffer_size = buffer_size

    def connect(self, control_port, control_baud, data_port, data_baud,
                data_bits="8", stop_bits="1", parity="None"):
        if self.is_connected:
            return False
        try:
            if control_port:
                self.control_serial.port = control_port
                self.control_serial.baudrate = control_baud
                self.control_serial.bytesize = DATA_BITS_MAP[data_bits]
                self.control_serial.stopbits = STOP_BITS_MAP[stop_bits]
                self.control_serial.parity = PARITY_MAP[parity]
                # self.control_serial.rtscts = False,  # 关闭 RTS/CTS
                # self.control_serial.dsrdtr = False  # 关闭 DSR/DTR
                self.control_serial.open()
            if data_port:
                self.data_serial.port = data_port
                self.data_serial.baudrate = data_baud
                self.data_serial.bytesize = DATA_BITS_MAP[data_bits]
                self.data_serial.stopbits = STOP_BITS_MAP[stop_bits]
                self.data_serial.parity = PARITY_MAP[parity]
                # self.data_serial.rtscts = False,  # 关闭 RTS/CTS
                # self.data_serial.dsrdtr = False  # 关闭 DSR/DTR
                self.data_serial.open()

            self.is_connected = True
            self._stop_event.clear()
            self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._receive_thread.start()
            return True
        except serial.SerialException as e:
            print("串口连接失败:", e)
            return False

    def disconnect(self):
        self._stop_event.set()
        if self._receive_thread:
            self._receive_thread.join(timeout=1)
        if self.control_serial.is_open:
            self.control_serial.close()
        if self.data_serial.is_open:
            self.data_serial.close()
        self.is_connected = False

    @staticmethod
    def list_ports():
        return [(p.device, p.description) for p in serial.tools.list_ports.comports()]

    def send_control(self, data: bytes):
        if self.control_serial.is_open:
            self.control_serial.write(data)

    def send_data(self, data: bytes):
        if self.data_serial.is_open:
            self.data_serial.write(data)

    def _receive_loop(self):
        while not self._stop_event.is_set():
            try:
                # 控制口
                if self.control_serial.is_open and self.control_serial.in_waiting:
                    # 逐字节读取
                    byte_data = self.control_serial.read(1)
                    if byte_data and self.control_callback:
                        self.control_callback(byte_data)

                # 数据口
                if self.data_serial.is_open and self.data_serial.in_waiting:
                    # 逐字节读取
                    byte_data = self.data_serial.read(1)
                    if byte_data and self.data_callback:
                        self.data_callback(byte_data)

            except Exception as e:
                print("接收线程异常:", e)
            time.sleep(0.00001) #避免空转报错


if __name__ == "__main__":
    def control_data_received(data):
        print(f"控制口接收到: {data.hex()}") # 打印十六进制

    def data_data_received(data):
        print(f"数据口接收到: {data.decode('utf-8', errors='ignore')}") # 尝试解码为UTF-8

    manager = serialManager()
    manager.control_callback = control_data_received
    manager.data_callback = data_data_received

    # 打印可用串口
    print("可用串口:")
    for port, desc in manager.list_ports():
        print(f"  {port}: {desc}")

    # 请根据你的实际串口名称和波特率修改这里
    control_port = "COM4"  # 替换为你的控制串口
    data_port = "COM5"     # 替换为你的数据串口
    baud_rate = 115200

    if manager.connect(control_port, baud_rate, data_port, baud_rate):
        print(f"成功连接到 {control_port} 和 {data_port}")

        try:
            while True:
                # 示例：每秒发送一个字节
                # manager.send_control(b'\x01')
                # manager.send_data(b'A')
                time.sleep(1)
        except KeyboardInterrupt:
            print("用户中断，正在断开连接...")
        finally:
            manager.disconnect()
            print("连接已断开。")
    else:
        print("连接失败，请检查串口设置。")


