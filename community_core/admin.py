from django.contrib import admin

from .models import (
    Building,
    Unit,
    Room,
    ResidentTag,
    Resident,
    OwnershipChange,
    UserMessage,
    UserFeedback,
    Announcement,
    CommunityActivity,
    ActivityRegistration,
    NeighborhoodPost,
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


@admin.register(UserMessage)
class UserMessageAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("title", "content", "user__username")


@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ("user", "content_preview", "created_at", "replied_at")
    list_filter = ("created_at",)
    search_fields = ("content", "user__username")

    def content_preview(self, obj):
        return (obj.content[:40] + "…") if len(obj.content) > 40 else obj.content

    content_preview.short_description = "内容摘要"


class ActivityRegistrationInline(admin.TabularInline):
    model = ActivityRegistration
    extra = 0
    readonly_fields = ("registered_at",)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "is_pinned", "is_published", "published_at", "created_by", "created_at")
    list_filter = ("is_pinned", "is_published")
    search_fields = ("title", "content")


@admin.register(CommunityActivity)
class CommunityActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "start_time", "end_time", "location", "status", "created_by", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "description", "location")
    inlines = [ActivityRegistrationInline]


@admin.register(ActivityRegistration)
class ActivityRegistrationAdmin(admin.ModelAdmin):
    list_display = ("activity", "user", "status", "registered_at")
    list_filter = ("status", "activity")
    search_fields = ("user__username", "activity__title")


@admin.register(NeighborhoodPost)
class NeighborhoodPostAdmin(admin.ModelAdmin):
    list_display = ("title", "post_type", "user", "status", "created_at")
    list_filter = ("post_type", "status")
    search_fields = ("title", "content", "user__username")
