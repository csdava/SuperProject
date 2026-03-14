from django.urls import path
from . import views

app_name = "repair"
urlpatterns = [
    # 管理员端 - 工单管理
    path("admin/orders/", views.admin_order_list, name="admin_order_list"),
    path("admin/orders/<int:pk>/", views.admin_order_detail, name="admin_order_detail"),
    # 户主端 - 报事报修
    path("household/", views.household_repair_list, name="household_repair_list"),
    path("household/create/", views.household_repair_create, name="household_repair_create"),
    path("household/<int:pk>/", views.household_repair_detail, name="household_repair_detail"),
    # 维修人员端 - 我的工单
    path("maintenance/", views.maintenance_order_list, name="maintenance_order_list"),
    path("maintenance/<int:pk>/", views.maintenance_order_detail, name="maintenance_order_detail"),
    path("maintenance/stats/", views.maintenance_order_stats, name="maintenance_order_stats"),
    # 维修人员端 - 接单处理
    path("maintenance/available/", views.maintenance_available_orders, name="maintenance_available_orders"),
    path("maintenance/available/<int:pk>/accept/", views.maintenance_accept_order, name="maintenance_accept_order"),
    path("maintenance/settings/accept/", views.maintenance_accept_settings, name="maintenance_accept_settings"),
    path("maintenance/overdue/", views.maintenance_overdue_list, name="maintenance_overdue_list"),
    # 维修人员端 - 个人中心
    path("maintenance/profile/", views.maintenance_profile_index, name="maintenance_profile_index"),
    path("maintenance/profile/schedule/", views.maintenance_schedule_list, name="maintenance_schedule_list"),
    path("maintenance/profile/payslip/", views.maintenance_payslip_list, name="maintenance_payslip_list"),
    path("maintenance/profile/certs/", views.maintenance_cert_list, name="maintenance_cert_list"),
    path("maintenance/profile/training/", views.maintenance_training_list, name="maintenance_training_list"),
    path("maintenance/profile/training/<int:pk>/", views.maintenance_training_detail, name="maintenance_training_detail"),
    # 维修人员端 - 巡检任务
    path("maintenance/inspection/", views.maintenance_inspection_list, name="maintenance_inspection_list"),
    path("maintenance/inspection/<int:pk>/", views.maintenance_inspection_detail, name="maintenance_inspection_detail"),
]
