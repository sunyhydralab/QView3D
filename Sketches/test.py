# print("Hello")
import serial
import time

# Connect to the right port.  See listing below
try:
    ser = serial.Serial('/dev/ttyS0', 115200, timeout=10)
    time.sleep(2)
    ser.write(b'M73 P0')
    ser.write(b'G162 X Y F3000')
    ser.write(b'G161 Z F1200')
    ser.write(b'G28\n')
    response = ser.readline().decode().strip()
    print("Printer says:", response)
    ser.close()
except Exception as e:
    print("Error: ", e)
    exit()

# time.sleep(2)

# #Send G-Code test
# #Return home
# ser.write(b'G28\n')
# time.sleep(5)

# ser.write(b'G21\n')

# ser.write(b'G1 F3000\n')

# ser.write(b'G1 X100 Y100\n')

# ser.close()

# print("Done")