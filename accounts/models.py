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


class LoginLog(models.Model):
    """登录日志（成功/失败、用户名、IP）。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_logs",
        verbose_name="用户",
    )
    username_attempted = models.CharField("尝试登录用户名", max_length=150, blank=True)
    success = models.BooleanField("是否成功", default=False)
    ip_address = models.GenericIPAddressField("IP 地址", null=True, blank=True)
    created_at = models.DateTimeField("时间", auto_now_add=True)

    class Meta:
        verbose_name = "登录日志"
        verbose_name_plural = "登录日志"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.username_attempted} {'成功' if self.success else '失败'} @ {self.created_at}"


class AuditLog(models.Model):
    """操作日志（管理员关键操作）。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="操作人",
    )
    action = models.CharField("操作类型", max_length=100, help_text="如：用户审批、修改角色、参数配置")
    message = models.CharField("说明", max_length=500, blank=True)
    created_at = models.DateTimeField("时间", auto_now_add=True)

    class Meta:
        verbose_name = "操作日志"
        verbose_name_plural = "操作日志"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.action} - {self.user_id} @ {self.created_at}"


class SystemConfig(models.Model):
    """基础参数配置（键值对）。"""

    key = models.CharField("参数键", max_length=100, unique=True)
    value = models.TextField("参数值", blank=True)
    description = models.CharField("说明", max_length=200, blank=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "系统参数"
        verbose_name_plural = "系统参数"

    def __str__(self):
        return self.key
