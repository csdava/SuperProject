"""
设施管理 API 视图
提供设施检测、摄像头集成、报告等 API
"""
import os
import time
import json
import tempfile
from datetime import datetime
from pathlib import Path

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .models import (
    FacilityImage, DetectionJob, DetectionJobImage,
    InferenceResult, TrainingJob, TrainingImage,
    FacilityReport, CameraConfig, DamageLevel
)
from .services.yolo_detector import YOLOFacilityDetector, get_detector
from .services.damage_assessor import DamageAssessor, assess_damage
from .services.camera_adapter import CameraAdapter, capture_from_url


# ==================== 工具函数 ====================

def get_yolo_detector() -> YOLOFacilityDetector:
    """获取 YOLO 检测器实例"""
    return get_detector()


def get_damage_assessor() -> DamageAssessor:
    """获取损坏评估器实例"""
    return DamageAssessor()


def process_detection(image_path: str) -> dict:
    """
    处理单张图片检测

    Returns:
        {
            'detections': [...],
            'total_detected': int,
            'processing_time_ms': int
        }
    """
    start_time = time.time()

    # 执行检测
    detector = get_yolo_detector()
    detections = detector.detect(image_path)

    # 评估损坏程度
    assessor = get_damage_assessor()
    results = []

    for det in detections:
        assessment = assessor.assess(det)
        results.append({
            'category': det['class_name'],
            'category_display': det['class_display'],
            'bbox': det['bbox'],
            'confidence': det['confidence'],
            'damage_level': assessment.damage_level,
            'estimated_lifespan_days': assessment.estimated_lifespan_days,
            'damage_reasons': assessment.damage_reasons,
        })

    processing_time = int((time.time() - start_time) * 1000)

    return {
        'detections': results,
        'total_detected': len(results),
        'processing_time_ms': processing_time,
    }


# ==================== API 端点 ====================

