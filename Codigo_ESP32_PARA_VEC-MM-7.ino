#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <EmonLib.h>

// === Constantes de Configuração ===
const int LED_PIN = 2;
const char* WIFI_SSID = "MGU98";
const char* WIFI_PASS = "870104431";
const char* SERVER_URL = "http://192.168.207.148:4242";

const int SAMPLE_RATE = 200;
const int NUM_SAMPLES = 200;
const int I2C_SDA = 21, I2C_SCL = 22;
const int SCT013_PIN = 35;

// === Instâncias de Objetos Globais ===
Adafruit_MPU6050 mpu;
HTTPClient http;
LiquidCrystal_I2C lcd(0x27, 16, 2);
EnergyMonitor emon1;

// === Funções Auxiliares ===
void blinkLED(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(delayMs);
    digitalWrite(LED_PIN, LOW);
    delay(delayMs);
  }
}

void connectToWiFi() {
  Serial.print("Connecting to WiFi");
  lcd.clear();
  lcd.print("Conectando ao");
  lcd.setCursor(0, 1);
  lcd.print("WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    blinkLED(1, 500);
    Serial.print(".");
  }
  blinkLED(5, 50);
  Serial.printf("\nConnected! IP: %s\n", WiFi.localIP().toString().c_str());
}

bool checkServerReady() {
  http.begin(SERVER_URL);
  int httpCode = http.GET();
  bool ready = (httpCode == HTTP_CODE_OK && http.getString() == "1");
  http.end();
  return ready;
}

void sendData(JsonDocument& json) {
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  String jsonString;
  serializeJson(json, jsonString);
  int httpCode = http.POST(jsonString);
  if (httpCode <= 0) Serial.println("Error sending data");
  http.end();
}

// === Setup Inicial ===
void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  pinMode(SCT013_PIN, INPUT);

  lcd.init();
  lcd.backlight();
  lcd.print("Iniciando...");

  Wire.begin(I2C_SDA, I2C_SCL);
  if (!mpu.begin()) {
    Serial.println("MPU6050 not found!");
    lcd.clear();
    lcd.print("MPU6050 nao");
    lcd.setCursor(0, 1);
    lcd.print("encontrado!");
    while (1) blinkLED(3, 200);
  }

  blinkLED(2, 100);

  mpu.setAccelerometerRange(MPU6050_RANGE_16_G);
  mpu.setFilterBandwidth(MPU6050_BAND_10_HZ);

  connectToWiFi();

  lcd.clear();
  lcd.print("Bem-vindo!");
  lcd.setCursor(0, 1);
  lcd.print("Scan QR Code");
  delay(3000);

  lcd.clear();
  lcd.print("VEC-MM-7 em");
  lcd.setCursor(0, 1);
  lcd.print("operacao...");

  emon1.current(SCT013_PIN, 5.06);
}

// === Loop Principal ===
void loop() {
  if (!checkServerReady()) {
    delay(100);
    return;
  }

  DynamicJsonDocument json(3 * JSON_ARRAY_SIZE(NUM_SAMPLES) + JSON_OBJECT_SIZE(4));
  JsonArray x_data = json.createNestedArray("x");
  JsonArray y_data = json.createNestedArray("y");
  JsonArray z_data = json.createNestedArray("z");
  JsonArray current_data = json.createNestedArray("current");

  unsigned long startTime = millis();
  int samples = 0;

  while (samples < NUM_SAMPLES) {
    if (millis() - startTime >= (samples * (1000 / SAMPLE_RATE))) {
      sensors_event_t accel, gyro, temp;
      mpu.getEvent(&accel, &gyro, &temp);

      x_data.add(accel.acceleration.x);
      y_data.add(accel.acceleration.y);
      z_data.add(accel.acceleration.z);

      double current = emon1.calcIrms(1500);
      current_data.add(current);

      if (samples % 50 == 0) {
        Serial.printf("Sample %d: X:%.2f Y:%.2f Z:%.2f Current: %.2f A\n",
                      samples, accel.acceleration.x,
                      accel.acceleration.y, accel.acceleration.z, current);
      }

      samples++;
    }
  }

  digitalWrite(LED_PIN, HIGH);
  sendData(json);
  digitalWrite(LED_PIN, LOW);
  delay(10);
}

