import os
import time
from threading import current_thread

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
    now = 0
    last_reading = read_action(file, serial, layout, now, calculation_data)
    while not getattr(thread, "stop_thread", False) and (runtime is None or now < runtime):
        time.sleep(period)
        now += period
        last_reading = read_action(file, serial, layout, now, calculation_data,  last_reading)
    if getattr(thread, "stop_thread", False):
        file.write('\n')
        file.close()


def read_action(file, serial, layout, now, calculation_data,  last_reading=0):
    serial.flushInput()
    reading = serial.readline().decode() or f'0.00  g'
    reading = float(reading.rstrip('g').lstrip('-').lstrip(' ').strip(' ').rstrip('\r\n'))
    mass, mass_difference, permeability = calculate(reading, calculation_data, last_reading=last_reading)
    file.write(f"{now}  {mass:.2f}  g  {mass_difference:.2f}  {permeability:.1f}  \r")
    layout.entries_made.set(layout.entries_made.get() + 1)
    file.flush()
    return mass


def calculate(reading, calculation_data, last_reading=0.0):
    mass_difference = reading - last_reading if reading > last_reading else last_reading
    volume = (mass_difference/1000/calculation_data['density'])/calculation_data['interval']
    flow = volume * 3600/calculation_data['surface']*1000
    permeability = flow/calculation_data['difference']
    return reading, mass_difference, permeability
