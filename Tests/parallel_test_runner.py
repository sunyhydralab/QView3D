import os
import re
import subprocess
import threading
import platform

from server.Classes.Ports import Ports

red = '\033[31m'
green = '\033[32m'
yellow = '\033[33m'
blue = '\033[34m'
magenta = '\033[35m'
cyan = '\033[36m'
reset = '\033[0m'
PORTS = []
# List of available ports for testing
if platform.system() == "Windows":
    import winreg
    path = "HARDWARE\\DEVICEMAP\\SERIALCOMM"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
        for i in range(256):
            try:
                val = winreg.EnumValue(key, i)
                if re.match(r"COM\d+|LPT\d+", val[1]):
                    PORTS.append(val[1])
            except OSError:
                break
    except FileNotFoundError:
        pass

elif platform.system() == "Darwin":
    import glob
    PORTS = glob.glob("/dev/tty.*")
else:
    import glob
    PORTS = glob.glob("/dev/tty[A-Za-z]*")

def printColor(color, message):
    print(color + message + reset)

# Function to run pytest for a specific port
def run_tests_for_port(comm_port):
    env = os.environ.copy()
    verbosity = 1
    env["PORT"] = comm_port
    showAnything = False
    verbosityCommand = "-p no:terminal" if not showAnything else "-vvv"
    subprocess.Popen(["pytest", "test_runner.py", verbosityCommand, f"--myVerbose={verbosity}"], env=env).wait()

# Create and start a thread for each port
threads = []
for port in PORTS:
    if Ports.getPortByName(port) is None:
        continue
    thread = threading.Thread(target=run_tests_for_port, args=(port,))
    thread.start()
    threads.append(thread)

# Wait for all threads to complete
for thread in threads:
    thread.join()