@csrf_exempt
@require_http_methods(["POST"])
def api_detect(request):
    """
    单张图片检测 API

    POST /facility/api/detect/
    Content-Type: multipart/form-data
    Form Data:
        image: <file>
        conf_threshold: float (optional, default 0.25)
        camera_id: int (optional, 如果使用摄像头抓拍)

    Response:
        {
            "success": true,
            "image_id": 123,
            "detections": [...],
            "total_detected": 5,
            "processing_time_ms": 234
        }
    """
    try:
        # 检查是否有图片文件
        if 'image' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': '未提供图片文件'
            }, status=400)

        image_file = request.FILES['image']
        conf_threshold = float(request.POST.get('conf_threshold', 0.25))

        # 保存图片
        facility_image = FacilityImage.objects.create(
            image=image_file,
            source_type=FacilityImage.SourceType.MANUAL_UPLOAD,
            uploaded_by=request.user if request.user.is_authenticated else None,
        )

        # 获取图片路径
        image_path = facility_image.image.path

        # 处理检测
        result = process_detection(image_path)

        # 保存检测结果
        job = None  # 单张检测不关联任务
        for det in result['detections']:
            InferenceResult.objects.create(
                image=facility_image,
                job=job,
                facility_category=det['category'],
                bbox_x1=det['bbox'][0],
                bbox_y1=det['bbox'][1],
                bbox_x2=det['bbox'][2],
                bbox_y2=det['bbox'][3],
                confidence=det['confidence'],
                damage_level=det['damage_level'],
                estimated_lifespan_days=det['estimated_lifespan_days'],
                damage_reasons=det['damage_reasons'],
            )

        return JsonResponse({
            'success': True,
            'image_id': facility_image.id,
            'detections': result['detections'],
            'total_detected': result['total_detected'],
            'processing_time_ms': result['processing_time_ms'],
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_detect_batch(request):
    """
    批量检测任务 API

    POST /facility/api/detect/batch/
    Content-Type: application/json
    Body: {"image_ids": [1, 2, 3], "job_name": "Weekly Inspection"}

    Response:
        {"success": true, "job_id": 45, "status": "pending", "total_images": 3}
    """
    try:
        body = json.loads(request.body)
        image_ids = body.get('image_ids', [])
        job_name = body.get('job_name', f'Batch Detection {datetime.now().strftime("%Y%m%d %H:%M")}')

        if not image_ids:
            return JsonResponse({
                'success': False,
                'error': '未提供图片ID列表'
            }, status=400)

        # 创建检测任务
        job = DetectionJob.objects.create(
            name=job_name,
            total_images=len(image_ids),
            created_by=request.user if request.user.is_authenticated else None,
        )

        # 关联图片
        for i, image_id in enumerate(image_ids):
            try:
                image = FacilityImage.objects.get(id=image_id)
                DetectionJobImage.objects.create(job=job, image=image, order=i)
            except FacilityImage.DoesNotExist:
                pass

        # 注意：实际检测应该异步处理，这里同步处理作为简化
        job.status = 'processing'
        job.started_at = datetime.now()
        job.save()

        processed = 0
        errors = []

        for job_image in job.job_images.all():
            try:
                result = process_detection(job_image.image.image.path)
                for det in result['detections']:
                    InferenceResult.objects.create(
                        image=job_image.image,
                        job=job,
                        facility_category=det['category'],
                        bbox_x1=det['bbox'][0],
                        bbox_y1=det['bbox'][1],
                        bbox_x2=det['bbox'][2],
                        bbox_y2=det['bbox'][3],
                        confidence=det['confidence'],
                        damage_level=det['damage_level'],
                        estimated_lifespan_days=det['estimated_lifespan_days'],
                        damage_reasons=det['damage_reasons'],
                    )
                processed += 1
            except Exception as e:
                errors.append(f"Image {job_image.image_id}: {str(e)}")

        job.processed_images = processed
        job.status = 'completed' if not errors else 'completed_with_errors'
        job.completed_at = datetime.now()
        if errors:
            job.error_message = json.dumps(errors)
        job.save()

        return JsonResponse({
            'success': True,
            'job_id': job.id,
            'status': job.status,
            'total_images': job.total_images,
            'processed_images': processed,
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_detect_job_status(request, job_id):
    """
    获取检测任务状态

    GET /facility/api/detect/jobs/<job_id>/

    Response:
        {
            "job_id": 45,
            "status": "completed",
            "total_images": 3,
            "processed_images": 3,
            "results": [...]
        }
    """
    job = get_object_or_404(DetectionJob, id=job_id)

    results = []
    if job.status == 'completed':
        for result in job.results.all()[:100]:  # 限制返回数量
            results.append({
                'id': result.id,
                'category': result.facility_category,
                'category_display': result.get_facility_category_display(),
                'bbox': result.bbox,
                'confidence': result.confidence,
                'damage_level': result.damage_level,
                'estimated_lifespan_days': result.estimated_lifespan_days,
                'damage_reasons': result.damage_reasons,
            })

    return JsonResponse({
        'job_id': job.id,
        'name': job.name,
        'status': job.status,
        'total_images': job.total_images,
        'processed_images': job.processed_images,
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'error_message': job.error_message,
        'results': results,
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_camera_capture(request):
    """
    摄像头抓拍并检测 API

    POST /facility/api/camera/capture/
    Content-Type: application/json
    Body: {"camera_id": 1} 或 {"camera_url": "rtsp://..."}

    Response:
        {"success": true, "image_id": 123, "detections": [...], ...}
    """
    try:
        body = json.loads(request.body)
        camera_id = body.get('camera_id')
        camera_url = body.get('camera_url')
        save_image = body.get('save_image', True)

        # 获取摄像头 URL
        if camera_id:
            camera = get_object_or_404(CameraConfig, id=camera_id, is_active=True)
            url = camera.url
            camera_type = camera.camera_type
        elif camera_url:
            url = camera_url
            camera_type = 'auto'
        else:
            return JsonResponse({
                'success': False,
                'error': '未提供 camera_id 或 camera_url'
            }, status=400)

        # 抓拍图片
        frame = capture_from_url(url, camera_type)

        if frame is None:
            return JsonResponse({
                'success': False,
                'error': '摄像头抓拍失败'
            }, status=500)

        # 保存为临时文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            import cv2
            cv2.imwrite(f.name, frame)
            temp_path = f.name

        try:
            # 处理检测
            result = process_detection(temp_path)

            # 保存图片
            if save_image:
                with open(temp_path, 'rb') as f:
                    facility_image = FacilityImage.objects.create(
                        source_type=FacilityImage.SourceType.CAMERA_CAPTURE,
                        uploaded_by=request.user if request.user.is_authenticated else None,
                        location_remark=camera.name if camera_id else url,
                    )
                    facility_image.image.save(f'temp_{facility_image.pk}.jpg', f)

                # 保存检测结果
                for det in result['detections']:
                    InferenceResult.objects.create(
                        image=facility_image,
                        facility_category=det['category'],
                        bbox_x1=det['bbox'][0],
                        bbox_y1=det['bbox'][1],
                        bbox_x2=det['bbox'][2],
                        bbox_y2=det['bbox'][3],
                        confidence=det['confidence'],
                        damage_level=det['damage_level'],
                        estimated_lifespan_days=det['estimated_lifespan_days'],
                        damage_reasons=det['damage_reasons'],
                    )

                image_id = facility_image.id
            else:
                image_id = None

            return JsonResponse({
                'success': True,
                'image_id': image_id,
                'detections': result['detections'],
                'total_detected': result['total_detected'],
                'processing_time_ms': result['processing_time_ms'],
            })

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_training_upload(request):
    """
    上传训练图片 API

    POST /facility/api/training/upload/
    Content-Type: multipart/form-data
    Form Data:
        image: <file>
        annotations: <json> - YOLO格式标注
        original_image_id: int (可选)

    Response:
        {"success": true, "image_id": 500, "status": "annotated"}
    """
    try:
        if 'image' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': '未提供图片文件'
            }, status=400)

        image_file = request.FILES['image']
        annotations = json.loads(request.POST.get('annotations', '{}'))
        original_image_id = request.POST.get('original_image_id')

        original_image = None
        if original_image_id:
            try:
                original_image = FacilityImage.objects.get(id=original_image_id)
            except FacilityImage.DoesNotExist:
                pass

        # 创建训练图片
        training_image = TrainingImage.objects.create(
            image=image_file,
            original_image=original_image,
            annotations=annotations,
            annotated_by=request.user if request.user.is_authenticated else None,
            annotation_status=TrainingImage.AnnotationStatus.ANNOTATED,
        )

        return JsonResponse({
            'success': True,
            'image_id': training_image.id,
            'status': training_image.annotation_status,
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_facility_report(request):
    """
    获取设施报告 API

    GET /facility/api/report/?start_date=2024-01-01&end_date=2024-01-31

    Response:
        {
            "report_date": "2024-01-31",
            "total_facilities_detected": 150,
            "total_damaged": 12,
            "damage_by_category": {...},
            "avg_estimated_lifespan_days": 245,
            "recommendations": "..."
        }
    """
    from datetime import datetime as dt

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # 查询检测结果
    results = InferenceResult.objects.all()

    if start_date:
        results = results.filter(processed_at__gte=start_date)
    if end_date:
        results = results.filter(processed_at__lte=end_date)

    # 统计
    total_detected = results.count()
    total_damaged = results.exclude(damage_level=DamageLevel.NORMAL).count()

    damage_by_category = {}
    lifespan_sum = 0
    lifespan_count = 0

    for result in results:
        cat = result.facility_category
        if cat not in damage_by_category:
            damage_by_category[cat] = {'total': 0, 'damaged': 0}
        damage_by_category[cat]['total'] += 1

        if result.damage_level != DamageLevel.NORMAL:
            damage_by_category[cat]['damaged'] += 1

        if result.estimated_lifespan_days:
            lifespan_sum += result.estimated_lifespan_days
            lifespan_count += 1

    avg_lifespan = lifespan_sum / lifespan_count if lifespan_count > 0 else None

    # 生成建议
    recommendations = generate_recommendations(damage_by_category)

    return JsonResponse({
        'report_date': dt.now().date().isoformat(),
        'total_facilities_detected': total_detected,
        'total_damaged': total_damaged,
        'damage_by_category': damage_by_category,
        'avg_estimated_lifespan_days': round(avg_lifespan, 1) if avg_lifespan else None,
        'recommendations': recommendations,
    })


def generate_recommendations(damage_by_category: dict) -> str:
    """根据损坏统计生成维护建议"""
    recommendations = []

    category_display = {
        'public_seat': '公共座椅',
        'lighting': '照明灯',
        'electricity_meter': '电表',
        'water_meter': '水表',
        'street_light': '路灯',
        'speed_bump': '减速带',
    }

    damaged_items = []
    for cat, stats in damage_by_category.items():
        if stats['damaged'] > 0:
            name = category_display.get(cat, cat)
            damaged_items.append(f"{name}({stats['damaged']}处)")

    if damaged_items:
        recommendations.append(f"建议优先检修: {', '.join(damaged_items)}")
    else:
        recommendations.append("所有设施状态良好，建议定期巡检。")

    return "；".join(recommendations)


# ==================== Web 视图 ====================

@login_required
def facility_dashboard(request):
    """设施管理仪表盘"""
    total_images = FacilityImage.objects.count()
    total_detections = InferenceResult.objects.count()
    damaged_facilities = InferenceResult.objects.exclude(
        damage_level=DamageLevel.NORMAL
    ).count()

    recent_results = InferenceResult.objects.select_related('image').order_by('-processed_at')[:10]

    context = {
        'total_images': total_images,
        'total_detections': total_detections,
        'damaged_facilities': damaged_facilities,
        'recent_results': recent_results,
    }
    return render(request, 'facility_mgmt/dashboard.html', context)


@login_required
def detection_upload(request):
    """检测图片上传页面"""
    return render(request, 'facility_mgmt/detection_upload.html')


@login_required
def detection_jobs_list(request):
    """检测任务列表"""
    jobs = DetectionJob.objects.order_by('-created_at')[:50]
    return render(request, 'facility_mgmt/detection_jobs_list.html', {'jobs': jobs})


@login_required
def detection_job_detail(request, job_id):
    """检测任务详情"""
    job = get_object_or_404(DetectionJob, id=job_id)
    results = job.results.select_related('image').all()
    return render(request, 'facility_mgmt/detection_job_detail.html', {
        'job': job,
        'results': results,
    })


@login_required
def facility_reports(request):
    """设施报告页面"""
    reports = FacilityReport.objects.order_by('-report_date')[:12]
    return render(request, 'facility_mgmt/facility_reports.html', {'reports': reports})


@login_required
def training_dashboard(request):
    """训练管理页面"""
    training_jobs = TrainingJob.objects.order_by('-created_at')[:20]
    pending_images = TrainingImage.objects.filter(
        annotation_status=TrainingImage.AnnotationStatus.PENDING
    ).count()
    verified_images = TrainingImage.objects.filter(
        annotation_status=TrainingImage.AnnotationStatus.VERIFIED
    ).count()

    context = {
        'training_jobs': training_jobs,
        'pending_images': pending_images,
        'verified_images': verified_images,
    }
    return render(request, 'facility_mgmt/training_dashboard.html', context)


@login_required
def camera_management(request):
    """摄像头管理页面"""
    cameras = CameraConfig.objects.order_by('-is_active', 'name')
    return render(request, 'facility_mgmt/camera_management.html', {'cameras': cameras})
