import math

from datetime import date
from threading import Thread
from tkinter import *
from tkinter import ttk, filedialog as fd
from serial import Serial, SerialException

from config import *
from utils import raise_error, xview_event_handler
from reader import Reader


class Layout:
    def __init__(self, root):
        self.root = root
        self.thread = None
        self.serial = None
        self.is_running = False
        self.runtime_seconds = None
        range_validation = root.register(self.validate_range)

        # frames
        mainframe = ttk.Frame(root, padding="5 5 5 5")
        app_params = ttk.Frame(mainframe)
        run_params = ttk.LabelFrame(mainframe, text='Параметры', width=210, height=450)
        output = ttk.LabelFrame(mainframe, text='Вывод', width=210, height=450)
        flow_dimension_frame = ttk.LabelFrame(run_params, text='Размерность потока', width=180, height=50)
        run_buttons = ttk.Frame(mainframe)

        mainframe.grid(column=0, row=0)
        app_params.grid(column=0, row=0, sticky=(N, W), padx=10, pady=(0, 5), columnspan=5)
        run_params.grid(column=0, row=1, sticky=(N, W), padx=(15, 15), pady=(0, 2), columnspan=2)
        output.grid(column=2, row=1, sticky=(N, E), padx=(15, 5), pady=(0, 2), columnspan=2)
        run_buttons.grid(column=0, row=2, sticky=(N, W), padx=10, pady=(0, 5), columnspan=5)

        # app params
        self.filename = StringVar(value=DEFAULT_FILE_PATH / f'{date.today()}.txt')
        self.filename.trace_add("write", self.filename_write_callback)
        filename_label = ttk.Label(app_params, text='Название файла: ')
        self.filename_entry = ttk.Entry(app_params, textvariable=self.filename, width=40)
        filename_buttons = ttk.Frame(app_params)
        self.filename_open_button = ttk.Button(filename_buttons, text='Открыть', command=self.select_file,
                                               width=15)
        self.filename_save_button = ttk.Button(filename_buttons, text='Создать новый', command=self.save_file,
                                               width=15)
        self.settings_button = ttk.Button(app_params, text='Настройки cерийного порта', command=self.serial_settings,
                                          width=74)
        filename_label.grid(column=0, row=0, sticky=(N, W), padx=10, columnspan=5)
        self.filename_entry.grid(column=0, row=1, sticky=(N, W), padx=(5, 5), pady=(3, 1), columnspan=2)
        filename_buttons.grid(column=2, row=1, padx=(0, 0), pady=(1, 1), columnspan=2)
        self.filename_save_button.grid(column=0, row=0, sticky=(N, W), padx=(0, 0), pady=(0, 1), columnspan=2)
        self.filename_open_button.grid(column=2, row=0, sticky=(N, W), padx=(0, 0), pady=(0, 1), columnspan=2)

        self.settings_button.grid(column=0, row=2, padx=(3, 0), pady=(1, 1), columnspan=5)

        # run params
        run_params.grid_propagate(FALSE)
        self.difference = DoubleVar(value=4)
        self.interval = IntVar(value=DEFAULT_INTERVAL)
        self.interval.trace_add("write", self.interval_write_callback)
        self.diameter = DoubleVar(value=19)
        self.density = DoubleVar(value=997.1)
        self.diff_percent = DoubleVar(value=5)
        self.flow_dimension = IntVar(value=1)
        self.runtime = IntVar()
        self.digits_after_dec = IntVar(value=2)
        spinbox_width = 27

        difference_label = ttk.Label(run_params, text='Разность давлений (бар):')
        self.difference_spinbox = ttk.Spinbox(run_params,
                                              width=spinbox_width,
                                              textvariable=self.difference,
                                              validate='key',
                                              validatecommand=(range_validation, '%P'),
                                              from_=0,
                                              to=1000,
                                              increment=1)

        interval_label = ttk.Label(run_params, text='Интервал записи (секунд):')
        self.interval_spinbox = ttk.Spinbox(run_params,
                                            width=spinbox_width,
                                            textvariable=self.interval,
                                            validate='key',
                                            validatecommand=(range_validation, '%P'),
                                            from_=MIN_INTERVAL,
                                            to=MAX_INTERVAL,
                                            increment=1)

        diameter_label = ttk.Label(run_params, text='Диаметр рабочей поверхности\nмембраны (мм):')
        self.diameter_spinbox = ttk.Spinbox(run_params,
                                            width=spinbox_width,
                                            textvariable=self.diameter,
                                            validate='key',
                                            validatecommand=(range_validation, '%P'),
                                            from_=1,
                                            to=1000,
                                            increment=1)

        density_label = ttk.Label(run_params, text='Плотность воды при\nкомнатной температуре (кг/м3):')
        self.density_spinbox = ttk.Spinbox(run_params,
                                           width=spinbox_width,
                                           textvariable=self.density,
                                           validate='key',
                                           validatecommand=(range_validation, '%P'),
                                           from_=0,
                                           to=1000,
                                           increment=1)
        diff_percent_label = ttk.Label(run_params, text='Процент уменьшения массы\nдля интерполяции')
        self.diff_percent_spinbox = ttk.Spinbox(run_params,
                                                width=spinbox_width,
                                                textvariable=self.diff_percent,
                                                validate='key',
                                                validatecommand=(range_validation, '%P'),
                                                from_=0.01,
                                                to=100,
                                                increment=1)
        #   flow_dimension_label = ttk.Label(run_params, text='Размерность потока')
        self.flow_dimension_radio_one = ttk.Radiobutton(flow_dimension_frame, text='л/м2 час',
                                                        variable=self.flow_dimension, value=1)
        self.flow_dimension_radio_thousand = ttk.Radiobutton(flow_dimension_frame, text='м3/м2 час',
                                                             variable=self.flow_dimension, value=1000)
        runtime_label = ttk.Label(run_params, text='Время эксперимента(минут):')
        self.runtime_spinbox = ttk.Spinbox(run_params,
                                           width=spinbox_width,
                                           textvariable=self.runtime,
                                           validate='key',
                                           validatecommand=(range_validation, '%P'),
                                           from_=0,
                                           to=1000,
                                           increment=1)
        digits_after_dec_label = ttk.Label(run_params, text='Количество символов после\nзапятой:')
        self.digits_after_dec_spinbox = ttk.Spinbox(run_params,
                                                    width=spinbox_width,
                                                    textvariable=self.digits_after_dec,
                                                    validate='key',
                                                    validatecommand=(range_validation, '%P'),
                                                    from_=1,
                                                    to=6,
                                                    increment=1)

        difference_label.grid(column=0, row=0, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=2)
        self.difference_spinbox.grid(column=0, row=1, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=2)
        interval_label.grid(column=0, row=2, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=2)
        self.interval_spinbox.grid(column=0, row=3, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=2)
        diameter_label.grid(column=0, row=4, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=2)
        self.diameter_spinbox.grid(column=0, row=5, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=2)
        density_label.grid(column=0, row=6, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=2)
        self.density_spinbox.grid(column=0, row=7, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=2)
        diff_percent_label.grid(column=0, row=8, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=2)
        self.diff_percent_spinbox.grid(column=0, row=9, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=2)
        runtime_label.grid(column=0, row=10, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=2)
        self.runtime_spinbox.grid(column=0, row=11, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=2)
        digits_after_dec_label.grid(column=0, row=12, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=2)
        self.digits_after_dec_spinbox.grid(column=0, row=13, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=2)
        flow_dimension_frame.grid(column=0, row=14, sticky=(N, W), padx=(10, 10), pady=(1, 1))

        # flow_dimension
        flow_dimension_frame.grid_propagate(FALSE)

        self.flow_dimension_radio_one.grid(column=0, row=0, sticky=(N, W), padx=(10, 5), pady=(1, 1), columnspan=2)
        self.flow_dimension_radio_thousand.grid(column=2, row=0, sticky=(N, W), padx=(5, 10), pady=(1, 1), columnspan=2)



        # output
        output.grid_propagate(FALSE)

        self.time_elapsed = IntVar()
        self.time_elapsed_label = ttk.Label(output, text='Прошло времени(сек.):')
        self.time_elapsed_text = ttk.Entry(output, textvariable=self.time_elapsed, state='readonly', width=30)
        self.entries_made = IntVar()
        self.entries_made_label = ttk.Label(output, text='Записей сделано:')
        self.entries_made_text = ttk.Entry(output, textvariable=self.entries_made, state='readonly', width=30)
        self.time_elapsed_label.grid(column=0, row=0, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=2)
        self.time_elapsed_text.grid(column=0, row=1, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=2)
        self.entries_made_label.grid(column=0, row=2, sticky=(N, W), padx=(10, 10), pady=(1, 1), columnspan=2)
        self.entries_made_text.grid(column=0, row=3, sticky=(N, W), padx=(10, 10), pady=(1, 5), columnspan=2)

        # run buttons
        self.start_button = ttk.Button(run_buttons, text='Старт', command=self.start, width=34, state=NORMAL)
        self.stop_button = ttk.Button(run_buttons, text='Стоп', command=self.stop, width=34, state=DISABLED)
        self.start_button.grid(column=0, row=0, sticky=(N, W), padx=(3, 12), pady=(1, 5), columnspan=2)
        self.stop_button.grid(column=3, row=0, sticky=(N, W), padx=(14, 2), pady=(1, 5), columnspan=2)

        self.serial_settings()

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

    def interval_write_callback(self, *args):
        interval = self.interval.get()
        if not isinstance(interval, int):
            return self.interval.set(DEFAULT_INTERVAL)
        if interval > MAX_INTERVAL or interval < MIN_INTERVAL:
            return self.start_button.config(state=DISABLED)
        self.start_button.config(state=NORMAL)

    def validate_range(self, user_input):
        self.start_button.config(state=DISABLED)
        if user_input.isdigit() or user_input == '' or user_input == '.':
            self.start_button.config(state=NORMAL)
            return True
        return False

    def serial_settings(self):
        SettingsLayout(self.root, self)

    def start(self):
        calculation_data = {
            'difference': self.difference.get(),
            'diameter': self.diameter.get(),
            'interval': self.interval.get(),
            'density': self.density.get(),
            'surface': (math.pi * math.pow(self.diameter.get() / 1000, 2)) / 4,
            'percent': self.diff_percent.get(),
            'flow_dimension': self.flow_dimension.get()
        }
        self.time_elapsed.set(0)
        self.entries_made.set(0)
        self.runtime_seconds = self.runtime.get() * 60 if self.runtime.get() > 0 else None
        self.is_running = True
        self.thread = Thread(target=Reader.read_data,
                             args=(Reader(), self, self.serial, calculation_data, self.filename.get(),
                                   self.interval.get(), self.runtime_seconds, self.digits_after_dec.get()))
        self.thread.start()
        self.stop_button.config(state=NORMAL)
        self.filename_entry.config(state='readonly')
        self.settings_button.config(state=DISABLED)
        self.difference_spinbox.config(state=DISABLED)
        self.flow_dimension_radio_one.config(state=DISABLED)
        self.flow_dimension_radio_thousand.config(state=DISABLED)
        self.diff_percent_spinbox.config(state=DISABLED)
        self.interval_spinbox.config(state=DISABLED)
        self.density_spinbox.config(state=DISABLED)
        self.diameter_spinbox.config(state=DISABLED)
        self.runtime_spinbox.config(state=DISABLED)
        self.digits_after_dec_spinbox.config(state=DISABLED)
        self.filename_open_button.config(state=DISABLED)
        self.filename_save_button.config(state=DISABLED)
        self.start_button.config(state=DISABLED)

    def stop(self):
        if self.thread:
            self.thread.stop_thread = True
            self.is_running = False
        self.filename_entry.config(state=NORMAL)
        self.settings_button.config(state=NORMAL)
        self.difference_spinbox.config(state=NORMAL)
        self.flow_dimension_radio_one.config(state=NORMAL)
        self.flow_dimension_radio_thousand.config(state=NORMAL)
        self.diff_percent_spinbox.config(state=NORMAL)
        self.interval_spinbox.config(state=NORMAL)
        self.density_spinbox.config(state=NORMAL)
        self.diameter_spinbox.config(state=NORMAL)
        self.runtime_spinbox.config(state=NORMAL)
        self.digits_after_dec_spinbox.config(state=NORMAL)
        self.filename_open_button.config(state=NORMAL)
        self.filename_save_button.config(state=NORMAL)
        self.start_button.config(state=NORMAL)
        self.stop_button.config(state=DISABLED)


