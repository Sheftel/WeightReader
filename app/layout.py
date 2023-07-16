from datetime import date
from threading import Thread
from tkinter import *
from tkinter import ttk, filedialog as fd

from config import STATIC_PATH, DEFAULT_FILE_PATH, DEFAULT_PERIOD, MIN_PERIOD, MAX_PERIOD
from reader import read_data


class Layout:
    def __init__(self, root, serial_port):
        self.serial_port = serial_port
        self.thread = None

        mainframe = ttk.Frame(root, padding="5 5 5 5")

        self.filename = StringVar()
        self.filename.trace_add("write", self.filename_write_callback)
        filename_label = ttk.Label(mainframe, text='Название файла: ')
        self.filename_entry = ttk.Entry(mainframe, textvariable=self.filename, width=42)
        self.filename_button_image = PhotoImage(file=STATIC_PATH / "file.png")
        self.filename_button = ttk.Button(mainframe, image=self.filename_button_image, command=self.select_file)

        self.period = IntVar()
        self.period.trace_add("write", self.period_write_callback)
        period_label = ttk.Label(mainframe, text='Период записи(сек.):')
        self.period_spinbox = ttk.Spinbox(mainframe,
                                          textvariable=self.period,
                                          from_=MIN_PERIOD,
                                          to=MAX_PERIOD,
                                          increment=1)

        self.start_button = ttk.Button(mainframe, text='Старт', command=self.start, width=20, state=DISABLED)
        self.stop_button = ttk.Button(mainframe, text='Стоп', command=self.stop, width=20, state=DISABLED)

        mainframe.grid(column=0, row=0)
        filename_label.grid(column=0, row=0, sticky=(N, W), padx=10, columnspan=5)
        self.filename_entry.grid(column=0, row=1, sticky=(N, W), padx=(15, 0), pady=(1, 1), columnspan=4)
        self.filename_button.grid(column=4, row=1, sticky=(N, E), padx=(0, 15), pady=(1, 1))
        period_label.grid(column=0, row=2, sticky=(N, W), padx=10, columnspan=5)
        self.period_spinbox.grid(column=0, row=3, sticky=(N, W), padx=15, pady=(1, 10), columnspan=2)
        self.start_button.grid(column=0, row=4, sticky=(N, W), padx=(15, 1), pady=(1, 5), columnspan=2)
        self.stop_button.grid(column=3, row=4, sticky=(N, W), padx=(1, 15), pady=(1, 5), columnspan=2)

    def set_defaults(self):
        self.filename.set(DEFAULT_FILE_PATH / f'{date.today()}.txt')
        self.period.set(DEFAULT_PERIOD)

    def start(self):
        self.thread = Thread(target=read_data, args=(self, self.serial_port, self.filename.get(), self.period.get()))
        self.thread.start()
        self.stop_button.config(state=NORMAL)
        self.filename_entry.config(state='readonly')
        self.period_spinbox.config(state=DISABLED)
        self.filename_button.config(state=DISABLED)
        self.start_button.config(state=DISABLED)

    def stop(self):
        if self.thread:
            self.thread.stop_thread = True
        self.filename_entry.config(state=NORMAL)
        self.period_spinbox.config(state=NORMAL)
        self.filename_button.config(state=NORMAL)
        self.start_button.config(state=NORMAL)
        self.stop_button.config(state=DISABLED)

    def select_file(self):
        self.filename.set(fd.askopenfilename(filetypes=[('Text files', '.txt')]))
        self.filename_entry.xview('end')

    def filename_write_callback(self, *args):
        self.filename_entry.bind('<Expose>', xview_event_handler)
        filename = self.filename.get()
        if filename and filename.endswith('.txt'):
            self.start_button.config(state=NORMAL)

    def period_write_callback(self, *args):
        period = self.period.get()
        if not isinstance(period, int):
            return self.period.set(DEFAULT_PERIOD)
        if period > MAX_PERIOD:
            return self.period.set(MAX_PERIOD)
        if period < MIN_PERIOD:
            return self.period.set(MIN_PERIOD)

    def reset_layout(self):
        self.filename_entry.config(state=NORMAL)
        self.period_spinbox.config(state=NORMAL)
        self.filename_button.config(state=NORMAL)
        self.start_button.config(state=DISABLED)
        self.stop_button.config(state=DISABLED)


def xview_event_handler(e):
    e.widget.update_idletasks()
    e.widget.xview('end')
    e.widget.unbind('<Expose>')


