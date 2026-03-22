from django.urls import path
from . import views

app_name = "accounts"
urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_select_role, name="login_select_role"),
    path("login/form/", views.login_form, name="login_form"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/household/", views.dashboard_household, name="dashboard_household"),
    path(
        "dashboard/household/current-sensor/",
        views.household_current_sensor,
        name="household_current_sensor",
    ),
    path("dashboard/maintenance/", views.dashboard_maintenance, name="dashboard_maintenance"),
    path("dashboard/admin/", views.dashboard_admin, name="dashboard_admin"),
    # 系统管理（仅管理员）
    path("admin/users/", views.admin_user_list, name="admin_user_list"),
    path("admin/users/<int:user_id>/edit/", views.admin_user_edit, name="admin_user_edit"),
    path("admin/login-log/", views.admin_login_log_list, name="admin_login_log_list"),
    path("admin/audit-log/", views.admin_audit_log_list, name="admin_audit_log_list"),
    path("admin/system-config/", views.admin_system_config_list, name="admin_system_config_list"),
    path("admin/system-config/add/", views.admin_system_config_create, name="admin_system_config_create"),
    path("admin/system-config/<int:pk>/edit/", views.admin_system_config_edit, name="admin_system_config_edit"),
]