class SettingsLayout:
    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        self.window = Toplevel(self.root)
        self.window.title = 'Настройки порта'
        self.window.resizable(FALSE, FALSE)
        frame = ttk.Frame(self.window, padding=(5, 5, 5, 5))
        self.port = StringVar(value=SERIAL_PORT)
        port_label = ttk.Label(frame, text='Порт подключения: ')
        port_entry = ttk.Entry(frame, textvariable=self.port, width=50)

        self.baudrate = IntVar(value=SERIAL_BAUDRATE)
        baudrate_label = ttk.Label(frame, text='Бит в секунду: ')
        baudrate_combobox = ttk.Combobox(frame, textvariable=self.baudrate,
                                         width=47,
                                         state='readonly', values=['75', '110', '134', '150',
                                                                   '300', '600', '1200', '1800',
                                                                   '2400', '4800', '7200', '9600',
                                                                   '14400', '19200', '38400', '57600',
                                                                   '115200', '12800'])
        self.bytesize = IntVar(value=SERIAL_BITESIZE)
        bytesize_label = ttk.Label(frame, text='Биты данных: ')
        bytesize_combobox = ttk.Combobox(frame, textvariable=self.bytesize,
                                         width=47,
                                         state='readonly', values=['4', '5', '6', '7', '8'])

        self.parity = StringVar(value=SERIAL_PARITY)
        parity_label = ttk.Label(frame, text='Четность: ')
        parity_combobox = ttk.Combobox(frame, textvariable=self.parity,
                                       width=47,
                                       state='readonly', values=['E', 'O', 'N', 'M', 'S'])
        self.stopbits = DoubleVar(value=SERIAL_STOPBITS)
        stopbits_label = ttk.Label(frame, text='Стоповые биты: ')
        stopbits_combobox = ttk.Combobox(frame, textvariable=self.stopbits,
                                         width=47,
                                         state='readonly', values=['1', '1.5', '2'])
        confirm_button = ttk.Button(frame, text='Принять', command=self.confirm, width=50)

        frame.grid(row=0, column=0)
        port_label.grid(row=0, column=0, sticky=(N, W))
        port_entry.grid(row=1, column=0)
        baudrate_label.grid(row=2, column=0, sticky=(N, W))
        baudrate_combobox.grid(row=3, column=0)
        bytesize_label.grid(row=4, column=0, sticky=(N, W))
        bytesize_combobox.grid(row=5, column=0)
        parity_label.grid(row=6, column=0, sticky=(N, W))
        parity_combobox.grid(row=7, column=0)
        stopbits_label.grid(row=8, column=0, sticky=(N, W))
        stopbits_combobox.grid(row=9, column=0)

        confirm_button.grid(row=10, column=0, pady=(5, 1))

        self.window.grab_set()

    def confirm(self):
        if self.parent.serial:
            self.parent.serial.close()
        try:
            self.parent.serial = Serial(
                port=self.port.get(),
                baudrate=self.baudrate.get(),
                bytesize=self.bytesize.get(),
                parity=self.parity.get(),
                stopbits=self.stopbits.get()
            )
        except SerialException as e:
            raise_error(message=f'Невозможно подключиться к порту:{e}')
        else:
            self.window.grab_release()
            self.window.destroy()
