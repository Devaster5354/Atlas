# Atlas

Atlas is a mini weather station + digital twin project built with an Arduino/IoT sensor setup and a Python Streamlit dashboard.

## Features
- Reads local sensor values from the Arduino side
- Fetches external weather data from OpenWeatherMap
- Visualizes live trends and environmental insights in Streamlit
- Stores recent readings in SQLite

## Hardware
- Arduino/ESP-based microcontroller
- BMP280/BME280-style pressure/temperature sensor
- MQ135-style air quality sensor
- Optional OLED display for local status output

## Python setup
1. Create a virtual environment
   - python -m venv .venv
   - .\.venv\Scripts\activate
2. Install dependencies
   - pip install -r requirements.txt
3. Copy the example environment file and update values
   - copy .env.example .env
4. Run the dashboard
   - streamlit run app.py

## Environment variables
- SERIAL_PORT
- SERIAL_BAUD
- OPENWEATHER_API_KEY
- CITY
- DB_FILE

## Important
- Do not upload the local secret files `secrets_local.py` or `secrets_local.h`.
- Keep those files only on your machine and copy the values into them when you run the project locally.

## Notes
- The current project keeps its original logic and behavior while adding safer configuration support for GitHub upload and local use.
