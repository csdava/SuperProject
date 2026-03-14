from django.urls import path
from . import views

app_name = "visitor_access"
urlpatterns = [
    path("household/", views.household_invite_list, name="household_invite_list"),
    path("household/create/", views.household_invite_create, name="household_invite_create"),
    path("household/<int:pk>/", views.household_invite_detail, name="household_invite_detail"),
    path("household/<int:pk>/cancel/", views.household_invite_cancel, name="household_invite_cancel"),
    path("v/<str:token>/", views.invite_show, name="invite_show"),
]
