from usbmonitor import USBMonitor
from usbmonitor.attributes import ID_MODEL, ID_MODEL_ID, ID_VENDOR_ID, ID_SERIAL
import signal
import platform

OS_VERSION = platform.system()

device_info_str = lambda device_info: f"{device_info[ID_MODEL]} (USB PID:VID={device_info[ID_MODEL_ID]}:{device_info[ID_VENDOR_ID]} SER={device_info[ID_SERIAL]})"
# Define the `on_connect` and `on_disconnect` callbacks
# TODO: use these function to update the device list and the front end
def on_connect(device_id, device_info):
    if "USB Serial Device" in device_info[ID_MODEL]:
        print(f"Connected: {device_info_str(device_info=device_info)}")
        # TODO: add device to the fabricator list, and update the front end

def on_disconnect(device_id, device_info):
    if "USB Serial Device" in device_info[ID_MODEL]:
        print(f"Disconnected: {device_info_str(device_info=device_info)}")
        # TODO: if in the fab list, remove device, clear queues, etc, and update the front end. if in middle of job, cause toast error

# Create the USBMonitor instance
monitor = USBMonitor()

def stop_monitoring(signum, frame):
    monitor.stop_monitoring()
    print("Monitoring stopped")

def setup_monitoring():
    # Start the daemon
    monitor.start_monitoring(on_connect=on_connect, on_disconnect=on_disconnect)
    print("Monitoring started")
    # setup signal handlers
    ### WINDOWS ###
    if OS_VERSION == "Windows":
        signal.signal(signal.SIGBREAK, stop_monitoring) # Handle break command
    ### LINUX ###
    elif OS_VERSION == "Linux":
        pass
    ### MAC ###
    elif OS_VERSION == "Darwin":
        pass
    ### OTHER ###
    else:
        print(f"USB monitoring not supported on this OS: {OS_VERSION}")
    ### COMMON ###
    signal.signal(signal.SIGINT, stop_monitoring)   # Handle Ctrl+C
    signal.signal(signal.SIGTERM, stop_monitoring)  # Handle kill command
