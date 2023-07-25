import configparser
from pathlib import Path

__all__ = [
    'APP_TITLE',
    'SERIAL_PORT',
    'SERIAL_BAUDRATE',
    'SERIAL_BITESIZE',
    'SERIAL_PARITY',
    'SERIAL_STOPBITS',
    'DEFAULT_FILE_PATH',
    'DEFAULT_INTERVAL',
    'MAX_INTERVAL',
    'MIN_INTERVAL',
    'STATIC_PATH'
]

ROOT_PATH = Path(__file__).resolve(strict=True).parent
STATIC_PATH = ROOT_PATH / 'static'

config = configparser.ConfigParser()
config.read(ROOT_PATH.parent / 'config.ini')

APP_TITLE = ''

serial = config['SERIAL']
SERIAL_PORT = serial.get('SERIAL_PORT', 'COM1')
SERIAL_BAUDRATE = serial.getint('SERIAL_BAUDRATE', 9600)
SERIAL_BITESIZE = serial.getint('SERIAL_BITESIZE', 8)
SERIAL_PARITY = serial.get('SERIAL_PARITY', 'N')
SERIAL_STOPBITS = serial.getint('SERIAL_STOPBITS', 1)


output = config['OUTPUT_FILE']
DEFAULT_FILE_PATH = output.get('DEFAULT_PATH', Path.home()/'weights')

period = config['READ_PERIOD']
DEFAULT_INTERVAL = period.getint('DEFAULT_INTERVAL', 30)
MIN_INTERVAL = period.getint('MIN_INTERVAL', 1) if period.getint('MIN_INTERVAL', 1) >= 1 else 1
MAX_INTERVAL = period.getint('MAX_INTERVAL', 7200)
