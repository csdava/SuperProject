from django.contrib import admin

from .models import (
    Building,
    Unit,
    Room,
    ResidentTag,
    Resident,
    OwnershipChange,
)


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "address")
    search_fields = ("name", "code", "address")


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "building")
    list_filter = ("building",)
    search_fields = ("name", "building__name", "building__code")


class ResidentInline(admin.TabularInline):
    model = Resident
    extra = 0


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("room_no", "unit", "floor_no", "status", "owner_name", "owner_phone")
    list_filter = ("unit__building", "unit", "status")
    search_fields = (
        "room_no",
        "floor_no",
        "unit__name",
        "unit__building__name",
        "owner_name",
        "owner_phone",
    )
    inlines = [ResidentInline]


@admin.register(ResidentTag)
class ResidentTagAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Resident)
class ResidentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "room",
        "is_householder",
        "relation_to_householder",
        "status",
        "phone",
    )
    list_filter = ("status", "is_householder", "room__unit__building")
    search_fields = ("name", "phone", "room__room_no", "room__unit__name")
    filter_horizontal = ("tags",)


@admin.register(OwnershipChange)
class OwnershipChangeAdmin(admin.ModelAdmin):
    list_display = ("room", "old_owner_name", "new_owner_name", "changed_at", "operator")
    list_filter = ("room__unit__building",)
    search_fields = (
        "room__room_no",
        "room__unit__name",
        "old_owner_name",
        "new_owner_name",
    )
