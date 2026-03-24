"""
设施管理 URL 配置
"""
from django.urls import path
from . import views

app_name = 'facility_mgmt'

urlpatterns = [
    # ==================== API 端点 ====================
    # 检测 API
    path('api/detect/', views.api_detect, name='api_detect'),
    path('api/detect/batch/', views.api_detect_batch, name='api_detect_batch'),
    path('api/detect/jobs/<int:job_id>/', views.api_detect_job_status, name='api_detect_job_status'),

    # 摄像头 API
    path('api/camera/capture/', views.api_camera_capture, name='api_camera_capture'),

    # 训练 API
    path('api/training/upload/', views.api_training_upload, name='api_training_upload'),

    # 报告 API
    path('api/report/', views.api_facility_report, name='api_facility_report'),

    # ==================== Web 页面 ====================
    # 仪表盘
    path('dashboard/', views.facility_dashboard, name='facility_dashboard'),

    # 检测管理
    path('detection/upload/', views.detection_upload, name='detection_upload'),
    path('detection/jobs/', views.detection_jobs_list, name='detection_jobs_list'),
    path('detection/jobs/<int:job_id>/', views.detection_job_detail, name='detection_job_detail'),

    # 训练管理
    path('training/', views.training_dashboard, name='training_dashboard'),

    # 摄像头管理
    path('cameras/', views.camera_management, name='camera_management'),

    # 报告
    path('reports/', views.facility_reports, name='facility_reports'),
]
