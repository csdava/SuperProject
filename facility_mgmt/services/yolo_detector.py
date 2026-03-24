"""
YOLO 设施检测服务
使用 YOLO v8.4.24 进行设施检测
"""
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# 添加 yolo26 到路径（延迟导入）
YOLO26_PATH = Path(__file__).resolve().parent.parent.parent.parent / 'yolo26'
sys.path.insert(0, str(YOLO26_PATH))

# YOLO 会在首次使用时延迟导入


# 设施类别映射
CLASS_NAMES = [
    'public_seat',       # 公共座椅
    'lighting',          # 照明灯
    'electricity_meter', # 电表
    'water_meter',       # 水表
    'street_light',      # 路灯
    'speed_bump',        # 减速带
]

CLASS_DISPLAY_NAMES = {
    'public_seat': '公共座椅',
    'lighting': '照明灯',
    'electricity_meter': '电表',
    'water_meter': '水表',
    'street_light': '路灯',
    'speed_bump': '减速带',
}


class YOLOFacilityDetector:
    """YOLO 设施检测器"""

    def __init__(self, model_path: Optional[str] = None):
        """
        初始化检测器

        Args:
            model_path: 模型文件路径，如果为 None 则使用预训练 nano 模型
        """
        # 延迟导入 YOLO，避免在模块加载时失败
        from ultralytics import YOLO

        if model_path is None:
            yolo26_dir = Path(__file__).resolve().parent.parent.parent.parent / 'yolo26'
            model_path = str(yolo26_dir / 'yolo26n.pt')

        self.model = YOLO(model_path)
        self.class_names = CLASS_NAMES
        self.class_display_names = CLASS_DISPLAY_NAMES

    def detect(self, image_path: str, conf_threshold: float = 0.25) -> List[Dict[str, Any]]:
        """
        对单张图片进行检测

        Args:
            image_path: 图片路径
            conf_threshold: 置信度阈值

        Returns:
            检测结果列表，每个元素包含:
            - bbox: 归一化边界框 [x1, y1, x2, y2]
            - confidence: 检测置信度
            - class_id: 类别ID
            - class_name: 类别名称
            - class_display: 显示名称
        """
        results = self.model.predict(
            source=image_path,
            conf=conf_threshold,
            verbose=False,
            save=False,
        )

        detections = []
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None and len(result.boxes) > 0:
                # 获取原始图片尺寸
                h, w = result.orig_shape

                for box in result.boxes:
                    xyxy = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])

                    # 获取类别名称
                    class_name = self.class_names[cls_id] if cls_id < len(self.class_names) else f'class_{cls_id}'
                    class_display = self.class_display_names.get(class_name, class_name)

                    detections.append({
                        'bbox': [
                            float(xyxy[0] / w),  # x1
                            float(xyxy[1] / h),  # y1
                            float(xyxy[2] / w),  # x2
                            float(xyxy[3] / h),  # y2
                        ],
                        'confidence': conf,
                        'class_id': cls_id,
                        'class_name': class_name,
                        'class_display': class_display,
                    })

        return detections

    def detect_from_array(self, image_array: Any, conf_threshold: float = 0.25) -> List[Dict[str, Any]]:
        """
        对 numpy 数组图片进行检测

        Args:
            image_array: numpy 数组格式的图片 (H, W, C)
            conf_threshold: 置信度阈值

        Returns:
            检测结果列表
        """
        results = self.model.predict(
            source=image_array,
            conf=conf_threshold,
            verbose=False,
            save=False,
        )

        detections = []
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None and len(result.boxes) > 0:
                h, w = result.orig_shape

                for box in result.boxes:
                    xyxy = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])

                    class_name = self.class_names[cls_id] if cls_id < len(self.class_names) else f'class_{cls_id}'
                    class_display = self.class_display_names.get(class_name, class_name)

                    detections.append({
                        'bbox': [
                            float(xyxy[0] / w),
                            float(xyxy[1] / h),
                            float(xyxy[2] / w),
                            float(xyxy[3] / h),
                        ],
                        'confidence': conf,
                        'class_id': cls_id,
                        'class_name': class_name,
                        'class_display': class_display,
                    })

        return detections

    def get_class_id(self, class_name: str) -> int:
        """获取类别ID"""
        try:
            return self.class_names.index(class_name)
        except ValueError:
            return -1


# 全局单例检测器实例
_detector_instance: Optional[YOLOFacilityDetector] = None


def get_detector(model_path: Optional[str] = None) -> YOLOFacilityDetector:
    """获取检测器单例"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = YOLOFacilityDetector(model_path)
    return _detector_instance


def reload_detector(model_path: Optional[str] = None) -> YOLOFacilityDetector:
    """重新加载检测器"""
    global _detector_instance
    _detector_instance = YOLOFacilityDetector(model_path)
    return _detector_instance
