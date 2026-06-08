#include <Wire.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_BMP280.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "secrets_local.h"

// ================= OLED =================
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_MOSI 23
#define OLED_CLK  14
#define OLED_DC   13
#define OLED_CS   27
#define OLED_RST  16

// ================= I2C =================
#define I2C_SDA 21
#define I2C_SCL 22

// ================= SENSOR =================
#define MQ135_PIN 33

// ================= WiFi =================
const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;

// ================= API =================
const char* openWeatherApiKey = OPENWEATHER_API_KEY;
const char* cityName = "Patiala";

// ================= OBJECTS =================
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT,
                         OLED_MOSI, OLED_CLK,
                         OLED_DC, OLED_RST, OLED_CS);

Adafruit_BMP280 bmp;

// ================= DATA =================
float localTemp = 0;
float localPressure = 0;
float altitude = 0;
int airQuality = 0;

float externalTemp = 0;
float externalHumidity = 0;
float externalPressure = 0;
int weatherCondition = 0;

// ================= TIMERS =================
unsigned long lastSensorRead = 0;
unsigned long lastAPICall = 0;
unsigned long lastAnimUpdate = 0;
unsigned long lastSerialOutput = 0;  // ADDED: Timer for serial output

int animationFrame = 0;

bool wifiConnected = false;
bool apiDataValid = false;

// ================= FUNCTIONS =================
void bootAnimation();
void connectWiFi();
void fetchWeatherData();
void parseWeatherData(String json);
void readLocalSensors();
void drawDashboard();

// ================= BOOT =================
void bootAnimation() {
  display.clearDisplay();
  display.setTextSize(2);
  display.setCursor(15, 20);
  display.print("IOT");
  display.setCursor(10, 45);
  display.print("WEATHER");
  display.display();
  delay(1500);

  display.clearDisplay();
  display.setTextSize(1);
  display.setCursor(10, 20);
  display.print("Booting...");
  display.display();
  delay(1000);
}

// ================= WIFI =================
void connectWiFi() {
  display.clearDisplay();
  display.setCursor(10, 20);
  display.print("Connecting WiFi...");
  display.display();

  WiFi.begin(ssid, password);
  int attempts = 0;

  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    display.print(".");
    display.display();
    attempts++;
  }

  display.clearDisplay();

  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    display.setCursor(10, 20);
    display.print("Connected!");
    Serial.println("WiFi Connected Successfully");  // ADDED
  } else {
    wifiConnected = false;
    display.setCursor(10, 20);
    display.print("Offline Mode");
    Serial.println("WiFi Connection Failed - Offline Mode");  // ADDED
  }

  display.display();
  delay(1500);

  // Smooth transition
  display.clearDisplay();
  display.setCursor(20, 25);
  display.print("Loading Data...");
  display.display();
  delay(1000);
}

// ================= API =================
void fetchWeatherData() {
  if (!wifiConnected) return;

  HTTPClient http;
  String url = "http://api.openweathermap.org/data/2.5/weather?q=" + String(cityName) +
               "&appid=" + String(openWeatherApiKey) + "&units=metric";

  http.begin(url);
  int code = http.GET();

  if (code == 200) {
    parseWeatherData(http.getString());
    apiDataValid = true;
    Serial.println("Weather API Data Updated");  // ADDED
  } else {
    apiDataValid = false;
    Serial.print("Weather API Failed - HTTP Code: ");  // ADDED
    Serial.println(code);  // ADDED
  }

  http.end();
}

// ================= JSON =================
void parseWeatherData(String json) {
  JsonDocument doc;
  if (!deserializeJson(doc, json)) {
    externalTemp     = doc["main"]["temp"];
    externalHumidity = doc["main"]["humidity"];
    externalPressure = doc["main"]["pressure"];

    String cond = doc["weather"][0]["main"];
    if (cond == "Clear") weatherCondition = 0;
    else if (cond == "Rain") weatherCondition = 1;
    else weatherCondition = 2;
    
    Serial.println("Weather Data Parsed Successfully");  // ADDED
  }
}

// ================= SENSORS =================
void readLocalSensors() {
  localTemp     = bmp.readTemperature();
  localPressure = bmp.readPressure() / 100.0F;
  altitude      = bmp.readAltitude(1013.25);

  // NOTE: MQ135 gives relative values (not calibrated ppm)
  const int N = 10;
  static int arr[N];
  static int idx = 0;
  static int sum = 0;

  sum -= arr[idx];
  arr[idx] = analogRead(MQ135_PIN);
  sum += arr[idx];
  idx = (idx + 1) % N;

  airQuality = sum / N;
}

