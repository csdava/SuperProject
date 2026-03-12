# 硬件接口预留模块
# 用于后续对接：门禁、道闸、传感器、监控、人脸/车牌识别等设备
# 使用方式：from hardware_interface import adapters, schemas

from hardware_interface.base import BaseHardwareAdapter

__all__ = ["BaseHardwareAdapter"]
