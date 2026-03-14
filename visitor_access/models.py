import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


def default_token():
    return uuid.uuid4().hex[:16]


class VisitorInvite(models.Model):
    """访客邀请（户主发起，访客凭链接/邀请码/二维码通行）。"""

    class Status(models.TextChoices):
        ACTIVE = "active", "有效"
        CANCELLED = "cancelled", "已取消"
        EXPIRED = "expired", "已过期"
        USED = "used", "已使用"

    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="visitor_invites",
        verbose_name="邀请人",
    )
    visitor_name = models.CharField("访客姓名", max_length=50)
    visitor_phone = models.CharField("访客电话", max_length=30, blank=True)
    id_number = models.CharField("访客证件号", max_length=50, blank=True)
    purpose = models.CharField("来访事由", max_length=200, blank=True)
    room = models.ForeignKey(
        "community_core.Room",
        on_delete=models.CASCADE,
        related_name="visitor_invites",
        verbose_name="到访房间",
    )
    valid_from = models.DateTimeField("有效期起", default=timezone.now)
    valid_until = models.DateTimeField("有效期止")
    status = models.CharField(
        "状态",
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    token = models.CharField("邀请码/令牌", max_length=32, unique=True, default=default_token, editable=False)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    checked_in_at = models.DateTimeField("实际到访时间", null=True, blank=True)

    class Meta:
        verbose_name = "访客邀请"
        verbose_name_plural = "访客邀请"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.visitor_name} -> {self.room} ({self.get_status_display()})"

    def update_status_by_time(self):
        """根据当前时间更新过期状态。"""
        if self.status != self.Status.ACTIVE:
            return
        now = timezone.now()
        if now > self.valid_until:
            self.status = self.Status.EXPIRED
            self.save(update_fields=["status"])
