import os
from werkzeug.local import LocalProxy
from Classes.EventEmitter import EventEmitter
import gzip
import shutil
from enum import Enum
import platform

# Global variables
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
uploads_folder = os.path.abspath(os.path.join(root_path, 'uploads'))
system_device_prefix = "COM" if platform.system() == "Windows" else ""
emulator_connections = {}
event_emitter = EventEmitter()

def _find_custom_app():
    from flask import current_app as flask_current_app
    from MyFlaskApp import MyFlaskApp
    app = flask_current_app._get_current_object()
    return app if isinstance(app, MyFlaskApp) else None

current_app = LocalProxy(_find_custom_app)

def compress_with_gzip(log_file_path):
    """
    Compresses a log file using gzip compression.

    Parameters:
        log_file_path (str): Path to the input log file.

    Returns:
        str: Path to the compressed file if successful.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input path is a directory or invalid.
        IOError: For any I/O operation errors.
    """
    # Validate the input path
    if not os.path.isfile(log_file_path):
        raise ValueError(f"The specified path '{log_file_path}' is not a valid file.")

    compressed_file_path = log_file_path + '.gz'

    try:
        # Compress the file
        with open(log_file_path, 'rb') as f_in, gzip.open(compressed_file_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        return compressed_file_path

    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{log_file_path}' does not exist.")
    except IOError as e:
        raise IOError(f"An error occurred while compressing the file: {e}")

def tabs(tab_change: int = 0):
    global tab_num
    if 'tab_num' not in globals():
        tab_num = 0
    tab_num += tab_change
    return "\t" * tab_num

class VID(int, Enum):
    PRUSA    = 0x2C99
    CREALITY = 0x1A86
    MAKERBOT = 0x23C1

class PID(int, Enum):
    MK3         = 0x0002
    MK4         = 0x000D
    MK4S        = 0x001A
    ENDER3      = 0x7523
    REPLICATOR2 = 0xB016