import time
from threading import current_thread


def read_data(serial, filename, period=1):
    """
    writes data read from serial port to given file.
    assumes that this method won't be called with filename = None

    :param serial:
    :param filename:
    :param period:
    :return:
    """
    thread = current_thread()
    file = open(filename, "a+")
    now = 0
    while not getattr(thread, "stop_thread", False):
        file.writelines(str(now) + ' - data\n')
        file.flush()
        now += period
        time.sleep(period)
    if getattr(thread, "stop_thread", False):
        file.write('\n')
        file.close()
