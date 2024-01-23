import datetime
import os
import time
from threading import current_thread, Thread

from config import ROOT_PATH
from utils import raise_error


class Reader:
    interpolation_data = None
    last_read = {}
    log_file = None
    filename = None

    def read_data(self, layout, serial, calculation_data, filename, period=1, runtime=None, digits_after_dec=3, logging=False):
        """
        writes data read from serial port to given file.
        assumes that this method won't be called with filename = None
        """
        thread = current_thread()
        serial.timeout = 1
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        except FileNotFoundError:
            raise_error(message="Ошибка в пути к файлу.")
            return layout.reset_layout()
        self.filename = filename
        if logging:
            self.log_file = open(ROOT_PATH/f'log_{datetime.date.today()}_{serial.port}', "a+")
            self.log_file.write('\n[LOG START]\n')
            serial.flushInput()
        file = open(filename, "a+")
        file.write(f"{datetime.date.today()}  {datetime.datetime.now().strftime('%H:%M')}\n")
        file.write(f"Время, с  Масса, г   Разность масс, г   Поток, {'л/м2 час' if calculation_data['flow_dimension'] == 1 else 'м3/м2 час'}  Проницаемость, {'л/м2 час бар' if calculation_data['flow_dimension'] == 1 else 'м3/м2 час бар'}\n")
        file.close()
        last_reading = 0
        time_elapsed = layout.time_elapsed.get()
        while not getattr(thread, "stop_thread", False) and (runtime is None or time_elapsed <= runtime):
            start = time.time()
            layout.time_elapsed.set(time_elapsed)
            if time_elapsed % period == 0:
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
            time_elapsed += 1
            elapsed = time.time() - start
            time.sleep(1. - min(1., elapsed))
        time.sleep(1.)

        file = open(filename, "a+")
        file.write('\n')
        file.close()
        if logging:
            self.log_file.write('\n[LOG END]\n')
            self.log_file.close()
        layout.stop()

    def get_reading(self, serial, logging=False):
        buffer = serial.read(serial.in_waiting).decode()
        reading = serial.readline().decode()
        if not buffer.endswith('\n'):
            if '\n' in buffer:
                split_buffer = buffer.split('\n')
                last_string = split_buffer[-1]
                buffer = split_buffer[:-1]
            else:
                last_string = buffer
                buffer = ''
            reading = last_string+reading
        reading = reading or f'-  0.00  g  \r\n'
        if logging:
            self.write_log(data=buffer+reading)
        try:
            reading = float(reading.lstrip('+').lstrip('-').lstrip(' ').rstrip('\r\n').rstrip(' ').rstrip('g').rstrip('!').strip(' '))
        except ValueError:
            reading = None
        return reading

    def validate_reading(self, reading, last_reading, calculation_data):
        diff = reading - last_reading if not self.interpolation_data else reading-self.interpolation_data['reading']
        if diff < 0 and abs(diff / last_reading) * 100 > calculation_data['percent']:
            return False
        return True

    def handle(self, layout, now, reading, calculation_data, last_reading=None, digits_after_dec=2):
        file = open(self.filename, "a+")
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
            file.write(
                f"{self.interpolation_data['time']}  {inter_mass:.{digits_after_dec}f}  {inter_diff:.{digits_after_dec}f}  {inter_flow:.{digits_after_dec}f}  {inter_perm:.{digits_after_dec}f}  \r")
            file.flush()
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
        file.write(f"{now}  {mass:.{digits_after_dec}f}  {mass_difference:.{digits_after_dec}f}  {flow:.{digits_after_dec}f}  {permeability:.{digits_after_dec}f}  \r")
        file.close()
        layout.entries_made.set(layout.entries_made.get() + 1)

    def calculate(self, reading, calculation_data, last_reading=0.0, interpolate=False, prev_diff=None, next_diff=None):
        if interpolate:
            mass_difference = (prev_diff + next_diff) / 2
        else:
            mass_difference = reading - last_reading if last_reading else 0
        volume = (mass_difference / 1000 / calculation_data['density']) / calculation_data['interval']
        flow = volume * 3600 / calculation_data['surface'] * 1000
        flow = flow/calculation_data['flow_dimension']
        permeability = flow / calculation_data['difference']
        return reading, mass_difference, volume, flow, permeability

    def write_log(self, data):
        self.log_file.write(data)
        self.log_file.flush()
