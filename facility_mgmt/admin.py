"""
设施管理 Django Admin 配置
"""
from django.contrib import admin
from .models import (
    FacilityImage, DetectionJob, DetectionJobImage,
    InferenceResult, TrainingJob, TrainingImage,
    FacilityReport, CameraConfig
)


class DetectionJobImageInline(admin.TabularInline):
    """检测任务图片关联内联"""
    model = DetectionJobImage
    extra = 0
    readonly_fields = ('order',)


@admin.register(FacilityImage)
class FacilityImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'source_type', 'location_remark', 'captured_at', 'uploaded_by')
    list_filter = ('source_type', 'captured_at')
    search_fields = ('location_remark',)
    readonly_fields = ('captured_at',)


@admin.register(DetectionJob)
class DetectionJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'status', 'total_images', 'processed_images', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'started_at', 'completed_at')
    inlines = [DetectionJobImageInline]


@admin.register(InferenceResult)
class InferenceResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'facility_category', 'confidence', 'damage_level', 'estimated_lifespan_days', 'processed_at')
    list_filter = ('facility_category', 'damage_level', 'processed_at')
    search_fields = ('facility_category',)
    readonly_fields = ('processed_at',)


@admin.register(TrainingJob)
class TrainingJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'status', 'base_model', 'epochs', 'map50', 'created_at')
    list_filter = ('status', 'base_model', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'started_at', 'completed_at')


@admin.register(TrainingImage)
class TrainingImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'annotation_status', 'annotated_by', 'verified_by', 'created_at')
    list_filter = ('annotation_status', 'created_at')
    search_fields = ('annotations',)
    readonly_fields = ('created_at', 'verified_at')


@admin.register(FacilityReport)
class FacilityReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'report_date', 'total_facilities_detected', 'total_damaged', 'created_at')
    list_filter = ('report_date',)
    search_fields = ('recommendations',)
    readonly_fields = ('created_at',)


@admin.register(CameraConfig)
class CameraConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'camera_type', 'location_remark', 'is_active', 'last_capture_at')
    list_filter = ('camera_type', 'is_active', 'created_at')
    search_fields = ('name', 'location_remark', 'url')
    readonly_fields = ('created_at', 'updated_at', 'last_capture_at')
