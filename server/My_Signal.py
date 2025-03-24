import signal
import platform
from typing import Callable

OS_VERSION = platform.system()


def setup_signal(func: Callable):
    # setup signal handlers
    ### WINDOWS ###
    if OS_VERSION == "Windows":
        signal.signal(signal.SIGBREAK, func)  # Handle break command
    ### LINUX ###
    elif OS_VERSION == "Linux":
        pass
    ### MAC ###
    elif OS_VERSION == "Darwin":
        pass
    ### OTHER ###
    else:
        print(f"USB monitoring not supported on this OS: {OS_VERSION}")
        return
    ### COMMON ###
    signal.signal(signal.SIGINT, func)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, func)  # Handle kill command
