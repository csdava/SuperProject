from django.urls import path
from . import views

app_name = "property_fees"
urlpatterns = [
    path("household/", views.household_bill_list, name="household_bill_list"),
    path("household/bills/<int:pk>/", views.household_bill_detail, name="household_bill_detail"),
    path("household/payments/", views.household_payment_list, name="household_payment_list"),
    # 管理员端 - 财务管理
    path("admin/feetypes/", views.admin_fee_type_list, name="admin_fee_type_list"),
    path("admin/feetypes/add/", views.admin_fee_type_create, name="admin_fee_type_create"),
    path("admin/feetypes/<int:pk>/edit/", views.admin_fee_type_edit, name="admin_fee_type_edit"),
    path("admin/bills/", views.admin_bill_list, name="admin_bill_list"),
    path("admin/bills/add/", views.admin_bill_create, name="admin_bill_create"),
    path("admin/bills/bulk/", views.admin_bill_bulk, name="admin_bill_bulk"),
    path("admin/bills/<int:pk>/edit/", views.admin_bill_edit, name="admin_bill_edit"),
    path("admin/payments/", views.admin_payment_list, name="admin_payment_list"),
    path("admin/payments/add/", views.admin_payment_add, name="admin_payment_add"),
    path("admin/stats/", views.admin_fee_stats, name="admin_fee_stats"),
]
