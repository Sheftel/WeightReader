import sys

from tkinter import *
from serial import Serial, SerialException

from config import *
from layout import Layout
from utils import raise_error


class App:
    def __init__(self):
        self.tk_root = Tk()
        self.tk_root.title(APP_TITLE)
        self.tk_root.iconbitmap(STATIC_PATH / "icon.ico")
        self.tk_root.resizable(FALSE, FALSE)
        try:
            self.serial = Serial(
                port=SERIAL_PORT,
                baudrate=SERIAL_BAUDRATE,
                bytesize=SERIAL_BITESIZE,
                parity=SERIAL_PARITY,
                stopbits=SERIAL_STOPBITS,
                timeout=SERIAL_TIMEOUT
            )
        except SerialException:
            raise_error(message='Невозможно подключиться к порту по указанным данным.')
            sys.exit(1)

        self.tk_root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.layout = Layout(self.tk_root, self.serial)
        self.layout.set_defaults()

    def on_closing(self):
        self.layout.stop()
        self.tk_root.destroy()

    def run(self):
        self.tk_root.mainloop()
