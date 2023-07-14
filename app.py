from tkinter import *
from serial import Serial

from config import *
from layout import Layout


class App:

    def __init__(self):
        self.serial = Serial(
            port=SERIAL_PORT,
            baudrate=SERIAL_BAUDRATE,
            bytesize=SERIAL_BITESIZE,
            parity=SERIAL_PARITY,
            stopbits=SERIAL_STOPBITS
        )

        self.tk_root = Tk()
        self.tk_root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.layout = Layout(self.tk_root, self.serial)
        self.layout.set_defaults()

    def on_closing(self):
        self.layout.stop()
        self.tk_root.destroy()

    def run(self):
        self.tk_root.mainloop()


