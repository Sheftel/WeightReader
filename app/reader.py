import datetime
import os
import re
import time
from threading import current_thread, Thread

from serial import SerialException
from config import ROOT_PATH, DEBUG
from debug_list import reading_list
from utils import raise_error, sample_max_volume_reached_mb


class Reader:
    debug = DEBUG
    interpolation_data = None
    last_read = {}
    last_entry = {}
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
    reading_list = reading_list

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
            passed_validation = False
            if reading is not None:
                if self.validate_reading(reading, calculation_data, last_reading = self.last_entry['mass'] if self.last_entry else 0):
                    passed_validation = True
                    Thread(target=self.handle,
                           args=(layout, time_elapsed, reading,
                                 calculation_data, last_reading, digits_after_dec)).start()
                    last_reading = reading
                else:
                    passed_validation = False
            if time_elapsed % period == 0:
                if passed_validation:
                    self.handle_interpolation(layout, reading,
                                 calculation_data, self.last_entry)
                    mass, mass_difference, volume, flow, permeability = self.calculate(self.last_read['mass'], calculation_data,
                                   last_reading=self.last_entry['mass'] if self.last_entry else None)
                    entry = {
                        'mass': mass,
                        'mass_difference': mass_difference,
                        'flow': flow,
                        'volume':  volume,
                        'permeability': permeability,
                    }
                    self.write_reading(time_elapsed, entry['mass'], entry['mass_difference'], entry['flow'], entry['permeability'])
                    self.last_entry = entry
                    layout.entries_made.set(layout.entries_made.get() + 1)
                else:
                    self.interpolation_data  = {
                        'reading': reading,
                        'time': time_elapsed
                    }
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

    def validate_reading(self, reading, calculation_data, last_reading = 0):
        diff = reading - last_reading if not self.interpolation_data else reading - self.interpolation_data['reading']
        if diff < 0 and abs(diff / last_reading) * 100 > calculation_data['percent']:
            return False
        return True

    def handle(self, layout, now, reading, calculation_data, last_reading=None, digits_after_dec=2):
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

    def handle_interpolation(self, layout, reading, calculation_data, last_entry=None):
        if self.interpolation_data:
            mass, mass_difference, volume, flow, permeability = self.calculate(reading, calculation_data,
                                                                               last_reading=self.interpolation_data[
                                                                                     'reading'])
            (inter_mass, inter_diff, inter_volume,
             inter_flow, inter_perm) = self.calculate(self.interpolation_data['reading'], calculation_data,
                                                      last_reading=last_entry['mass'],
                                                      interpolate=True,
                                                      prev_diff=last_entry['mass_difference'],
                                                      next_diff=mass_difference)

            self.write_reading(self.interpolation_data['time'], inter_mass, inter_diff, inter_flow, inter_perm)
            layout.entries_made.set(layout.entries_made.get() + 1)
            self.interpolation_data = None

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
        self.layout.sample_value.set(f"{self.sample_data['current_volume']:.{self.digits_after_dec}f}")

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
