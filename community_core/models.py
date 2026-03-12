from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Building(models.Model):
    """楼栋信息。"""

    name = models.CharField("楼栋名称", max_length=50)
    code = models.CharField("楼栋编号", max_length=20, unique=True)
    address = models.CharField("详细地址", max_length=200, blank=True)
    remark = models.CharField("备注", max_length=200, blank=True)

    class Meta:
        verbose_name = "楼栋"
        verbose_name_plural = "楼栋"

    def __str__(self) -> str:
        return f"{self.name}({self.code})"


class Unit(models.Model):
    """单元信息。"""

    building = models.ForeignKey(
        Building, on_delete=models.CASCADE, related_name="units", verbose_name="楼栋"
    )
    name = models.CharField("单元名称/编号", max_length=20)

    class Meta:
        verbose_name = "单元"
        verbose_name_plural = "单元"
        unique_together = ("building", "name")

    def __str__(self) -> str:
        return f"{self.building}-{self.name}单元"


class Room(models.Model):
    """房间信息。"""

    class RoomStatus(models.TextChoices):
        OCCUPIED = "occupied", "已入住"
        VACANT = "vacant", "空置"
        RESERVED = "reserved", "预留"

    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, related_name="rooms", verbose_name="单元"
    )
    floor_no = models.CharField("楼层", max_length=10, blank=True)
    room_no = models.CharField("房号", max_length=20)
    area = models.DecimalField("建筑面积(㎡)", max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField(
        "房间状态",
        max_length=20,
        choices=RoomStatus.choices,
        default=RoomStatus.VACANT,
    )
    owner_name = models.CharField("产权人姓名", max_length=50, blank=True)
    owner_phone = models.CharField("产权人电话", max_length=30, blank=True)
    owner_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_rooms",
        verbose_name="绑定户主账号",
        help_text="可选，绑定到实际登录账号的户主。",
    )

    class Meta:
        verbose_name = "房间"
        verbose_name_plural = "房间"
        unique_together = ("unit", "room_no")

    def __str__(self) -> str:
        return f"{self.unit}-{self.room_no}"


class ResidentTag(models.Model):
    """住户标签：VIP、特殊需求、欠费等。"""

    name = models.CharField("标签名称", max_length=50, unique=True)
    description = models.CharField("说明", max_length=200, blank=True)

    class Meta:
        verbose_name = "住户标签"
        verbose_name_plural = "住户标签"

    def __str__(self) -> str:
        return self.name


class Resident(models.Model):
    """住户信息（含家庭成员）。"""

    class ResidentStatus(models.TextChoices):
        ACTIVE = "active", "在住"
        MOVED_OUT = "moved_out", "已迁出"
        ARREARS = "arrears", "欠费"

    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name="residents", verbose_name="房间"
    )
    name = models.CharField("姓名", max_length=50)
    phone = models.CharField("联系电话", max_length=30, blank=True)
    id_number = models.CharField("证件号", max_length=50, blank=True)
    is_householder = models.BooleanField("是否户主", default=False)
    relation_to_householder = models.CharField(
        "与户主关系", max_length=50, blank=True, help_text="如：本人、配偶、子女、父母等"
    )
    status = models.CharField(
        "住户状态",
        max_length=20,
        choices=ResidentStatus.choices,
        default=ResidentStatus.ACTIVE,
    )
    tags = models.ManyToManyField(
        ResidentTag, blank=True, related_name="residents", verbose_name="标签"
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "住户"
        verbose_name_plural = "住户"

    def __str__(self) -> str:
        return f"{self.name} - {self.room}"


class OwnershipChange(models.Model):
    """产权变更记录。"""

    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name="ownership_changes", verbose_name="房间"
    )
    old_owner_name = models.CharField("原产权人姓名", max_length=50, blank=True)
    new_owner_name = models.CharField("新产权人姓名", max_length=50)
    changed_at = models.DateTimeField("变更时间", auto_now_add=True)
    reason = models.CharField("变更原因", max_length=200, blank=True)
    operator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ownership_changes",
        verbose_name="操作人",
    )

    class Meta:
        verbose_name = "产权变更记录"
        verbose_name_plural = "产权变更记录"
        ordering = ("-changed_at",)

    def __str__(self) -> str:
        return f"{self.room} 产权变更：{self.old_owner_name} → {self.new_owner_name}"

