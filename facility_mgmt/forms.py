"""
设施管理表单
"""
from django import forms
from .models import FacilityImage, DetectionJob, TrainingImage, CameraConfig


class FacilityImageUploadForm(forms.ModelForm):
    """设施图片上传表单"""

    class Meta:
        model = FacilityImage
        fields = ['image', 'location_remark', 'source_type']
        widgets = {
            'location_remark': forms.TextInput(attrs={
                'placeholder': '如: 1号楼北侧健身区',
                'class': 'form-control',
            }),
            'source_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = True
        self.fields['image'].widget.attrs.update({'class': 'form-control'})


class DetectionJobForm(forms.ModelForm):
    """检测任务表单"""

    class Meta:
        model = DetectionJob
        fields = ['name', 'model_version']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': '如: 2024年第一季度设施巡检',
                'class': 'form-control',
            }),
            'model_version': forms.TextInput(attrs={
                'placeholder': 'yolo26n',
                'class': 'form-control',
            }),
        }


class TrainingImageForm(forms.ModelForm):
    """训练图片表单（用于手动标注）"""

    class Meta:
        model = TrainingImage
        fields = ['image', 'annotations', 'annotation_status']
        widgets = {
            'annotations': forms.Textarea(attrs={
                'placeholder': '{"annotations": [{"class_id": 0, "bbox": [...]}]}',
                'class': 'form-control',
                'rows': 5,
            }),
            'annotation_status': forms.Select(attrs={'class': 'form-select'}),
        }


class CameraConfigForm(forms.ModelForm):
    """摄像头配置表单"""

    class Meta:
        model = CameraConfig
        fields = ['name', 'camera_type', 'url', 'location_remark', 'is_active', 'capture_interval']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': '如: 1号楼门口摄像头',
                'class': 'form-control',
            }),
            'camera_type': forms.Select(attrs={'class': 'form-select'}),
            'url': forms.TextInput(attrs={
                'placeholder': 'rtsp://192.168.1.100:554/stream',
                'class': 'form-control',
            }),
            'location_remark': forms.TextInput(attrs={
                'placeholder': '如: 1号楼北门',
                'class': 'form-control',
            }),
            'capture_interval': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 60,
            }),
        }
