from datetime import date
from threading import Thread, Timer
from tkinter import *
from tkinter import ttk, filedialog as fd

from config import STATIC_PATH, DEFAULT_FILE_PATH, DEFAULT_PERIOD, MIN_PERIOD, MAX_PERIOD
from reader import read_data


class Layout:
    def __init__(self, root, serial_port):
        self.root = root
        self.serial_port = serial_port
        self.thread = None
        self.timer = Timer(1, self.set_time)
        self.is_running = False
        range_validation = root.register(self.validate_period)
        mainframe = ttk.Frame(root, padding="5 5 5 5")

        self.filename = StringVar()
        self.filename.trace_add("write", self.filename_write_callback)
        filename_label = ttk.Label(mainframe, text='Название файла: ')
        self.filename_entry = ttk.Entry(mainframe, textvariable=self.filename, width=50)
        self.filename_button_image = PhotoImage(file=STATIC_PATH / "file.png")
        filename_buttons = ttk.Frame(mainframe)
        self.filename_open_button = ttk.Button(filename_buttons, text='Открыть файл', command=self.select_file,
                                               width=20)
        self.filename_save_button = ttk.Button(filename_buttons, text='Создать новый файл', command=self.save_file,
                                               width=20)

        self.period = IntVar()
        self.period.trace_add("write", self.period_write_callback)
        period_label = ttk.Label(mainframe, text='Период записи(сек.):')
        self.period_spinbox = ttk.Spinbox(mainframe,
                                          textvariable=self.period,
                                          validate='key',
                                          validatecommand=(range_validation, '%P'),
                                          from_=MIN_PERIOD,
                                          to=MAX_PERIOD,
                                          increment=1)

        self.start_button = ttk.Button(mainframe, text='Старт', command=self.start, width=20, state=DISABLED)
        self.stop_button = ttk.Button(mainframe, text='Стоп', command=self.stop, width=20, state=DISABLED)

        info = ttk.Frame(mainframe)
        self.time_elapsed = IntVar()
        self.time_elapsed_label = ttk.Label(info, text='Прошло времени(сек.):')
        self.time_elapsed_text = ttk.Entry(info, textvariable=self.time_elapsed, state='readonly', width=20)
        self.entries_made = IntVar()
        self.entries_made_label = ttk.Label(info, text='Записей сделано:')
        self.entries_made_text = ttk.Entry(info, textvariable=self.entries_made, state='readonly', width=20)

        mainframe.grid(column=0, row=0)
        filename_label.grid(column=0, row=0, sticky=(N, W), padx=10, columnspan=5)
        self.filename_entry.grid(column=0, row=1, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=4)
        filename_buttons.grid(column=0, row=2, padx=(0, 0), pady=(1, 1), columnspan=4)
        self.filename_open_button.grid(column=0, row=0, sticky=(N, W), padx=(10, 17), pady=(1, 1), columnspan=2)
        self.filename_save_button.grid(column=3, row=0, sticky=(N, W), padx=(17, 10), pady=(1, 1), columnspan=2)
        period_label.grid(column=0, row=3, sticky=(N, W), padx=10, columnspan=5)
        self.period_spinbox.grid(column=0, row=4, sticky=(N, W), padx=15, pady=(1, 10), columnspan=2)
        info.grid(column=0, row=5, padx=(0, 0), pady=(1, 1), columnspan=4)
        self.time_elapsed_label.grid(column=0, row=0, sticky=(N, W), padx=(10, 15), pady=(1, 1), columnspan=2)
        self.entries_made_label.grid(column=3, row=0, sticky=(N, W), padx=(15, 10), pady=(1, 1), columnspan=2)
        self.time_elapsed_text.grid(column=0, row=1, sticky=(N, W), padx=(10, 15), pady=(1, 1), columnspan=2)
        self.entries_made_text.grid(column=3, row=1, sticky=(N, W), padx=(15, 10), pady=(1, 1), columnspan=2)
        self.start_button.grid(column=0, row=6, sticky=(N, W), padx=(15, 1), pady=(1, 5), columnspan=2)
        self.stop_button.grid(column=3, row=6, sticky=(N, W), padx=(1, 15), pady=(1, 5), columnspan=2)

    def set_defaults(self):
        self.filename.set(DEFAULT_FILE_PATH / f'{date.today()}.txt')
        self.period.set(DEFAULT_PERIOD)

    def start(self):
        self.time_elapsed.set(0)
        self.entries_made.set(0)
        self.is_running = True
        self.thread = Thread(target=read_data, args=(self, self.serial_port, self.filename.get(), self.period.get()))
        self.thread.start()
        self.stop_button.config(state=NORMAL)
        self.filename_entry.config(state='readonly')
        self.period_spinbox.config(state=DISABLED)
        self.filename_open_button.config(state=DISABLED)
        self.filename_save_button.config(state=DISABLED)
        self.start_button.config(state=DISABLED)
        self.root.after(1000, self.set_time)

    def stop(self):
        if self.thread:
            self.thread.stop_thread = True
            self.is_running = False
        self.filename_entry.config(state=NORMAL)
        self.period_spinbox.config(state=NORMAL)
        self.filename_open_button.config(state=NORMAL)
        self.filename_save_button.config(state=NORMAL)
        self.start_button.config(state=NORMAL)
        self.stop_button.config(state=DISABLED)

    def set_time(self):
        self.time_elapsed.set(self.time_elapsed.get() + 1)
        if self.is_running:
            self.root.after(1000, self.set_time)

    def select_file(self):
        self.filename.set(fd.askopenfilename(filetypes=[('Text files', '.txt')]))
        self.filename_entry.xview('end')

    def save_file(self):
        self.filename.set(fd.asksaveasfilename(filetypes=[('Text file', '.txt')], defaultextension='.txt'))
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
        if period > MAX_PERIOD or period < MIN_PERIOD:
            return self.start_button.config(state=DISABLED)
        self.start_button.config(state=NORMAL)

    def validate_period(self, user_input):
        self.start_button.config(state=DISABLED)
        if user_input.isdigit() or user_input == '':
            return True
        return False

    def reset_layout(self):
        self.filename_entry.config(state=NORMAL)
        self.period_spinbox.config(state=NORMAL)
        self.filename_open_button.config(state=NORMAL)
        self.filename_save_button.config(state=NORMAL)
        self.start_button.config(state=DISABLED)
        self.stop_button.config(state=DISABLED)


def xview_event_handler(e):
    e.widget.update_idletasks()
    e.widget.xview('end')
    e.widget.unbind('<Expose>')


