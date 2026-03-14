from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, LoginLog, AuditLog, SystemConfig


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "身份与审批"
    extra = 0


class UserAdminWithProfile(BaseUserAdmin):
    inlines = (UserProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdminWithProfile)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "is_approved", "created_at")
    list_filter = ("role", "is_approved")
    search_fields = ("user__username",)
    list_editable = ("is_approved",)
    actions = ["approve_selected", "reject_selected"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.role == UserProfile.Role.ADMIN:
            obj.user.is_staff = True
            obj.user.save(update_fields=["is_staff"])

    @admin.action(description="批准所选用户")
    def approve_selected(self, request, queryset):
        for p in queryset:
            p.is_approved = True
            p.save()
            if p.role == UserProfile.Role.ADMIN:
                p.user.is_staff = True
                p.user.save(update_fields=["is_staff"])
        self.message_user(request, f"已批准 {queryset.count()} 名用户。")

    @admin.action(description="拒绝所选用户")
    def reject_selected(self, request, queryset):
        n = queryset.update(is_approved=False)
        self.message_user(request, f"已拒绝 {n} 名用户。")


@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display = ("username_attempted", "user", "success", "ip_address", "created_at")
    list_filter = ("success",)
    search_fields = ("username_attempted",)
    readonly_fields = ("user", "username_attempted", "success", "ip_address", "created_at")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "message", "created_at")
    list_filter = ("action",)
    search_fields = ("action", "message")
    readonly_fields = ("user", "action", "message", "created_at")


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ("key", "value_preview", "description", "updated_at")
    search_fields = ("key", "description")

    def value_preview(self, obj):
        return (obj.value[:50] + "…") if obj.value and len(obj.value) > 50 else (obj.value or "")
    value_preview.short_description = "参数值"
