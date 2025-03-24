from usbmonitor import USBMonitor
from usbmonitor.attributes import ID_MODEL, ID_MODEL_ID, ID_VENDOR_ID, ID_SERIAL

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

def stop_monitoring():
    monitor.stop_monitoring()

def setup_monitoring():
    # Start the daemon
    monitor.start_monitoring(on_connect=on_connect, on_disconnect=on_disconnect)
    print("Monitoring started")