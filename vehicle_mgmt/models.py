from django.db import models
from django.conf import settings


class Vehicle(models.Model):
    """户主登记的车辆。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vehicles",
        verbose_name="车主",
    )
    plate_number = models.CharField("车牌号", max_length=20)
    brand_model = models.CharField("品牌型号", max_length=100, blank=True)
    color = models.CharField("颜色", max_length=30, blank=True)
    created_at = models.DateTimeField("登记时间", auto_now_add=True)

    class Meta:
        verbose_name = "车辆"
        verbose_name_plural = "车辆"
        ordering = ("-created_at",)
        unique_together = ("user", "plate_number")

    def __str__(self):
        return f"{self.plate_number} ({self.user.username})"


class ParkingSpace(models.Model):
    """车位（由管理员维护，户主可查看状态）。"""

    class SpaceType(models.TextChoices):
        FIXED = "fixed", "固定车位"
        TEMP = "temp", "临停车位"

    class Status(models.TextChoices):
        VACANT = "vacant", "空闲"
        OCCUPIED = "occupied", "占用"
        RESERVED = "reserved", "预留"

    code = models.CharField("车位编号", max_length=50, unique=True)
    zone = models.CharField("区域", max_length=100, blank=True, help_text="如：地库A区、地面B区")
    space_type = models.CharField(
        "类型",
        max_length=20,
        choices=SpaceType.choices,
        default=SpaceType.FIXED,
    )
    status = models.CharField(
        "状态",
        max_length=20,
        choices=Status.choices,
        default=Status.VACANT,
    )
    remark = models.CharField("备注", max_length=200, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "车位"
        verbose_name_plural = "车位"
        ordering = ("zone", "code")

    def __str__(self):
        return f"{self.code} ({self.get_space_type_display()})"


class TempParkingRequest(models.Model):
    """临停申请（户主提交）。"""

    class Status(models.TextChoices):
        PENDING = "pending", "待审批"
        APPROVED = "approved", "已通过"
        REJECTED = "rejected", "已拒绝"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="temp_parking_requests",
        verbose_name="申请人",
    )
    plate_number = models.CharField("车牌号", max_length=20)
    start_time = models.DateTimeField("预计进入时间")
    end_time = models.DateTimeField("预计离开时间")
    purpose = models.CharField("事由", max_length=200, blank=True)
    status = models.CharField(
        "状态",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField("申请时间", auto_now_add=True)
    admin_remark = models.CharField("审批备注", max_length=200, blank=True)

    class Meta:
        verbose_name = "临停申请"
        verbose_name_plural = "临停申请"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.plate_number} {self.start_time.date()} ({self.get_status_display()})"


class ViolationRecord(models.Model):
    """违规记录（管理员录入，户主可查看本人相关）。"""

    class Status(models.TextChoices):
        PENDING = "pending", "待处理"
        PAID = "paid", "已处理"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="violation_records",
        verbose_name="关联户主",
    )
    plate_number = models.CharField("车牌号", max_length=20)
    violation_type = models.CharField("违规类型", max_length=100, help_text="如：违停、占道")
    description = models.CharField("违规说明", max_length=300, blank=True)
    occurred_at = models.DateTimeField("发生时间", null=True, blank=True)
    status = models.CharField(
        "状态",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField("录入时间", auto_now_add=True)

    class Meta:
        verbose_name = "违规记录"
        verbose_name_plural = "违规记录"
        ordering = ("-occurred_at", "-created_at")

    def __str__(self):
        return f"{self.plate_number} {self.violation_type} ({self.get_status_display()})"
