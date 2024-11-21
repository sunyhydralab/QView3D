import os
import sys
import re
import subprocess
import platform

# Add test root to sys.path if needed
rootpath=os.path.abspath(os.path.join(os.path.dirname(__file__).split("QView3D")[0], 'QView3D'))
if rootpath not in sys.path:
    sys.path.append(rootpath)
serverpath = os.path.join(rootpath, "server")
if serverpath not in sys.path:
    sys.path.append(serverpath)
testpath = os.path.join(rootpath, "Tests")
if testpath not in sys.path:
    sys.path.append(testpath)

from server.Classes.Ports import Ports
from app import app

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
testLevel = 0
verbosity = 2
runFlags = 0b010 # 0b001: -s, 0b010: -vvv or -p no:terminal, 0b100: debug or info

def run_tests_for_port(comm_port):
    env = os.environ.copy()
    env["PORT"] = comm_port
    args = ["pytest", testpath, f"--myVerbose={verbosity}", f"--port={comm_port}"]
    if runFlags & 0b1: args.append("-s")
    args.append("-vv") if runFlags & 0b10 else args.append("-p no:terminal")
    env["LEVEL"] = "DEBUG" if runFlags & 0b100 else "INFO"
    subprocess.Popen(args, env=env).wait()

if __name__ == "__main__":
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with app.app_context():
        if len(PORTS) != 0:
            with ThreadPoolExecutor(max_workers=len(PORTS)) as executor:
                futures = [executor.submit(run_tests_for_port, port) for port in PORTS if Ports.getPortByName(port) is not None]
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        from app import handle_errors_and_logging
                        handle_errors_and_logging(e)