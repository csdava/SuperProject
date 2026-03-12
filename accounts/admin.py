from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


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
