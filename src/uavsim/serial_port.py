import select
from collections.abc import Buffer

import serial


class SerialPort:
    """"
    Implements a PySerial port.
    """

    def __init__(self, port, baud=115200):
        self.serial_port = serial.Serial(port=port,
                                         baudrate=baud,
                                         timeout=0.1,
                                         bytesize=serial.EIGHTBITS,
                                         parity=serial.PARITY_NONE,
                                         stopbits=serial.STOPBITS_ONE,
                                         xonxoff=False,
                                         rtscts=False,
                                         dsrdtr=False)

    def is_byte_available(self) -> bool:
        readable, _, _ = select.select([self.serial_port.fileno()], [], [], 0)

        return bool(readable)

    def read_byte(self) -> int | None:
        """"
        Reads a byte from the serial port.
        """
        if self.is_byte_available():
            data = self.serial_port.read()
            if data:
                return data[0]

        return None

    def write(self, data: Buffer) -> None:
        """"
        Write data to a serial port.
        """
        self.serial_port.write(data)
