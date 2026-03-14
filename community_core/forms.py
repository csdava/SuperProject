from django import forms
from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from .models import (
    UserFeedback,
    Building,
    Unit,
    Room,
    Resident,
    ResidentTag,
    OwnershipChange,
)

User = get_user_model()


# ---------- 管理员端：楼栋 / 单元 / 房间 / 住户 / 标签 / 产权变更 ----------


class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ("name", "code", "address", "remark")
        labels = {"name": "楼栋名称", "code": "楼栋编号", "address": "详细地址", "remark": "备注"}


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ("building", "name")
        labels = {"building": "所属楼栋", "name": "单元名称/编号"}


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = (
            "unit",
            "floor_no",
            "room_no",
            "area",
            "status",
            "owner_name",
            "owner_phone",
            "owner_user",
        )
        labels = {
            "unit": "所属单元",
            "floor_no": "楼层",
            "room_no": "房号",
            "area": "建筑面积(㎡)",
            "status": "房间状态",
            "owner_name": "产权人姓名",
            "owner_phone": "产权人电话",
            "owner_user": "绑定户主账号",
        }
        widgets = {
            "owner_user": forms.Select(attrs={"class": "user-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["owner_user"].queryset = User.objects.filter(
            profile__role=UserProfile.Role.HOUSEHOLD,
            profile__is_approved=True,
        ).order_by("username")
        self.fields["owner_user"].required = False
        self.fields["owner_user"].empty_label = "（未绑定）"


class ResidentForm(forms.ModelForm):
    class Meta:
        model = Resident
        fields = (
            "name",
            "phone",
            "id_number",
            "is_householder",
            "relation_to_householder",
            "status",
            "tags",
        )
        labels = {
            "name": "姓名",
            "phone": "联系电话",
            "id_number": "证件号",
            "is_householder": "是否户主",
            "relation_to_householder": "与户主关系",
            "status": "住户状态",
            "tags": "标签",
        }
        widgets = {"tags": forms.CheckboxSelectMultiple()}


class ResidentTagForm(forms.ModelForm):
    class Meta:
        model = ResidentTag
        fields = ("name", "description")
        labels = {"name": "标签名称", "description": "说明"}


class OwnershipChangeForm(forms.ModelForm):
    class Meta:
        model = OwnershipChange
        fields = ("room", "old_owner_name", "new_owner_name", "reason")
        labels = {
            "room": "房间",
            "old_owner_name": "原产权人姓名",
            "new_owner_name": "新产权人姓名",
            "reason": "变更原因",
        }
        widgets = {"reason": forms.Textarea(attrs={"rows": 2})}


# ---------- 户主端 ----------


class HouseholdProfileForm(forms.ModelForm):
    """户主个人信息编辑（姓名、邮箱等）。"""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {"first_name": "名", "last_name": "姓", "email": "邮箱"}


class HouseholdFeedbackForm(forms.ModelForm):
    """户主意见反馈表单。"""

    class Meta:
        model = UserFeedback
        fields = ("content",)
        widgets = {"content": forms.Textarea(attrs={"rows": 4, "placeholder": "请输入您的意见或建议…"})}
        labels = {"content": "反馈内容"}
