import serial
import threading
import time

import config

class SerialManager:
    def __init__(self, callback):
        self.callback = callback
        self.ser = None
        self.running = False

    def connect(self):
        self.ser = serial.Serial(config.SERIAL_PORT, config.SERIAL_BAUD, timeout=1)
        time.sleep(2)
        print(f"[SERIAL] Connected to {config.SERIAL_PORT}")

    def start(self):
        self.connect()
        self.running = True
        threading.Thread(target=self.read_loop, daemon=True).start()

    def read_loop(self):
        while self.running:
            try:
                line = self.ser.readline().decode(errors="ignore").strip()
                if line.startswith("DATA:"):
                    self.callback(line[5:])
            except Exception as e:
                print("[SERIAL ERROR]", e)
                time.sleep(1)