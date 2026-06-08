import os

try:
    from secrets_local import OPENWEATHER_API_KEY as API_KEY
except ImportError:
    API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

SERIAL_PORT = os.getenv("SERIAL_PORT", "COM5")
SERIAL_BAUD = int(os.getenv("SERIAL_BAUD", "115200"))
REFRESH_RATE = int(os.getenv("REFRESH_RATE", "2"))
DB_FILE = os.getenv("DB_FILE", "atlas.db")
CITY = os.getenv("CITY", "Patiala")

# Safety thresholds
MAX_TEMP = 60
MIN_TEMP = -10