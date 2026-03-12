"""
硬件适配器基类 - 预留接口
后续具体设备（门禁、道闸、传感器、摄像头等）继承此类实现对接。
"""
from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseHardwareAdapter(ABC):
    """所有硬件设备适配器的抽象基类。"""

    device_type: str = "unknown"

    @abstractmethod
    def connect(self, **config: Any) -> bool:
        """建立与设备的连接。"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """断开连接。"""
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """检查设备是否在线/正常。"""
        pass

    def read(self, **kwargs: Any) -> Optional[Any]:
        """读取数据（如传感器数值）。子类按需实现。"""
        return None

    def write(self, **kwargs: Any) -> bool:
        """下发指令（如开门、抬杆）。子类按需实现。"""
        return False
