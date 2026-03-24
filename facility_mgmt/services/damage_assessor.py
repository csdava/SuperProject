"""
损坏评估服务
基于规则的设施损坏评估和寿命预测
"""
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass

# 各类设施的基础寿命（天）
BASE_LIFESPAN_DAYS = {
    'public_seat': 1825,      # 5年
    'lighting': 1095,         # 3年
    'electricity_meter': 3650, # 10年
    'water_meter': 2190,      # 6年
    'street_light': 1460,     # 4年
    'speed_bump': 730,        # 2年
}

# 损坏等级定义
DAMAGE_LEVELS = ['normal', 'minor', 'moderate', 'severe']

# 各类别的典型损坏原因
DAMAGE_REASONS_BY_CATEGORY = {
    'public_seat': ['生锈', '表面破损', '结构松动', '缺失零件', '严重变形'],
    'lighting': ['灯罩破损', '灯泡熄灭', '支架锈蚀', '线路裸露', '严重倾斜'],
    'electricity_meter': ['表盘模糊', '指针异常', '外壳破损', '安装松动', '读数异常'],
    'water_meter': ['表盘模糊', '指针异常', '外壳锈蚀', '漏水', '读数异常'],
    'street_light': ['灯罩破损', '灯泡损坏', '灯杆倾斜', '基础破损', '严重锈蚀'],
    'speed_bump': ['标线模糊', '破损', '移位', '缺失', '严重变形'],
}


@dataclass
class DamageAssessment:
    """损坏评估结果"""
    damage_level: str           # normal, minor, moderate, severe
    estimated_lifespan_days: int  # 预计剩余天数
    damage_reasons: List[str]     # 损坏原因列表
    confidence: float             # 评估置信度


class DamageAssessor:
    """
    基于规则的损坏评估器

    评估策略：
    1. 低检测置信度 → 可能存在异常/损坏
    2. 边界框比例异常 → 物体变形或被遮挡
    3. 类别特定规则
    """

    def __init__(self):
        self.base_lifespan = BASE_LIFESPAN_DAYS
        self.damage_reasons = DAMAGE_REASONS_BY_CATEGORY

    def assess(
        self,
        detection: Dict[str, Any],
        image_path: Optional[str] = None,
        extra_features: Optional[Dict] = None
    ) -> DamageAssessment:
        """
        评估单个检测结果的损坏程度

        Args:
            detection: YOLO 检测结果，包含 bbox, confidence, class_name 等
            image_path: 图片路径（可选，用于高级分析）
            extra_features: 额外特征（可选）

        Returns:
            DamageAssessment 评估结果
        """
        confidence = detection.get('confidence', 1.0)
        class_name = detection.get('class_name', '')
        bbox = detection.get('bbox', [0, 0, 1, 1])

        damage_reasons = []
        lifespan_deduction = 0

        # 1. 基于置信度的评估
        if confidence < 0.3:
            lifespan_deduction += 180  # 严重损坏风险
            damage_reasons.append('检测置信度极低，可能存在严重异常')
        elif confidence < 0.5:
            lifespan_deduction += 90
            damage_reasons.append('检测置信度偏低，可能存在损坏或形变')
        elif confidence < 0.7:
            lifespan_deduction += 30
            damage_reasons.append('检测置信度一般，建议现场检查')

        # 2. 基于边界框比例的评估
        bbox_ratio = self._calculate_bbox_ratio(bbox)
        if bbox_ratio < 0.3 or bbox_ratio > 3.0:
            lifespan_deduction += 60
            damage_reasons.append('目标比例异常，可能存在形变或部分遮挡')

        # 3. 边界框面积评估（小面积可能是远处或小的目标）
        bbox_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        if bbox_area < 0.01:  # 小于图片 1%
            lifespan_deduction += 30
            damage_reasons.append('目标过小，可能需要近距离检查')

        # 4. 类别特定的额外规则（如果有）
        if extra_features:
            class_reasons = self._assess_category_specific(class_name, extra_features)
            damage_reasons.extend(class_reasons)
            lifespan_deduction += len(class_reasons) * 30

        # 计算最终寿命
        base_life = self.base_lifespan.get(class_name, 1095)  # 默认3年
        estimated_lifespan = max(0, base_life - lifespan_deduction)

        # 确定损坏等级
        if len(damage_reasons) == 0:
            damage_level = 'normal'
            assessment_confidence = 0.9
        elif len(damage_reasons) == 1:
            damage_level = 'minor'
            assessment_confidence = 0.7
        elif len(damage_reasons) == 2:
            damage_level = 'moderate'
            assessment_confidence = 0.6
        else:
            damage_level = 'severe'
            assessment_confidence = 0.5

        return DamageAssessment(
            damage_level=damage_level,
            estimated_lifespan_days=estimated_lifespan,
            damage_reasons=damage_reasons,
            confidence=assessment_confidence
        )

    def _calculate_bbox_ratio(self, bbox: List[float]) -> float:
        """计算边界框宽高比"""
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        if height == 0:
            return 0
        return width / height

    def _assess_category_specific(
        self,
        class_name: str,
        extra_features: Dict
    ) -> List[str]:
        """
        类别特定的损坏评估

        Args:
            class_name: 设施类别
            extra_features: 额外特征

        Returns:
            损坏原因列表
        """
        reasons = []

        # 当有额外特征时可以扩展此处
        # 例如：颜色分析、纹理分析等

        return reasons

    def batch_assess(
        self,
        detections: List[Dict[str, Any]]
    ) -> List[DamageAssessment]:
        """
        批量评估

        Args:
            detections: 检测结果列表

        Returns:
            评估结果列表
        """
        return [self.assess(d) for d in detections]


def assess_damage(detection: Dict[str, Any]) -> Tuple[str, int, List[str]]:
    """
    便捷函数：评估单个检测结果的损坏程度

    Returns:
        (damage_level, estimated_lifespan_days, damage_reasons)
    """
    assessor = DamageAssessor()
    result = assessor.assess(detection)
    return result.damage_level, result.estimated_lifespan_days, result.damage_reasons
