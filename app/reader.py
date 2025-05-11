import datetime
import os
import re
import time
from threading import current_thread, Thread

from serial import SerialException
from config import ROOT_PATH
from utils import raise_error, sample_max_volume_reached_mb


class Reader:
    debug = False
    interpolation_data = None
    last_read = {}
    log_file = None
    filename = None
    digits_after_dec = 2
    collect_samples = False
    layout = None
    sample_data = {
        "current_volume": 0.0,
        "current_sample": 1,
        "continue_sample": False,
        "start_time": 0
    }
    reading_list =['0.01  g', '0.02  g', '0.03  g', '0.04  g', '0.05  g', '0.06  g', '0.07  g', '0.08  g', '0.09  g', '0.10  g', '0.12  g', '0.14  g', '0.16  g', '0.18  g', '0.20  g', '0.22  g', '0.24  g', '0.26  g', '0.28  g', '0.30  g', '0.33  g', '0.36  g', '0.39  g', '0.42  g', '0.45  g', '0.48  g', '0.51  g', '0.54  g', '0.57  g', '0.60  g', '0.64  g', '0.68  g', '0.72  g', '0.76  g', '0.80  g', '0.84  g', '0.88  g', '0.92  g', '0.96  g', '1.00  g', '1.05  g', '1.10  g', '1.15  g', '1.20  g', '1.25  g', '1.30  g', '1.35  g', '1.40  g', '1.45  g', '1.50  g', '1.56  g', '1.62  g', '1.68  g', '1.74  g', '1.80  g', '1.86  g', '1.92  g', '1.98  g', '2.04  g', '2.10  g', '2.17  g', '2.24  g', '2.31  g', '2.38  g', '2.45  g', '2.52  g', '2.59  g', '2.66  g', '2.73  g', '2.80  g', '2.88  g', '2.96  g', '3.04  g', '3.12  g', '3.20  g', '3.28  g', '3.36  g', '3.44  g', '3.52  g', '3.60  g', '3.69  g', '3.78  g', '3.87  g', '3.96  g', '4.05  g', '4.14  g', '4.23  g', '4.32  g', '4.41  g', '4.50  g', '4.60  g', '4.70  g', '4.80  g', '4.90  g', '5.00  g', '5.10  g', '5.20  g', '5.30  g', '5.40  g', '5.50  g']

    def read_data(self, layout, serial, calculation_data, samples_data, filename, period=1, runtime=None,
                  digits_after_dec=3, logging=False):
        """
        writes data read from serial port to given file.
        assumes that this method won't be called with filename = None
        """
        thread = current_thread()
        self.layout = layout
        try:
            serial.timeout = 1
        except SerialException as e:
            raise_error(message=f'Возникла проблема с доступом к порту:{e}', layout=self.layout)

        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        except FileNotFoundError:
            raise_error(message="Ошибка в пути к файлу.", layout=self.layout)
            return layout.reset_layout()

        self.filename = filename
        self.digits_after_dec = digits_after_dec

        if samples_data['collect_samples']:
            self.collect_samples = True
            self.sample_data['max_volume'] = samples_data['max_sample_value']
            self.sample_data['current_sample'] = 1
            self.sample_data['start_time'] = 0
            self.sample_data['filename'] = self.filename.rstrip('.txt') + "_пробы.txt"

        if logging:
            self.log_file = open(ROOT_PATH / f'log_{datetime.date.today()}_{serial.port}', "a+")
            self.log_file.write('\n[LOG START]\n')
            serial.flushInput()
        with open(self.filename, "a+", encoding="utf-8") as file:
        #file = open(self.filename, "a+")
            file.write(f"{datetime.date.today()}  {datetime.datetime.now().strftime('%H:%M')}\n")
            file.write(
                f"Время, с  Масса, г   Разность масс, г   Поток, {'л/м2 час' if calculation_data['flow_dimension'] == 1 else 'м3/м2 час'}  Проницаемость, {'л/м2 час бар' if calculation_data['flow_dimension'] == 1 else 'м3/м2 час бар'}\n")
        last_reading = 0
        time_elapsed = layout.time_elapsed.get()

        while not getattr(thread, "stop_thread", False) and (runtime is None or time_elapsed <= runtime):
            start = time.time()
            layout.time_elapsed.set(time_elapsed)
            if self.collect_samples:
                self.update_samples_layout_data(time_elapsed)
            if getattr(thread, "start_new_sample", False):
                setattr(thread, "start_new_sample", False)
                self.handle_start_new_sample_command(time_elapsed)
            reading = self.get_reading(serial, logging=logging)
            if reading is not None:
                if self.validate_reading(reading, last_reading, calculation_data):
                    Thread(target=self.handle,
                           args=(layout, time_elapsed, reading,
                                 calculation_data, last_reading, digits_after_dec)).start()
                    last_reading = reading
                else:
                    self.interpolation_data = {'reading': reading,
                                               'time': time_elapsed}

            if time_elapsed % period == 0:
                self.write_reading(time_elapsed, self.last_read['mass'], self.last_read['mass_difference'], self.last_read['flow'], self.last_read['permeability'])
                layout.entries_made.set(layout.entries_made.get() + 1)
            time_elapsed += 1
            elapsed = time.time() - start
            time.sleep(1. - min(1., elapsed))
        time.sleep(1.)

        file = open(filename, "a+", encoding="utf-8")
        file.write('\n')
        file.close()
        if logging:
            self.log_file.write('\n[LOG END]\n')
            self.log_file.close()

    def get_reading(self, serial, logging=False):
        try:
            if self.debug:
                buffer = '\n'
                reading = self.get_debug_reading()
            else:
                buffer = serial.read(serial.in_waiting).decode()
                reading = serial.readline().decode()
        except OSError:
            raise_error("Потеряна связь с весами", "Потеряна связь с весами. Проверьте подключение и запустите программу снова", layout=self.layout)
            current_thread().stop_thread = True
            self.layout.reset_layout()
        except UnicodeDecodeError as e:
            raise_error("Ошибка обработки", f"Возникла ошибка при обработке данных. {e}", layout=self.layout)
            current_thread().stop_thread = True
            self.layout.reset_layout()

        if not buffer.endswith('\n'):
            if '\n' in buffer:
                split_buffer = buffer.split('\n')
                last_string = split_buffer[-1]
                buffer = split_buffer[:-1]
            else:
                last_string = buffer
                buffer = ''
            reading = last_string + reading
        reading = reading or '-  0.00  g  !\r\n'
        if logging:
            self.write_log(data=buffer + reading)
        try:
            reading = re.search(r'(\d+\.\d+)', reading).group(1)
            reading = float(reading.rstrip(' ').rstrip('g'))
        except ValueError:
            reading = None
        except AttributeError:
            reading = self.get_reading(serial)
        return reading

    def validate_reading(self, reading, last_reading, calculation_data):
        diff = reading - last_reading if not self.interpolation_data else reading - self.interpolation_data['reading']
        if diff < 0 and abs(diff / last_reading) * 100 > calculation_data['percent']:
            return False
        return True

    def handle(self, layout, now, reading, calculation_data, last_reading=None, digits_after_dec=2):
        if self.interpolation_data:
            mass, mass_difference, volume, flow, permeability = self.calculate(reading, calculation_data,
                                                                               last_reading=self.interpolation_data[
                                                                                     'reading'])
            (inter_mass, inter_diff, inter_volume,
             inter_flow, inter_perm) = self.calculate(self.interpolation_data['reading'], calculation_data,
                                                      last_reading=last_reading,
                                                      interpolate=True,
                                                      prev_diff=self.last_read['mass_difference'],
                                                      next_diff=mass_difference)

            self.write_reading(self.interpolation_data['time'], inter_mass, inter_diff, inter_flow, inter_perm)
            layout.entries_made.set(layout.entries_made.get() + 1)
            self.interpolation_data = None
        else:
            mass, mass_difference, volume, flow, permeability = self.calculate(reading, calculation_data,
                                                                               last_reading=last_reading)
        self.last_read = {
            'mass': mass,
            'mass_difference': mass_difference,
            'volume': volume,
            'flow': flow,
            'permeability': permeability
        }

        if self.collect_samples:
            self.handle_samples(now)

    def calculate(self, reading, calculation_data, last_reading=0.0, interpolate=False, prev_diff=None, next_diff=None):
        if interpolate:
            mass_difference = (prev_diff + next_diff) / 2
        else:
            mass_difference = reading - last_reading if last_reading is not None else 0
        volume = (mass_difference / 1000 / calculation_data['density']) / calculation_data['interval']
        flow = volume * 3600 / calculation_data['surface'] * 1000
        flow = flow / calculation_data['flow_dimension']
        permeability = flow / calculation_data['difference']
        return reading, mass_difference, volume, flow, permeability

    def write_log(self, data):
        self.log_file.write(data)
        self.log_file.flush()

    def write_reading(self, current_time, mass, mass_difference, flow, permeability):
        with open(self.filename, "a+", encoding="utf-8") as file:
            file.write(
                f"{current_time}  {mass:.{self.digits_after_dec}f}  {mass_difference:.{self.digits_after_dec}f}  {flow:.{self.digits_after_dec}f}  {permeability:.{self.digits_after_dec}f}\n")

    def new_sample(self, time_elapsed):
        sample_data = self.sample_data
        if sample_data['current_sample'] == 1:
            file = open(sample_data['filename'], "a+", encoding="utf-8")
            file.write(f"{datetime.date.today()}  {datetime.datetime.now().strftime('%H:%M')}\n")
            file.write(
                f"Номер пробы; Время начала сбора пробы, сек; Время конца сбора пробы, сек; Объем пробы, мл\n")
            file.close()
        file = open(sample_data['filename'], "a+", encoding="utf-8")
        file.write(f"{sample_data['current_sample']}  "
                   f"{sample_data['start_time']}  "
                   f"{time_elapsed}  "
                   f"{sample_data['current_volume']:.{self.digits_after_dec}f}\n")
        file.flush()
        file.close()
        self.sample_data['current_sample'] += 1
        self.sample_data['current_volume'] = 0.0
        self.sample_data['start_time'] = time_elapsed
        self.sample_data['continue_sample'] = False
        self.update_samples_layout_data(time_elapsed)

    def handle_samples(self, time_elapsed):
        self.sample_data['current_volume'] += self.last_read['mass_difference']
        if not self.sample_data['continue_sample']:
            if self.sample_data['current_volume'] >= self.sample_data['max_volume']:
                Thread(target=self.handle_sample_max_volume_reached,
                       args=[time_elapsed]).start()

    def handle_start_new_sample_command(self, time_elapsed):
        self.new_sample(time_elapsed)

    def handle_sample_max_volume_reached(self, time_elapsed):
        self.sample_data['continue_sample'] = True
        messagebox_answer = sample_max_volume_reached_mb(self.sample_data['max_volume'], self.sample_data['current_sample'], self.layout)
        if messagebox_answer:
            self.new_sample(self.layout.time_elapsed.get())

    def update_samples_layout_data(self, time_elapsed):
        self.layout.current_sample.set(self.sample_data['current_sample'])
        self.layout.sample_time_elapsed.set(time_elapsed - self.sample_data['start_time'])
        self.layout.sample_value.set(self.sample_data['current_volume'])

    def get_debug_reading(self):
        # DEBUG LIST GENERATOR
        # for i in range(0, 100):
        #     if i == 0:
        #         list = []
        #         last_value = 0.00
        #     value = last_value + (1 + i // 10) * 0.01
        #     list.append(f'{value:.2f}  g')
        #     last_value = value
        if self.reading_list:
            return self.reading_list.pop(0)
        return "-  0.00  g  !\r\n"
