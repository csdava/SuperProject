from django.contrib import admin
from .models import VisitorInvite


@admin.register(VisitorInvite)
class VisitorInviteAdmin(admin.ModelAdmin):
    list_display = ("visitor_name", "room", "inviter", "status", "valid_from", "valid_until", "created_at")
    list_filter = ("status",)
    search_fields = ("visitor_name", "visitor_phone", "inviter__username", "room__room_no")
    readonly_fields = ("token", "created_at", "checked_in_at")
