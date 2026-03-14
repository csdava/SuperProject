from django import forms
from django.contrib.auth import get_user_model
from .models import (
    RepairOrder,
    RepairEvaluation,
    RepairProgressLog,
    RepairPartUsage,
    InspectionCheckIn,
    InspectionAbnormality,
)

User = get_user_model()


class CreateRepairForm(forms.ModelForm):
    """户主提交报修/投诉表单。"""

    class Meta:
        model = RepairOrder
        fields = ("category", "title", "description", "contact_phone", "room")
        labels = {
            "category": "类型",
            "title": "标题",
            "description": "问题描述",
            "contact_phone": "联系电话",
            "room": "报修房间（选填）",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "请详细描述问题或投诉内容…"}),
            "room": forms.Select(attrs={"class": "room-select"}),
        }


class EvaluationForm(forms.ModelForm):
    """工单服务评价表单。"""

    class Meta:
        model = RepairEvaluation
        fields = ("rating", "comment")
        labels = {"rating": "评分", "comment": "评价内容（选填）"}
        widgets = {"comment": forms.Textarea(attrs={"rows": 3})}


class MaintenanceOrderUpdateForm(forms.ModelForm):
    """维修人员更新工单：状态、备注、费用。"""

    class Meta:
        model = RepairOrder
        fields = ("status", "worker_remark", "cost_amount", "cost_note")
        labels = {
            "status": "状态",
            "worker_remark": "维修备注",
            "cost_amount": "费用金额（元）",
            "cost_note": "费用说明",
        }
        widgets = {
            "worker_remark": forms.Textarea(attrs={"rows": 3, "placeholder": "处理进度、更换配件等"}),
            "cost_amount": forms.NumberInput(attrs={"step": "0.01", "min": "0", "placeholder": "选填"}),
        }


class ProgressLogForm(forms.ModelForm):
    """维修进度上报。"""

    class Meta:
        model = RepairProgressLog
        fields = ("content",)
        labels = {"content": "进度内容"}
        widgets = {"content": forms.Textarea(attrs={"rows": 2, "placeholder": "如：已到场检查、已更换XX配件…"})}


class PartUsageForm(forms.ModelForm):
    """配件使用登记。"""

    class Meta:
        model = RepairPartUsage
        fields = ("part_name", "quantity", "unit", "remark")
        labels = {"part_name": "配件名称", "quantity": "数量", "unit": "单位", "remark": "备注"}
        widgets = {"quantity": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"})}


class InspectionCheckInForm(forms.ModelForm):
    """巡检打卡。"""

    class Meta:
        model = InspectionCheckIn
        fields = ("location", "remark")
        labels = {"location": "打卡位置", "remark": "备注"}
        widgets = {"location": forms.TextInput(attrs={"placeholder": "如：1号楼电梯间"})}


class InspectionAbnormalityForm(forms.ModelForm):
    """巡检异常上报。"""

    class Meta:
        model = InspectionAbnormality
        fields = ("content", "severity")
        labels = {"content": "异常描述", "severity": "严重程度"}
        widgets = {"content": forms.Textarea(attrs={"rows": 3, "placeholder": "请描述发现的异常情况…"})}


class AdminOrderAssignForm(forms.Form):
    """管理员指派工单：维修人员、管理备注。"""

    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),  # 视图中通过 assignee_queryset 覆盖
        required=False,
        label="指派给",
        empty_label="（未指派）",
    )
    admin_remark = forms.CharField(
        required=False,
        label="管理备注",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "内部备注，报修人不可见"}),
    )

    def __init__(self, *args, **kwargs):
        qs = kwargs.pop("assignee_queryset", None)
        super().__init__(*args, **kwargs)
        if qs is not None:
            self.fields["assigned_to"].queryset = qs
