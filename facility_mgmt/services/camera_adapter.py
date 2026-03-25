"""
摄像头适配器服务
支持 RTSP 流、HTTP API、USB 摄像头和文件路径
"""
from typing import Optional, Iterator, Tuple, Union
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class CameraAdapter:
    """
    摄像头适配器

    支持:
    - RTSP 流 (rtsp://)
    - HTTP API (http://)
    - USB 摄像头 (usb://0 或直接写摄像头索引如 0)
    - 文件路径
    """

    def __init__(self, url: Union[str, int], camera_type: str = 'auto'):
        """
        初始化摄像头适配器

        Args:
            url: 摄像头地址/索引
                - RTSP: 'rtsp://user:pass@ip:port/path'
                - HTTP: 'http://ip:port/mjpeg'
                - USB: 0, 1, 2... (摄像头索引) 或 'usb://0'
                - 文件: '/path/to/video.mp4'
            camera_type: 'rtsp', 'http', 'usb', 'file', 'auto'
        """
        self.url = str(url)
        self.camera_index: Optional[int] = None
        if camera_type == 'auto':
            self.camera_type = self._detect_camera_type(self.url)
        else:
            self.camera_type = camera_type
            # 如果显式指定为 usb，解析索引
            if self.camera_type == 'usb' or camera_type == 'usb':
                if url.isdigit():
                    self.camera_index = int(url)
                elif url.startswith('usb://'):
                    try:
                        self.camera_index = int(url.replace('usb://', ''))
                    except ValueError:
                        pass
        self._cap = None
        self._is_connected = False

    def _detect_camera_type(self, url: str) -> str:
        """自动检测摄像头类型"""
        # USB 摄像头检测 (数字索引或 usb:// 前缀)
        if url.isdigit():
            self.camera_index = int(url)
            return 'usb'
        elif url.startswith('usb://'):
            try:
                self.camera_index = int(url.replace('usb://', ''))
                return 'usb'
            except ValueError:
                return 'http'

        parsed = urlparse(url)
        if parsed.scheme == 'rtsp':
            return 'rtsp'
        elif parsed.scheme == 'http':
            return 'http'
        elif parsed.scheme == 'file' or '.' in url:
            return 'file'
        return 'http'

    def connect(self) -> bool:
        """
        连接到摄像头

        Returns:
            连接是否成功
        """
        # 延迟导入
        import cv2

        try:
            if self.camera_type == 'usb':
                # USB 摄像头使用索引
                self._cap = cv2.VideoCapture(self.camera_index)
                self._is_connected = self._cap.isOpened()
            elif self.camera_type == 'rtsp':
                self._cap = cv2.VideoCapture(self.url)
                self._is_connected = self._cap.isOpened()
            elif self.camera_type == 'http':
                # HTTP 摄像头通常返回 MJPEG 流
                self._cap = cv2.VideoCapture(self.url)
                self._is_connected = self._cap.isOpened()
            elif self.camera_type == 'file':
                self._cap = cv2.VideoCapture(self.url)
                self._is_connected = self._cap.isOpened()
            else:
                self._is_connected = False

            if not self._is_connected:
                logger.warning(f"Failed to open camera: {self.url}")

            return self._is_connected

        except Exception as e:
            logger.error(f"Camera connection error: {e}")
            self._is_connected = False
            return False

    def disconnect(self) -> None:
        """断开摄像头连接"""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._is_connected = False

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._is_connected and self._cap is not None

    def capture_frame(self):
        """
        捕获单帧图片

        Returns:
            numpy 数组格式的图片 (BGR)，失败返回 None
        """
        import cv2

        if not self.is_connected():
            if not self.connect():
                return None

        try:
            ret, frame = self._cap.read()
            if ret:
                return frame
            else:
                logger.warning("Failed to read frame from camera")
                return None
        except Exception as e:
            logger.error(f"Frame capture error: {e}")
            return None

    def capture_frames(self, count: int = 10, interval: float = 0.1):
        """
        捕获多帧图片

        Args:
            count: 捕获帧数
            interval: 帧间隔（秒）

        Returns:
            图片列表
        """
        frames = []
        for _ in range(count):
            frame = self.capture_frame()
            if frame is not None:
                frames.append(frame)
        return frames

    def stream(self):
        """
        流式获取图片帧

        Yields:
            numpy 数组格式的图片 (BGR)
        """
        import cv2

        if not self.is_connected():
            if not self.connect():
                return

        while True:
            ret, frame = self._cap.read()
            if ret:
                yield frame
            else:
                break

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


class RTSPCamera(CameraAdapter):
    """RTSP 摄像头专用适配器"""

    def __init__(self, url: str):
        super().__init__(url, 'rtsp')

    def reconnect(self, max_attempts: int = 3) -> bool:
        """
        尝试重连

        Args:
            max_attempts: 最大重试次数

        Returns:
            是否重连成功
        """
        for attempt in range(max_attempts):
            self.disconnect()
            if self.connect():
                return True
            logger.warning(f"RTSP reconnect attempt {attempt + 1} failed")
        return False


class HTTPCamera(CameraAdapter):
    """HTTP 摄像头专用适配器"""

    def __init__(self, url: str, timeout: int = 5):
        super().__init__(url, 'http')
        self.timeout = timeout

    def capture_from_api(self):
        """
        从 HTTP API 获取图片

        Returns:
            numpy 数组格式的图片
        """
        import requests
        import cv2
        import numpy as np

        try:
            response = requests.get(self.url, timeout=self.timeout)
            if response.status_code == 200:
                image_array = np.frombuffer(response.content, dtype=np.uint8)
                image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                return image
            return None
        except Exception as e:
            logger.error(f"HTTP camera capture error: {e}")
            return None


def capture_from_url(url: str, camera_type: str = 'auto'):
    """
    从 URL 捕获单帧图片的便捷函数

    Args:
        url: 摄像头地址
        camera_type: 摄像头类型

    Returns:
        numpy 数组格式的图片
    """
    with CameraAdapter(url, camera_type) as camera:
        return camera.capture_frame()


def validate_rtsp_url(url: str) -> Tuple[bool, str]:
    """
    验证 RTSP URL 格式

    Args:
        url: RTSP 地址

    Returns:
        (是否有效, 错误信息)
    """
    if not url.startswith('rtsp://'):
        return False, "URL must start with rtsp://"

    parsed = urlparse(url)
    if not parsed.netloc:
        return False, "Invalid RTSP URL format"

    return True, ""


def validate_http_url(url: str) -> Tuple[bool, str]:
    """
    验证 HTTP URL 格式

    Args:
        url: HTTP 地址

    Returns:
        (是否有效, 错误信息)
    """
    if not url.startswith('http://') and not url.startswith('https://'):
        return False, "URL must start with http:// or https://"

    parsed = urlparse(url)
    if not parsed.netloc:
        return False, "Invalid HTTP URL format"

    return True, ""
