/**
 * ESP32 + DHT22 串口发送温湿度（JSON一行一条）
 *
 * 上传到 ESP32 后，串口输出示例：
 * {"t":25.3,"h":60.2}
 *
 * 配套：Django 命令
 *   python manage.py esp32_temp_humidity_reader --port COM5
 */

#include <Arduino.h>
#include <DHTesp.h>

// 你的 DHT22 数据脚（DATA）连接到 ESP32 的哪个 GPIO？
// 常见接法：GPIO4。请按你的实际接线修改。
static const int DHT_PIN = 4;

static const unsigned long READ_INTERVAL_MS = 2000;

DHTesp dht;
unsigned long lastReadMs = 0;

void setup() {
  Serial.begin(115200);
  dht.setup(DHT_PIN, DHTesp::DHT22);
}

void loop() {
  unsigned long now = millis();
  if (now - lastReadMs < READ_INTERVAL_MS) {
    return;
  }
  lastReadMs = now;

  TempAndHumidity data = dht.getTempAndHumidity();

  // DHT22 在某些极端情况下可能读到 NaN，直接跳过本次输出
  if (isnan(data.temperature) || isnan(data.humidity)) {
    return;
  }

  // 一行 JSON：{ "t": 温度, "h": 湿度 }
  Serial.print("{\"t\":");
  Serial.print(data.temperature, 1);
  Serial.print(",\"h\":");
  Serial.print(data.humidity, 1);
  Serial.println("}");
}

