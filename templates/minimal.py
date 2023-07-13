from tkinter import *
from tkinter import ttk

from config import APP_TITLE


class MinimalLayout:

    def __init__(self, root):
        root.title(APP_TITLE)
        mainframe = ttk.Frame(root, width=310, height=360, padding="3 3 12 12")
        mainframe.grid(column=0, row=0)


    def duh(self):
        ...