from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class RepairOrder(models.Model):
    """报事报修工单。"""

    class Category(models.TextChoices):
        REPAIR = "repair", "报修"
        COMPLAINT = "complaint", "投诉"
        OTHER = "other", "其他"

    class Status(models.TextChoices):
        PENDING = "pending", "待处理"
        ASSIGNED = "assigned", "已派单"
        IN_PROGRESS = "in_progress", "处理中"
        COMPLETED = "completed", "已完成"
        CANCELLED = "cancelled", "已取消"

    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="repair_orders",
        verbose_name="报修人",
    )
    room = models.ForeignKey(
        "community_core.Room",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="repair_orders",
        verbose_name="报修房间",
    )
    category = models.CharField(
        "类型",
        max_length=20,
        choices=Category.choices,
        default=Category.REPAIR,
    )
    title = models.CharField("标题", max_length=100)
    description = models.TextField("问题描述")
    contact_phone = models.CharField("联系电话", max_length=30, blank=True)
    status = models.CharField(
        "状态",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_repair_orders",
        verbose_name="指派给",
    )
    admin_remark = models.TextField("管理备注", blank=True)
    worker_remark = models.TextField("维修人员备注", blank=True, help_text="接单/处理过程中填写")
    created_at = models.DateTimeField("提交时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    completed_at = models.DateTimeField("完成时间", null=True, blank=True)
    cost_amount = models.DecimalField(
        "费用金额",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="维修产生的材料/人工等费用（如有）",
    )
    cost_note = models.CharField("费用说明", max_length=200, blank=True)

    class Meta:
        verbose_name = "报修工单"
        verbose_name_plural = "报修工单"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class RepairEvaluation(models.Model):
    """工单服务评价。"""

    order = models.OneToOneField(
        RepairOrder,
        on_delete=models.CASCADE,
        related_name="evaluation",
        verbose_name="工单",
    )
    rating = models.PositiveSmallIntegerField(
        "评分",
        choices=[(i, str(i) + "星") for i in range(1, 6)],
    )
    comment = models.TextField("评价内容", blank=True)
    created_at = models.DateTimeField("评价时间", auto_now_add=True)

    class Meta:
        verbose_name = "工单评价"
        verbose_name_plural = "工单评价"

    def __str__(self):
        return f"{self.order.title} - {self.rating}星"


class MaintenancePreference(models.Model):
    """维修人员接单偏好（如是否自动接单）。"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="maintenance_preference",
        verbose_name="用户",
    )
    auto_accept = models.BooleanField("自动接单", default=False)

    class Meta:
        verbose_name = "维修接单偏好"
        verbose_name_plural = "维修接单偏好"

    def __str__(self):
        return f"{self.user.username} 自动接单={self.auto_accept}"


class RepairProgressLog(models.Model):
    """维修进度记录（上报记录）。"""

    order = models.ForeignKey(
        RepairOrder,
        on_delete=models.CASCADE,
        related_name="progress_logs",
        verbose_name="工单",
    )
    content = models.TextField("进度内容")
    created_at = models.DateTimeField("上报时间", auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="repair_progress_logs",
        verbose_name="上报人",
    )

    class Meta:
        verbose_name = "维修进度记录"
        verbose_name_plural = "维修进度记录"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.order.title} @ {self.created_at}"


class RepairPartUsage(models.Model):
    """配件使用登记。"""

    order = models.ForeignKey(
        RepairOrder,
        on_delete=models.CASCADE,
        related_name="part_usages",
        verbose_name="工单",
    )
    part_name = models.CharField("配件名称", max_length=100)
    quantity = models.DecimalField("数量", max_digits=10, decimal_places=2, default=1)
    unit = models.CharField("单位", max_length=20, default="个")
    remark = models.CharField("备注", max_length=200, blank=True)
    created_at = models.DateTimeField("登记时间", auto_now_add=True)

    class Meta:
        verbose_name = "配件使用"
        verbose_name_plural = "配件使用"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.order.title} - {self.part_name} x{self.quantity}"


class MaintenanceSchedule(models.Model):
    """维修人员工作排班。"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="maintenance_schedules",
        verbose_name="维修人员",
    )
    work_date = models.DateField("排班日期")
    shift_name = models.CharField("班次名称", max_length=50)
    start_time = models.TimeField("开始时间", null=True, blank=True)
    end_time = models.TimeField("结束时间", null=True, blank=True)
    remark = models.CharField("备注", max_length=200, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "维修排班"
        verbose_name_plural = "维修排班"
        ordering = ("-work_date", "-start_time")

    def __str__(self):
        return f"{self.user.username} {self.work_date} {self.shift_name}"


class MaintenancePayslip(models.Model):
    """维修人员工资单。"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="maintenance_payslips",
        verbose_name="维修人员",
    )
    period = models.CharField("工资周期", max_length=20)
    base_salary = models.DecimalField("基本工资", max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField("奖金/补贴", max_digits=10, decimal_places=2, default=0)
    deduction = models.DecimalField("扣款", max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField("实发", max_digits=10, decimal_places=2, default=0)
    remark = models.CharField("备注", max_length=200, blank=True)
    created_at = models.DateTimeField("生成时间", auto_now_add=True)

    class Meta:
        verbose_name = "维修工资单"
        verbose_name_plural = "维修工资单"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.username} {self.period}"


class MaintenanceCert(models.Model):
    """维修人员技能认证。"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="maintenance_certs",
        verbose_name="维修人员",
    )
    cert_name = models.CharField("证书名称", max_length=100)
    cert_no = models.CharField("证书编号", max_length=80, blank=True)
    issued_at = models.DateField("发证日期", null=True, blank=True)
    expiry_at = models.DateField("有效期至", null=True, blank=True)
    issuer = models.CharField("发证机构", max_length=100, blank=True)
    created_at = models.DateTimeField("登记时间", auto_now_add=True)

    class Meta:
        verbose_name = "技能认证"
        verbose_name_plural = "技能认证"
        ordering = ("-issued_at",)

    def __str__(self):
        return f"{self.user.username} - {self.cert_name}"


