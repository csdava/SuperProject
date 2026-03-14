from django.db import models
from django.db.models import Sum
from django.conf import settings


class FeeType(models.Model):
    """费用类型（物业费、水费、电费等）。"""

    name = models.CharField("费用名称", max_length=50)
    code = models.CharField("编号", max_length=20, blank=True)
    unit = models.CharField("单位", max_length=30, default="元", help_text="如：元/月、元/度")

    class Meta:
        verbose_name = "费用类型"
        verbose_name_plural = "费用类型"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Bill(models.Model):
    """账单（按房间、费用类型、账期）。"""

    class Status(models.TextChoices):
        PENDING = "pending", "待缴费"
        PARTIAL = "partial", "部分缴费"
        PAID = "paid", "已缴清"
        OVERDUE = "overdue", "已逾期"

    room = models.ForeignKey(
        "community_core.Room",
        on_delete=models.CASCADE,
        related_name="bills",
        verbose_name="房间",
    )
    fee_type = models.ForeignKey(
        FeeType,
        on_delete=models.PROTECT,
        related_name="bills",
        verbose_name="费用类型",
    )
    period = models.CharField("账期", max_length=20, help_text="如：2024-01 表示 2024年1月")
    amount = models.DecimalField("应收金额", max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField("已缴金额", max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        "状态",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    due_date = models.DateField("到期日", null=True, blank=True)
    paid_at = models.DateTimeField("缴清时间", null=True, blank=True)
    remark = models.CharField("备注", max_length=200, blank=True)
    created_at = models.DateTimeField("生成时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "账单"
        verbose_name_plural = "账单"
        ordering = ("-period", "-created_at")
        unique_together = ("room", "fee_type", "period")

    def __str__(self):
        return f"{self.room} {self.fee_type} {self.period}"

    def update_status(self):
        """根据已缴金额更新状态。"""
        if self.paid_amount >= self.amount:
            self.status = self.Status.PAID
            if not self.paid_at:
                from django.utils import timezone
                self.paid_at = timezone.now()
        elif self.paid_amount > 0:
            self.status = self.Status.PARTIAL
        else:
            from django.utils import timezone
            if self.due_date and self.due_date < timezone.now().date():
                self.status = self.Status.OVERDUE
            else:
                self.status = self.Status.PENDING
        self.save(update_fields=["status", "paid_at", "updated_at"])


class Payment(models.Model):
    """缴费记录。"""

    class PaymentMethod(models.TextChoices):
        OFFLINE = "offline", "线下/现金"
        BANK = "bank", "银行转账"
        ONLINE = "online", "在线缴费"
        OTHER = "other", "其他"

    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="账单",
    )
    amount = models.DecimalField("缴费金额", max_digits=12, decimal_places=2)
    payment_method = models.CharField(
        "支付方式",
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.OFFLINE,
    )
    paid_at = models.DateTimeField("缴费时间", auto_now_add=True)
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fee_payments_made",
        verbose_name="操作人",
    )
    remark = models.CharField("备注", max_length=200, blank=True)

    class Meta:
        verbose_name = "缴费记录"
        verbose_name_plural = "缴费记录"
        ordering = ("-paid_at",)

    def __str__(self):
        return f"{self.bill} 缴 {self.amount}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # 更新账单已缴金额与状态
        self.bill.paid_amount = self.bill.payments.aggregate(total=Sum("amount"))["total"] or 0
        self.bill.update_status()
