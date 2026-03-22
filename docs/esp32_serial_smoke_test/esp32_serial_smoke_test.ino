/**
 * ESP32 串口冒烟测试
 * - 上传到 ESP32
 * - Arduino IDE 打开 Serial Monitor：波特率 115200
 * - 应每秒看到一行：ESP32 OK
 *
 * 如果看不到，说明：
 * - 串口没有在发数据（代码没烧录/板子不对/USB供电问题）
 * - 或者你看到的 COMx 与这块板不一致
 */

#include <Arduino.h>

void setup() {
  Serial.begin(115200);
  delay(500);
}

void loop() {
  Serial.println("ESP32 OK");
  delay(1000);
}

