import os
import re
import subprocess
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
runFlags = 0b000 # 0b001: -s, 0b010: -vvv or -p no:terminal, 0b100: debug or info

def run_tests_for_port(comm_port):
    env = os.environ.copy()
    env["PORT"] = comm_port
    args = ["pytest", ".", f"--myVerbose={verbosity}", f"--port={comm_port}"]
    if runFlags & 0b1: args.append("-s")
    args.append("-vvv") if runFlags & 0b10 else args.append("-p no:terminal")
    env["LEVEL"] = "DEBUG" if runFlags & 0b100 else "INFO"
    subprocess.Popen(args, env=env).wait()

if __name__ == "__main__":
    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=len(PORTS)) as executor:
        futures = [executor.submit(run_tests_for_port, port) for port in PORTS if Ports.getPortByName(port) is not None]
        for future in as_completed(futures):
            future.result()