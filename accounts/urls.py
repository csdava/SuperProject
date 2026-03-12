from django.urls import path
from . import views

app_name = "accounts"
urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_select_role, name="login_select_role"),
    path("login/form/", views.login_form, name="login_form"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/household/", views.dashboard_household, name="dashboard_household"),
    path("dashboard/maintenance/", views.dashboard_maintenance, name="dashboard_maintenance"),
    path("dashboard/admin/", views.dashboard_admin, name="dashboard_admin"),
]
