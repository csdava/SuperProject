from django.db import models
from django.conf import settings


class UserProfile(models.Model):
    """用户身份与审批状态：户主、管理员、维修人员。"""

    class Role(models.TextChoices):
        HOUSEHOLD = "household", "户主"
        ADMIN = "admin", "管理员"
        MAINTENANCE = "maintenance", "维修人员"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="用户",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.HOUSEHOLD,
        verbose_name="身份",
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name="已审批",
        help_text="户主/维修人员需管理员审批通过后才能登录；管理员默认已审批。",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "用户身份"
        verbose_name_plural = "用户身份"

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def can_login(self):
        """是否允许登录：管理员直接允许，户主/维修人员需已审批。"""
        if self.role == self.Role.ADMIN:
            return True
        return self.is_approved
