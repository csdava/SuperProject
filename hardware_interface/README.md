# 硬件接口模块（预留）

本目录为智慧社区**硬件设备对接**预留接口，后续可扩展：

- **门禁**：人脸识别、单元门远程开门
- **道闸**：车牌识别、抬杆落杆
- **传感器**：温湿度、烟感、水浸、井盖等
- **监控**：摄像头流、告警联动
- **其他**：消防、照明、能耗采集等

## 使用方式

1. 在 `adapters/` 下新增具体设备适配器，继承 `hardware_interface.base.BaseHardwareAdapter`。
2. 在 `schemas/` 下定义设备数据/指令结构。
3. 在 Django 视图或异步任务中调用适配器，避免在请求中阻塞。

## 示例（伪代码）

```python
from hardware_interface.base import BaseHardwareAdapter

class DoorAccessAdapter(BaseHardwareAdapter):
    device_type = "door_access"
    def connect(self, **config): ...
    def disconnect(self): ...
    def is_healthy(self): ...
    def write(self, action="open", **kwargs): ...
```
