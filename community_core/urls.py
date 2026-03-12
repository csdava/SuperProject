from django.urls import path
from . import views

app_name = "community_core"
urlpatterns = [
    path("", views.home, name="home"),
    # 管理员 Web 工作台 - 住户管理
    path("core/residents/", views.resident_list, name="admin_resident_list"),
    path("core/residents/<int:pk>/", views.resident_detail, name="admin_resident_detail"),
]