// ================= UI =================
void drawDashboard() {
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);

  // Header
  display.setCursor(5, 0);
  display.print("LOCAL");

  display.setCursor(78, 0);
  display.print("ONLINE");

  display.drawLine(0, 10, 127, 10, SSD1306_WHITE);
  display.drawLine(63, 10, 63, 63, SSD1306_WHITE);

  // ----- LOCAL -----
  display.setCursor(2, 14);
  display.print("Temp:");
  display.setCursor(2, 22);
  display.print(localTemp, 1);
  display.print("C");

  display.setCursor(2, 32);
  display.print("Press:");
  display.setCursor(2, 40);
  display.print(localPressure, 0);
  display.print("hPa");

  display.setCursor(2, 50);
  display.print("Air:");

  String airStatus;
  if (airQuality < 1500) airStatus = "Clean";
  else if (airQuality < 2500) airStatus = "Mode";
  else airStatus = "Poor";

  display.setCursor(30, 50);
  display.print(airStatus);

  // ----- ONLINE -----
  display.setCursor(66, 14);
  display.print("Temp:");
  display.setCursor(66, 22);
  apiDataValid ? display.print(externalTemp, 1) : display.print("--");
  display.print("C");

  display.setCursor(66, 32);
  display.print("Hum:");
  display.setCursor(66, 40);
  apiDataValid ? display.print(externalHumidity, 0) : display.print("--");
  display.print("%");

  display.setCursor(66, 50);
  display.print("Press:");
  display.setCursor(98, 50);
  apiDataValid ? display.print(externalPressure, 0) : display.print("--");

  // ----- ICON -----
  if (apiDataValid && animationFrame % 10 < 5) {
    if (weatherCondition == 0) {
      display.drawCircle(120, 5, 3, SSD1306_WHITE);
    } else if (weatherCondition == 1) {
      display.fillCircle(120, 4, 3, SSD1306_WHITE);
      display.drawLine(118, 8, 118, 11, SSD1306_WHITE);
    } else {
      display.fillCircle(118, 5, 3, SSD1306_WHITE);
      display.fillCircle(123, 5, 3, SSD1306_WHITE);
    }
  }
}

// ================= SETUP =================
void setup() {
  Serial.begin(115200);
  Serial.println("=========================================");  // ADDED
  Serial.println("IoT Weather Station Starting...");  // ADDED
  Serial.println("=========================================");  // ADDED

  Wire.begin(I2C_SDA, I2C_SCL);

  bmp.begin(0x76) || bmp.begin(0x77);
  display.begin(SSD1306_SWITCHCAPVCC);

  bootAnimation();
  connectWiFi();

  readLocalSensors();
  if (wifiConnected) fetchWeatherData();
  
  Serial.println("System Ready - Sending Data Every 2 Seconds");  // ADDED
  Serial.println("=========================================");  // ADDED
}

// ================= LOOP =================
void loop() {
  unsigned long now = millis();

  if (now - lastSensorRead > 2000) {
    lastSensorRead = now;
    readLocalSensors();
  }

  if (wifiConnected && now - lastAPICall > 600000) {
    lastAPICall = now;
    fetchWeatherData();
  }

  // ADDED: Send data to serial monitor every 2 seconds
  if (now - lastSerialOutput > 2000) {
    lastSerialOutput = now;
    
    // Format: DATA:localTemp,localPressure,airQuality,externalTemp,externalHumidity,externalPressure,altitude,weatherCondition
    Serial.print("DATA:");
    Serial.print(localTemp); Serial.print(",");
    Serial.print(localPressure); Serial.print(",");
    Serial.print(airQuality); Serial.print(",");
    Serial.print(externalTemp); Serial.print(",");
    Serial.print(externalHumidity); Serial.print(",");
    Serial.print(externalPressure); Serial.print(",");
    Serial.print(altitude); Serial.print(",");
    Serial.print(weatherCondition);
    Serial.println();
    
    // Also print human-readable format for monitoring
    Serial.print("  -> Local: ");
    Serial.print(localTemp); Serial.print("°C, ");
    Serial.print(localPressure); Serial.print("hPa, ");
    Serial.print("Air: "); Serial.print(airQuality);
    
    if(apiDataValid) {
      Serial.print(" | Online: ");
      Serial.print(externalTemp); Serial.print("°C, ");
      Serial.print(externalHumidity); Serial.print("%, ");
      Serial.print(externalPressure); Serial.print("hPa");
    }
    Serial.println();
  }

  if (now - lastAnimUpdate > 100) {
    lastAnimUpdate = now;
    animationFrame++;

    display.clearDisplay();
    drawDashboard();
    display.display();
  }
}