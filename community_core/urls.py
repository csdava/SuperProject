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
    # 管理员 Web 工作台 - 社区服务（公告、活动）
    path("core/announcements/", views.admin_announcement_list, name="admin_announcement_list"),
    path("core/announcements/add/", views.admin_announcement_create, name="admin_announcement_create"),
    path("core/announcements/<int:pk>/edit/", views.admin_announcement_edit, name="admin_announcement_edit"),
    path("core/announcements/<int:pk>/delete/", views.admin_announcement_delete, name="admin_announcement_delete"),
    path("core/announcements/<int:pk>/pin/", views.admin_announcement_toggle_pin, name="admin_announcement_toggle_pin"),
    path("core/activities/", views.admin_activity_list, name="admin_activity_list"),
    path("core/activities/add/", views.admin_activity_create, name="admin_activity_create"),
    path("core/activities/<int:pk>/", views.admin_activity_detail, name="admin_activity_detail"),
    path("core/activities/<int:pk>/edit/", views.admin_activity_edit, name="admin_activity_edit"),
    # 户主端 - 个人中心
    path("household/profile/", views.household_profile_index, name="household_profile_index"),
    path("household/profile/personal/", views.household_personal_info, name="household_personal_info"),
    path("household/profile/family/", views.household_family_members, name="household_family_members"),
    path("household/profile/housing/", views.household_housing_info, name="household_housing_info"),
    path("household/profile/password/", views.household_change_password, name="household_change_password"),
    path("household/profile/messages/", views.household_messages, name="household_messages"),
    path("household/profile/feedback/", views.household_feedback, name="household_feedback"),
    # 户主端 - 社区公告与活动
    path("household/announcements/", views.household_announcement_list, name="household_announcement_list"),
    path("household/announcements/<int:pk>/", views.household_announcement_detail, name="household_announcement_detail"),
    path("household/activities/", views.household_activity_list, name="household_activity_list"),
    path("household/activities/<int:pk>/", views.household_activity_detail, name="household_activity_detail"),
    # 户主端 - 邻里圈
    path("household/neighborhood/", views.household_neighborhood_feed, name="household_neighborhood_feed"),
    path("household/neighborhood/create/", views.household_neighborhood_create, name="household_neighborhood_create"),
    path("household/neighborhood/my/", views.household_neighborhood_my_posts, name="household_neighborhood_my_posts"),
    path("household/neighborhood/<int:pk>/", views.household_neighborhood_detail, name="household_neighborhood_detail"),
    path("household/neighborhood/<int:pk>/delete/", views.household_neighborhood_delete, name="household_neighborhood_delete"),
    # 户主端 - 社区服务（家政、快递、报失）
    path("household/services/bookings/", views.household_service_booking_list, name="household_service_booking_list"),
    path("household/services/bookings/create/", views.household_service_booking_create, name="household_service_booking_create"),
    path("household/services/parcels/", views.household_parcel_list, name="household_parcel_list"),
    path("household/services/parcels/create/", views.household_parcel_create, name="household_parcel_create"),
    path("household/services/parcels/<int:pk>/taken/", views.household_parcel_mark_taken, name="household_parcel_mark_taken"),
    path("household/services/lost/", views.household_lost_report_list, name="household_lost_report_list"),
    path("household/services/lost/create/", views.household_lost_report_create, name="household_lost_report_create"),
]