class TrainingMaterial(models.Model):
    """培训资料（全体维修人员可查看）。"""

    title = models.CharField("标题", max_length=200)
    content = models.TextField("内容", blank=True)
    attachment = models.CharField("附件路径/链接", max_length=300, blank=True)
    created_at = models.DateTimeField("发布时间", auto_now_add=True)

    class Meta:
        verbose_name = "培训资料"
        verbose_name_plural = "培训资料"
        ordering = ("-created_at",)

    def __str__(self):
        return self.title


class InspectionTask(models.Model):
    """巡检任务（计划/指派给维修人员）。"""

    class Status(models.TextChoices):
        PENDING = "pending", "待执行"
        IN_PROGRESS = "in_progress", "进行中"
        COMPLETED = "completed", "已完成"

    title = models.CharField("巡检标题", max_length=100)
    task_date = models.DateField("巡检日期")
    assignee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="inspection_tasks",
        verbose_name="执行人",
    )
    status = models.CharField(
        "状态",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    route_remark = models.CharField("巡检路线/区域说明", max_length=300, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "巡检任务"
        verbose_name_plural = "巡检任务"
        ordering = ("-task_date", "-created_at")

    def __str__(self):
        return f"{self.title} ({self.task_date})"


class InspectionCheckIn(models.Model):
    """巡检打卡记录。"""

    task = models.ForeignKey(
        InspectionTask,
        on_delete=models.CASCADE,
        related_name="check_ins",
        verbose_name="巡检任务",
    )
    check_in_at = models.DateTimeField("打卡时间", auto_now_add=True)
    location = models.CharField("打卡位置", max_length=100)
    remark = models.CharField("备注", max_length=200, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inspection_check_ins",
        verbose_name="打卡人",
    )

    class Meta:
        verbose_name = "巡检打卡"
        verbose_name_plural = "巡检打卡"
        ordering = ("-check_in_at",)

    def __str__(self):
        return f"{self.task.title} @ {self.check_in_at}"


class InspectionAbnormality(models.Model):
    """巡检异常上报。"""

    class Severity(models.TextChoices):
        LOW = "low", "一般"
        MEDIUM = "medium", "较重"
        HIGH = "high", "严重"

    class AbnormalityStatus(models.TextChoices):
        PENDING = "pending", "待处理"
        HANDLED = "handled", "已处理"

    task = models.ForeignKey(
        InspectionTask,
        on_delete=models.CASCADE,
        related_name="abnormalities",
        verbose_name="巡检任务",
    )
    content = models.TextField("异常描述")
    severity = models.CharField(
        "严重程度",
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM,
    )
    reported_at = models.DateTimeField("上报时间", auto_now_add=True)
    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inspection_abnormalities",
        verbose_name="上报人",
    )
    status = models.CharField(
        "处理状态",
        max_length=20,
        choices=AbnormalityStatus.choices,
        default=AbnormalityStatus.PENDING,
    )

    class Meta:
        verbose_name = "巡检异常"
        verbose_name_plural = "巡检异常"
        ordering = ("-reported_at",)

    def __str__(self):
        return f"{self.task.title} - {self.get_severity_display()}"
