"""
智慧社区管理系统 - 根 URL 配置
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("community_core.urls")),
    # 后续按模块挂载：
    # path("fees/", include("property_fees.urls")),
    # path("repair/", include("repair.urls")),
    # path("visitor/", include("visitor_access.urls")),
    # path("security/", include("security.urls")),
    # path("services/", include("life_services.urls")),
    # path("vehicle/", include("vehicle_mgmt.urls")),
    # path("facility/", include("facility_mgmt.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
