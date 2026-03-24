from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class FacilityCategory(models.TextChoices):
    PUBLIC_SEAT = 'public_seat', '公共座椅'
    LIGHTING = 'lighting', '照明灯'
    ELECTRICITY_METER = 'electricity_meter', '电表'
    WATER_METER = 'water_meter', '水表'
    STREET_LIGHT = 'street_light', '路灯'
    SPEED_BUMP = 'speed_bump', '减速带'


class DetectionStatus(models.TextChoices):
    PENDING = 'pending', '待检测'
    PROCESSING = 'processing', '检测中'
    COMPLETED = 'completed', '已完成'
    FAILED = 'failed', '失败'


class DamageLevel(models.TextChoices):
    NORMAL = 'normal', '正常'
    MINOR = 'minor', '轻微损坏'
    MODERATE = 'moderate', '中等损坏'
    SEVERE = 'severe', '严重损坏'


class AnnotationStatus(models.TextChoices):
    PENDING = 'pending', '待标注'
    ANNOTATED = 'annotated', '已标注'
    VERIFIED = 'verified', '已验证'
    REJECTED = 'rejected', '已拒绝'


class TrainingStatus(models.TextChoices):
    PENDING = 'pending', '待训练'
    TRAINING = 'training', '训练中'
    COMPLETED = 'completed', '已完成'
    FAILED = 'failed', '失败'


class FacilityImage(models.Model):
    """设施检测图片来源"""

    class SourceType(models.TextChoices):
        MANUAL_UPLOAD = 'manual_upload', '手动上传'
        CAMERA_CAPTURE = 'camera_capture', '摄像头采集'
        INSPECTION = 'inspection', '巡检采集'

    image = models.ImageField('图片', upload_to='facility_images/raw/%Y/%m/')
    captured_at = models.DateTimeField('采集时间', auto_now_add=True)
    location_remark = models.CharField('位置备注', max_length=200, blank=True)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='uploaded_facility_images', verbose_name='上传人'
    )
    source_type = models.CharField(
        '图片来源', max_length=20, choices=SourceType.choices,
        default=SourceType.MANUAL_UPLOAD
    )

    class Meta:
        verbose_name = '设施图片'
        verbose_name_plural = '设施图片'
        ordering = ('-captured_at',)

    def __str__(self):
        return f"Image {self.pk} ({self.get_source_type_display()})"


