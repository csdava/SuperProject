from django.urls import path
from . import views

app_name = "vehicle_mgmt"
urlpatterns = [
    path("household/vehicles/", views.household_vehicle_list, name="household_vehicle_list"),
    path("household/vehicles/create/", views.household_vehicle_create, name="household_vehicle_create"),
    path("household/vehicles/<int:pk>/edit/", views.household_vehicle_edit, name="household_vehicle_edit"),
    path("household/vehicles/<int:pk>/delete/", views.household_vehicle_delete, name="household_vehicle_delete"),
    path("household/parking/", views.household_parking_list, name="household_parking_list"),
    path("household/temp/", views.household_temp_request_list, name="household_temp_request_list"),
    path("household/temp/create/", views.household_temp_request_create, name="household_temp_request_create"),
    path("household/violations/", views.household_violation_list, name="household_violation_list"),
]
