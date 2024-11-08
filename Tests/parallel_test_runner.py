import re
import subprocess
import threading
import platform

from server.Classes.Ports import Ports

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

# Function to run pytest for a specific port
testLevel = 10
verbosity = 2
showAnything = False
verbosityCommand = "-p no:terminal" if not showAnything else "-vvv"
def run_tests_for_port(comm_port):
    subprocess.Popen(["pytest", "test_runner.py", verbosityCommand, f"--myVerbose={verbosity}", f"--port={comm_port}"]).wait()

if __name__ == "__main__":
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