class DetectionJob(models.Model):
    """批量检测任务"""

    name = models.CharField('任务名称', max_length=100)
    status = models.CharField('状态', max_length=20, choices=DetectionStatus.choices, default='pending')
    model_version = models.CharField('模型版本', max_length=50, default='yolo26n')
    total_images = models.IntegerField('总图片数', default=0)
    processed_images = models.IntegerField('已处理', default=0)
    started_at = models.DateTimeField('开始时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    error_message = models.TextField('错误信息', blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='created_detection_jobs', verbose_name='创建人'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '检测任务'
        verbose_name_plural = '检测任务'
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class DetectionJobImage(models.Model):
    """检测任务与图片的关联"""

    job = models.ForeignKey(DetectionJob, on_delete=models.CASCADE, related_name='job_images')
    image = models.ForeignKey(FacilityImage, on_delete=models.CASCADE, related_name='job_associations')
    order = models.IntegerField('顺序', default=0)

    class Meta:
        unique_together = ('job', 'image')
        ordering = ('order',)


class InferenceResult(models.Model):
    """单个设施检测结果"""

    image = models.ForeignKey(
        FacilityImage, on_delete=models.CASCADE,
        related_name='inference_results', verbose_name='图片'
    )
    job = models.ForeignKey(
        DetectionJob, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='results', verbose_name='检测任务'
    )
    facility_category = models.CharField('设施类别', max_length=30, choices=FacilityCategory.choices)
    bbox_x1 = models.FloatField('边界框X1', help_text='归一化坐标 0-1')
    bbox_y1 = models.FloatField('边界框Y1')
    bbox_x2 = models.FloatField('边界框X2')
    bbox_y2 = models.FloatField('边界框Y2')
    confidence = models.FloatField('检测置信度', help_text='0-1')
    damage_level = models.CharField(
        '损坏等级', max_length=20, choices=DamageLevel.choices, default='normal'
    )
    damage_confidence = models.FloatField('损坏置信度', null=True, blank=True)
    estimated_lifespan_days = models.IntegerField('预计剩余寿命(天)', null=True, blank=True)
    lifespan_confidence = models.FloatField('寿命置信度', null=True, blank=True)
    damage_reasons = models.JSONField('损坏原因列表', default=list, blank=True)
    processed_at = models.DateTimeField('处理时间', auto_now_add=True)

    class Meta:
        verbose_name = '检测结果'
        verbose_name_plural = '检测结果'
        ordering = ('-processed_at',)
        indexes = [
            models.Index(fields=['image', 'facility_category']),
            models.Index(fields=['damage_level']),
        ]

    def __str__(self):
        return f"{self.get_facility_category_display()} @{self.image_id} ({self.confidence:.2f})"

    @property
    def bbox(self):
        return [self.bbox_x1, self.bbox_y1, self.bbox_x2, self.bbox_y2]


class TrainingJob(models.Model):
    """模型训练任务"""

    name = models.CharField('任务名称', max_length=100)
    dataset_version = models.CharField('数据集版本', max_length=50)
    base_model = models.CharField('基础模型', max_length=50, default='yolo26n')
    status = models.CharField('状态', max_length=20, choices=TrainingStatus.choices, default='pending')
    epochs = models.IntegerField('训练轮数', default=100)
    batch_size = models.IntegerField('批次大小', default=16)
    image_size = models.IntegerField('图像尺寸', default=640)
    map50 = models.FloatField('mAP50', null=True, blank=True)
    map50_95 = models.FloatField('mAP50-95', null=True, blank=True)
    model_path = models.CharField('模型路径', max_length=300, null=True, blank=True)
    started_at = models.DateTimeField('开始时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    error_message = models.TextField('错误信息', blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='created_training_jobs', verbose_name='创建人'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '训练任务'
        verbose_name_plural = '训练任务'
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class TrainingImage(models.Model):
    """已标注的训练图片"""

    image = models.ImageField('图片', upload_to='facility_images/annotated/%Y/%m/')
    original_image = models.ForeignKey(
        FacilityImage, on_delete=models.CASCADE,
        null=True, blank=True, related_name='training_images'
    )
    annotations = models.JSONField(
        '标注数据', default=dict,
        help_text='YOLO格式: {"class_id": 0, "bbox": [x_center, y_center, width, height]}'
    )
    annotated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='annotated_training_images', verbose_name='标注人'
    )
    annotation_status = models.CharField(
        '标注状态', max_length=20, choices=AnnotationStatus.choices,
        default=AnnotationStatus.PENDING
    )
    verified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='verified_training_images', verbose_name='审核人'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    verified_at = models.DateTimeField('审核时间', null=True, blank=True)

    class Meta:
        verbose_name = '训练图片'
        verbose_name_plural = '训练图片'
        ordering = ('-created_at',)

    def __str__(self):
        return f"TrainingImage {self.pk} ({self.get_annotation_status_display()})"


class FacilityReport(models.Model):
    """设施状况汇总报告"""

    report_date = models.DateField('报告日期')
    total_facilities_detected = models.IntegerField('检测设施总数', default=0)
    total_damaged = models.IntegerField('损坏设施数', default=0)
    damage_by_category = models.JSONField('各类损坏数量', default=dict)
    avg_estimated_lifespan_days = models.FloatField('平均剩余寿命(天)', null=True, blank=True)
    recommendations = models.TextField('维护建议', blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='created_facility_reports', verbose_name='生成人'
    )
    created_at = models.DateTimeField('生成时间', auto_now_add=True)

    class Meta:
        verbose_name = '设施报告'
        verbose_name_plural = '设施报告'
        ordering = ('-report_date',)
        unique_together = ('report_date',)

    def __str__(self):
        return f"Report {self.report_date} ({self.total_facilities_detected} facilities)"


class CameraConfig(models.Model):
    """摄像头配置"""

    class CameraType(models.TextChoices):
        RTSP = 'rtsp', 'RTSP流'
        HTTP = 'http', 'HTTP API'
        USB = 'usb', 'USB摄像头'
        FILE = 'file', '文件'

    name = models.CharField('摄像头名称', max_length=100)
    camera_type = models.CharField('类型', max_length=20, choices=CameraType.choices)
    url = models.CharField('地址', max_length=500)
    location_remark = models.CharField('位置备注', max_length=200, blank=True)
    is_active = models.BooleanField('启用', default=True)
    capture_interval = models.IntegerField('采集间隔(秒)', default=300)
    last_capture_at = models.DateTimeField('最后采集时间', null=True, blank=True)
    last_capture_status = models.CharField('采集状态', max_length=50, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '摄像头配置'
        verbose_name_plural = '摄像头配置'
        ordering = ('name',)

    def __str__(self):
        return f"{self.name} ({self.get_camera_type_display()})"
