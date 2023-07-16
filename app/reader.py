import os
import time
from threading import current_thread

from utils import raise_error


def read_data(layout, serial, filename, period=1):
    """
    writes data read from serial port to given file.
    assumes that this method won't be called with filename = None
    """
    thread = current_thread()
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
    except FileNotFoundError:
        raise_error(message="Ошибка в пути к файлу.")
        return layout.reset_layout()
    file = open(filename, "a+")

    now = 0
    while not getattr(thread, "stop_thread", False):
        # do some stuff
        print(now)
        file.write(str(now) + ' - data\n')
        file.flush()
        start = time.time()
        now += period
        time.sleep(period)
        stop = time.time()
        duration = stop - start
        print(duration)
    if getattr(thread, "stop_thread", False):
        file.write('\n')
        file.close()
