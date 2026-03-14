from django.urls import path
from . import views

app_name = "community_core"
urlpatterns = [
    path("", views.home, name="home"),
    # 管理员 Web 工作台 - 住户管理
    path("core/residents/", views.resident_list, name="admin_resident_list"),
    path("core/residents/<int:pk>/", views.resident_detail, name="admin_resident_detail"),
    path("core/residents/<int:pk>/edit/", views.admin_resident_edit, name="admin_resident_edit"),
    path("core/residents/<int:pk>/delete/", views.admin_resident_delete, name="admin_resident_delete"),
    path("core/buildings/", views.admin_building_list, name="admin_building_list"),
    path("core/buildings/add/", views.admin_building_create, name="admin_building_create"),
    path("core/buildings/<int:pk>/", views.admin_building_detail, name="admin_building_detail"),
    path("core/buildings/<int:pk>/edit/", views.admin_building_edit, name="admin_building_edit"),
    path("core/units/<int:pk>/edit/", views.admin_unit_edit, name="admin_unit_edit"),
    path("core/rooms/", views.admin_room_list, name="admin_room_list"),
    path("core/rooms/add/", views.admin_room_create, name="admin_room_create"),
    path("core/rooms/<int:pk>/", views.admin_room_detail, name="admin_room_detail"),
    path("core/rooms/<int:pk>/edit/", views.admin_room_edit, name="admin_room_edit"),
    path("core/tags/", views.admin_tag_list, name="admin_tag_list"),
    path("core/tags/add/", views.admin_tag_create, name="admin_tag_create"),
    path("core/tags/<int:pk>/edit/", views.admin_tag_edit, name="admin_tag_edit"),
    path("core/tags/<int:pk>/delete/", views.admin_tag_delete, name="admin_tag_delete"),
    path("core/ownership/", views.admin_ownership_list, name="admin_ownership_list"),
    path("core/ownership/add/", views.admin_ownership_add, name="admin_ownership_add"),
    # 户主端 - 个人中心
    path("household/profile/", views.household_profile_index, name="household_profile_index"),
    path("household/profile/personal/", views.household_personal_info, name="household_personal_info"),
    path("household/profile/family/", views.household_family_members, name="household_family_members"),
    path("household/profile/housing/", views.household_housing_info, name="household_housing_info"),
    path("household/profile/password/", views.household_change_password, name="household_change_password"),
    path("household/profile/messages/", views.household_messages, name="household_messages"),
    path("household/profile/feedback/", views.household_feedback, name="household_feedback"),
]
