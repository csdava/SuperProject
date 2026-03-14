from django.contrib import admin
from .models import (
    RepairOrder,
    RepairEvaluation,
    MaintenancePreference,
    RepairProgressLog,
    RepairPartUsage,
    MaintenanceSchedule,
    MaintenancePayslip,
    MaintenanceCert,
    TrainingMaterial,
    InspectionTask,
    InspectionCheckIn,
    InspectionAbnormality,
)


class RepairProgressLogInline(admin.TabularInline):
    model = RepairProgressLog
    extra = 0
    readonly_fields = ("created_at", "created_by")


class RepairPartUsageInline(admin.TabularInline):
    model = RepairPartUsage
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(RepairOrder)
class RepairOrderAdmin(admin.ModelAdmin):
    list_display = ("title", "reporter", "category", "status", "assigned_to", "cost_amount", "created_at", "completed_at")
    list_filter = ("category", "status")
    search_fields = ("title", "description", "reporter__username")
    raw_id_fields = ("reporter", "room", "assigned_to")
    readonly_fields = ("created_at", "updated_at")
    inlines = (RepairProgressLogInline, RepairPartUsageInline)


@admin.register(RepairEvaluation)
class RepairEvaluationAdmin(admin.ModelAdmin):
    list_display = ("order", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("comment", "order__title")


@admin.register(MaintenancePreference)
class MaintenancePreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "auto_accept")
    list_filter = ("auto_accept",)


@admin.register(RepairProgressLog)
class RepairProgressLogAdmin(admin.ModelAdmin):
    list_display = ("order", "content_preview", "created_by", "created_at")
    list_filter = ("created_at",)
    search_fields = ("content", "order__title")

    def content_preview(self, obj):
        return (obj.content[:50] + "…") if len(obj.content) > 50 else obj.content

    content_preview.short_description = "内容"


@admin.register(RepairPartUsage)
class RepairPartUsageAdmin(admin.ModelAdmin):
    list_display = ("order", "part_name", "quantity", "unit", "created_at")
    list_filter = ("order",)
    search_fields = ("part_name", "order__title")


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ("user", "work_date", "shift_name", "start_time", "end_time", "remark")
    list_filter = ("work_date",)
    search_fields = ("user__username", "shift_name")
    raw_id_fields = ("user",)


@admin.register(MaintenancePayslip)
class MaintenancePayslipAdmin(admin.ModelAdmin):
    list_display = ("user", "period", "base_salary", "bonus", "deduction", "total", "created_at")
    list_filter = ("period",)
    search_fields = ("user__username", "period")
    raw_id_fields = ("user",)


@admin.register(MaintenanceCert)
class MaintenanceCertAdmin(admin.ModelAdmin):
    list_display = ("user", "cert_name", "cert_no", "issued_at", "expiry_at", "issuer")
    list_filter = ("issued_at",)
    search_fields = ("user__username", "cert_name", "cert_no")
    raw_id_fields = ("user",)


@admin.register(TrainingMaterial)
class TrainingMaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at")
    search_fields = ("title", "content")


class InspectionCheckInInline(admin.TabularInline):
    model = InspectionCheckIn
    extra = 0
    readonly_fields = ("check_in_at", "created_by")


class InspectionAbnormalityInline(admin.TabularInline):
    model = InspectionAbnormality
    extra = 0
    readonly_fields = ("reported_at", "reported_by")


@admin.register(InspectionTask)
class InspectionTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "task_date", "assignee", "status", "created_at")
    list_filter = ("status", "task_date")
    search_fields = ("title", "route_remark", "assignee__username")
    raw_id_fields = ("assignee",)
    inlines = (InspectionCheckInInline, InspectionAbnormalityInline)


@admin.register(InspectionCheckIn)
class InspectionCheckInAdmin(admin.ModelAdmin):
    list_display = ("task", "check_in_at", "location", "created_by")
    list_filter = ("check_in_at",)
    search_fields = ("location", "task__title")


@admin.register(InspectionAbnormality)
class InspectionAbnormalityAdmin(admin.ModelAdmin):
    list_display = ("task", "content_preview", "severity", "status", "reported_at", "reported_by")
    list_filter = ("severity", "status")
    search_fields = ("content", "task__title")

    def content_preview(self, obj):
        return (obj.content[:40] + "…") if len(obj.content) > 40 else obj.content

    content_preview.short_description = "异常描述"
