from django.contrib import admin
from .models import Vehicle, ParkingSpace, TempParkingRequest, ViolationRecord


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("plate_number", "user", "brand_model", "color", "created_at")
    list_filter = ("user",)
    search_fields = ("plate_number", "user__username")


@admin.register(ParkingSpace)
class ParkingSpaceAdmin(admin.ModelAdmin):
    list_display = ("code", "zone", "space_type", "status", "remark")
    list_filter = ("space_type", "status")
    search_fields = ("code", "zone")


@admin.register(TempParkingRequest)
class TempParkingRequestAdmin(admin.ModelAdmin):
    list_display = ("plate_number", "user", "start_time", "end_time", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("plate_number", "user__username")


@admin.register(ViolationRecord)
class ViolationRecordAdmin(admin.ModelAdmin):
    list_display = ("plate_number", "user", "violation_type", "occurred_at", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("plate_number", "user__username", "violation_type")
