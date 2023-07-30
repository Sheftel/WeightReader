import os
import time
from threading import current_thread, Thread

from utils import raise_error


def read_data(layout, serial, calculation_data, filename, period=1, runtime=None):
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
            reading = get_reading(serial)
            Thread(target=write,
                   args=(file, layout, time_elapsed, reading,  calculation_data, last_reading)).start()
            last_reading = reading
        time_elapsed += 1
        elapsed = time.time() - start
        time.sleep(1. - elapsed)
    file.write('\n')
    file.close()
    layout.stop()


def get_reading(serial):
    serial.flushInput()
    reading = serial.readline().decode() or f'0.00  g'
    reading = float(reading.lstrip('-').lstrip(' ').rstrip('\r\n').rstrip('g').strip(' '))
    return reading


def write(file, layout, now, reading, calculation_data,  last_reading=0):
    mass, mass_difference, permeability = calculate(reading, calculation_data, last_reading=last_reading)
    file.write(f"{now}  {mass:.2f}  g  {mass_difference:.2f}  {permeability:.1f}  \r")
    layout.entries_made.set(layout.entries_made.get() + 1)
    file.flush()


def calculate(reading, calculation_data, last_reading=0.0):
    mass_difference = reading - last_reading if reading > last_reading else last_reading
    volume = (mass_difference/1000/calculation_data['density'])/calculation_data['interval']
    flow = volume * 3600/calculation_data['surface']*1000
    permeability = flow/calculation_data['difference']
    return reading, mass_difference, permeability

