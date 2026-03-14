from django.urls import path
from . import views

app_name = "property_fees"
urlpatterns = [
    path("household/", views.household_bill_list, name="household_bill_list"),
    path("household/bills/<int:pk>/", views.household_bill_detail, name="household_bill_detail"),
    path("household/payments/", views.household_payment_list, name="household_payment_list"),
]
