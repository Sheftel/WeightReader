from tkinter import *

from config import *
from layout import Layout


class App:
    def __init__(self):
        self.tk_root = Tk()
        self.tk_root.title(APP_TITLE)
#        self.tk_root.iconbitmap(STATIC_PATH / "icon.ico")
        self.tk_root.resizable(FALSE, FALSE)

        self.tk_root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.layout = Layout(self.tk_root)

    def on_closing(self):
        self.layout.stop()
        self.tk_root.destroy()

    def run(self):
        self.tk_root.mainloop()
