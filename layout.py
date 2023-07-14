from datetime import date
from threading import Thread
from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd

from config import APP_TITLE, DEFAULT_FILE_PATH
from reader import read_data

# TODO: 1. Disable start button until both file and period are filled
# TODO: 2. Disable stop button unless start was activated
# TODO: 3. Fix grid
# TODO: 4. Make it so entry.xview('end') works


class Layout:
    def __init__(self, root, serial_port):
        self.serial_port = serial_port
        self.thread = None
        root.title(APP_TITLE)
        root.iconbitmap("static/icon.ico")
        root.resizable(FALSE, FALSE)

        mainframe = ttk.Frame(root, padding="5 5 12 12")


        # TODO: make file widget
        self.filename = StringVar()
        self.filename.trace_add("write", self.filename_write_callback)
        filename_label = ttk.Label(mainframe, text='Название файла: ')
        self.filename_entry = ttk.Entry(mainframe, textvariable=self.filename, width=40)
        self.filename_button = ttk.Button(mainframe, text='Выбрать файл', command=self.select_file, width=5)


        # TODO: add validation
        self.period = IntVar(value=30)
        # period = StringVar(value='30')
        period_label = ttk.Label(mainframe, text='Период записи(сек.):')
        # TODO: change limits to .env variables
        # TODO: add validator for cases when value is bigger than to
        self.period_spinbox = ttk.Spinbox(mainframe, textvariable=self.period, from_=1, to=7200, increment=1, width=50)
       #  self.period_spinbox.set("2")
        # period_entry = ttk.Entry(mainframe, textvariable=period)


        # TODO: add start button
        self.start_button = ttk.Button(mainframe, text='Старт', command=self.start, width=35)
        # TODO: add stop button
        self.stop_button = ttk.Button(mainframe, text='Стоп', command=self.stop, width=35)

        # grid setup
        # mainframe.grid_propagate(FALSE)
        mainframe.grid(column=0, row=0)
        filename_label.grid(column=0, row=0)
        self.filename_entry.grid(column=0, columnspan=2, row=1)
        self.filename_button.grid(column=2, row=1)
        period_label.grid(column=0, row=2)
        self.period_spinbox.grid(column=0, row=3)
        self.start_button.grid(column=0, row=4, columnspan=2)
        self.stop_button.grid(column=0, row=5, columnspan=2)

    def set_defaults(self):
        self.filename.set(DEFAULT_FILE_PATH / f'{date.today()}.txt')
        self.period.set(30)

    def start(self):
        self.thread = Thread(target=read_data, args=(self.serial_port, self.filename.get(), self.period.get()))
        self.thread.start()

    def stop(self):
        if self.thread:
            self.thread.stop_thread = True

    def select_file(self):
        self.filename.set(fd.askopenfilename(filetypes=[('Text files', '.txt')]))
        self.filename_entry.xview('end')

    def filename_write_callback(self, *args):
        # self.filename_entry.
        self.filename_entry.xview('end')



