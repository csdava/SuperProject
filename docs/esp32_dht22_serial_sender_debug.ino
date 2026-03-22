/**
 * ESP32 + DHT22 串口调试版
 *
 * 你需要先确认串口能输出（见 esp32_serial_smoke_test.ino）。
 * 本文件用于确认 DHT22 是否读到有效温湿度：
 * - 每次读取都会输出一行调试信息
 * - 只有温湿度都不是 NaN 时，才额外输出 JSON：
 *     {"t":25.3,"h":60.2}
 *
 * 配套 Django 命令读取 JSON：
 *   python manage.py esp32_temp_humidity_reader --port COM5 --baudrate 115200
 */

#include <Arduino.h>
#include <DHTesp.h>

static const int DHT_PIN = 4; // 按你的接线：GPIO4

static const unsigned long READ_INTERVAL_MS = 2000;

DHTesp dht;
unsigned long lastReadMs = 0;

void setup() {
  Serial.begin(115200);
  dht.setup(DHT_PIN, DHTesp::DHT22);
}

void loop() {
  unsigned long now = millis();
  if (now - lastReadMs < READ_INTERVAL_MS) return;
  lastReadMs = now;

  TempAndHumidity data = dht.getTempAndHumidity();
  bool ok = !(isnan(data.temperature) || isnan(data.humidity));

  // 调试输出：不论 ok 与否都打印，方便你在 Serial Monitor 里看到 nan
  Serial.print("DHT22 DEBUG: T=");
  Serial.print(data.temperature, 1);
  Serial.print(" H=");
  Serial.println(data.humidity, 1);

  // 只有有效读数才输出 JSON（给 Django 用）
  if (!ok) return;

  Serial.print("{\"t\":");
  Serial.print(data.temperature, 1);
  Serial.print(",\"h\":");
  Serial.print(data.humidity, 1);
  Serial.println("}");
}

