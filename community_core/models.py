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


class UserMessage(models.Model):
    """户主端消息通知（系统/物业推送）。"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="community_messages",
        verbose_name="接收用户",
    )
    title = models.CharField("标题", max_length=100)
    content = models.TextField("内容", blank=True)
    is_read = models.BooleanField("已读", default=False)
    created_at = models.DateTimeField("发送时间", auto_now_add=True)

    class Meta:
        verbose_name = "用户消息"
        verbose_name_plural = "用户消息"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.title} -> {self.user.username}"


class UserFeedback(models.Model):
    """户主意见反馈。"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="community_feedbacks",
        verbose_name="用户",
    )
    content = models.TextField("反馈内容")
    created_at = models.DateTimeField("提交时间", auto_now_add=True)
    reply = models.TextField("回复内容", blank=True)
    replied_at = models.DateTimeField("回复时间", null=True, blank=True)

    class Meta:
        verbose_name = "用户反馈"
        verbose_name_plural = "用户反馈"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.user.username} @ {self.created_at}"


# ---------- 社区服务：公告、活动 ----------


class Announcement(models.Model):
    """社区公告（管理员发布）。"""

    title = models.CharField("标题", max_length=200)
    content = models.TextField("内容", blank=True)
    is_pinned = models.BooleanField("是否置顶", default=False)
    is_published = models.BooleanField("是否已发布", default=False)
    published_at = models.DateTimeField("发布时间", null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_announcements",
        verbose_name="发布人",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "社区公告"
        verbose_name_plural = "社区公告"
        ordering = ("-is_pinned", "-published_at", "-created_at")

    def __str__(self) -> str:
        return self.title


class CommunityActivity(models.Model):
    """社区活动（管理员发布）。"""

    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        PUBLISHED = "published", "已发布"
        ENDED = "ended", "已结束"

    title = models.CharField("活动标题", max_length=200)
    description = models.TextField("活动说明", blank=True)
    start_time = models.DateTimeField("开始时间")
    end_time = models.DateTimeField("结束时间")
    location = models.CharField("活动地点", max_length=200, blank=True)
    max_participants = models.PositiveIntegerField("人数上限", null=True, blank=True, help_text="不填表示不限制")
    status = models.CharField(
        "状态",
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_activities",
        verbose_name="创建人",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "社区活动"
        verbose_name_plural = "社区活动"
        ordering = ("-start_time",)

    def __str__(self) -> str:
        return self.title


class ActivityRegistration(models.Model):
    """活动报名记录。"""

    class RegStatus(models.TextChoices):
        REGISTERED = "registered", "已报名"
        CANCELLED = "cancelled", "已取消"

    activity = models.ForeignKey(
        CommunityActivity,
        on_delete=models.CASCADE,
        related_name="registrations",
        verbose_name="活动",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="activity_registrations",
        verbose_name="报名用户",
    )
    status = models.CharField(
        "状态",
        max_length=20,
        choices=RegStatus.choices,
        default=RegStatus.REGISTERED,
    )
    registered_at = models.DateTimeField("报名时间", auto_now_add=True)
    remark = models.CharField("备注", max_length=200, blank=True)

    class Meta:
        verbose_name = "活动报名"
        verbose_name_plural = "活动报名"
        ordering = ("-registered_at",)
        unique_together = ("activity", "user")

    def __str__(self) -> str:
        return f"{self.user.username} - {self.activity.title}"


# ---------- 邻里圈：动态 / 二手市场 / 邻里互助 ----------


class NeighborhoodPost(models.Model):
    """邻里圈帖子（动态、二手市场、邻里互助）。"""

    class PostType(models.TextChoices):
        DYNAMIC = "dynamic", "动态"
        SECOND_HAND = "second_hand", "二手市场"
        HELP = "help", "邻里互助"

    class PostStatus(models.TextChoices):
        NORMAL = "normal", "正常"
        HIDDEN = "hidden", "已隐藏"
        VIOLATED = "violated", "违规下架"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="neighborhood_posts",
        verbose_name="发布人",
    )
    post_type = models.CharField(
        "类型",
        max_length=20,
        choices=PostType.choices,
        default=PostType.DYNAMIC,
    )
    title = models.CharField("标题", max_length=200, blank=True, help_text="动态可留空，二手/互助建议填写")
    content = models.TextField("内容")
    contact_info = models.CharField("联系方式", max_length=100, blank=True, help_text="选填，二手/互助可留电话或房号")
    status = models.CharField(
        "状态",
        max_length=20,
        choices=PostStatus.choices,
        default=PostStatus.NORMAL,
    )
    created_at = models.DateTimeField("发布时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "邻里圈帖子"
        verbose_name_plural = "邻里圈帖子"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return (self.title or self.content[:30]) + f" ({self.get_post_type_display()})"

