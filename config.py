from pathlib import Path


__all__ = [
    'APP_TITLE',
    'SERIAL_PORT',
    'SERIAL_BAUDRATE',
    'SERIAL_BITESIZE',
    'SERIAL_PARITY',
    'SERIAL_STOPBITS',
    'DEFAULT_FILE_PATH'
]

APP_TITLE = 'WeightReader'

SERIAL_PORT = 'COM1'
SERIAL_BAUDRATE = 9600
SERIAL_BITESIZE = 8
SERIAL_PARITY = 'N'
SERIAL_STOPBITS = 1


ROOT_PATH = Path(__file__).resolve(strict=True).parent
DEFAULT_FILE_PATH = ROOT_PATH / 'static/output'
print(DEFAULT_FILE_PATH)
