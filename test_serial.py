import serial
import time

try:
    ser = serial.Serial("COM5", 115200, timeout=1)
    time.sleep(2)  # allow ESP32 to reset
    print("✅ Connected to COM5\n")

    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            print(line)

except Exception as e:
    print("❌ Error:", e)