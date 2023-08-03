import os
import time
from threading import current_thread, Thread

from utils import raise_error


class Reader:
    interpolation_data = None
    last_read = {}

    def read_data(self, layout, serial, calculation_data, filename, period=1, runtime=None):
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
        file = open(filename, "a+")
        last_reading = 0
        time_elapsed = layout.time_elapsed.get()
        while not getattr(thread, "stop_thread", False) and (runtime is None or time_elapsed <= runtime):
            start = time.time()
            layout.time_elapsed.set(time_elapsed)
            if time_elapsed % period == 0:
                reading = self.get_reading(serial)
                if self.validate_reading(reading, last_reading, calculation_data):
                    Thread(target=self.handle,
                           args=(file, layout, time_elapsed, reading, calculation_data, last_reading)).start()
                    last_reading = reading
                else:
                    self.interpolation_data = {'reading': reading,
                                               'time': time_elapsed}
            time_elapsed += 1
            elapsed = time.time() - start
            time.sleep(1. - min(1., elapsed))
        time.sleep(1.)
        file.write('\n')
        file.close()
        layout.stop()

    def get_reading(self, serial):
        serial.flushInput()
        reading = serial.readline().decode() or f'-  0.00  g  \r\n'
        reading = float(reading.lstrip('-').lstrip(' ').rstrip('\r\n').rstrip(' ').rstrip('g').strip(' '))
        return reading

    def validate_reading(self, reading, last_reading, calculation_data):
        diff = reading - last_reading
        if diff < 0 and abs(diff / last_reading) * 100 > calculation_data['percent']:
            return False
        return True

    def handle(self, file, layout, now, reading, calculation_data, last_reading=None):
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
                f"{self.interpolation_data['time']}  {inter_mass:.2f}  g  {inter_diff:.2f}  {inter_flow:.2f}  {inter_perm:.1f}  \r")
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
        file.write(f"{now}  {mass:.2f}  g  {mass_difference:.2f}  {flow:.2f}  {permeability:.1f}  \r")
        file.flush()
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
