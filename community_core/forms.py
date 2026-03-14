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
    Announcement,
    CommunityActivity,
    NeighborhoodPost,
    ServiceBooking,
    ParcelRecord,
    LostItemReport,
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


# ---------- 管理员端：社区服务（公告、活动） ----------


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ("title", "content", "is_pinned", "is_published")
        labels = {"title": "标题", "content": "内容", "is_pinned": "置顶", "is_published": "发布"}
        widgets = {"content": forms.Textarea(attrs={"rows": 6})}


class CommunityActivityForm(forms.ModelForm):
    class Meta:
        model = CommunityActivity
        fields = (
            "title",
            "description",
            "start_time",
            "end_time",
            "location",
            "max_participants",
            "status",
        )
        labels = {
            "title": "活动标题",
            "description": "活动说明",
            "start_time": "开始时间",
            "end_time": "结束时间",
            "location": "活动地点",
            "max_participants": "人数上限（不填不限制）",
            "status": "状态",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class NeighborhoodPostForm(forms.ModelForm):
    """邻里圈发帖表单。"""

    class Meta:
        model = NeighborhoodPost
        fields = ("post_type", "title", "content", "contact_info")
        labels = {
            "post_type": "类型",
            "title": "标题（动态可留空）",
            "content": "内容",
            "contact_info": "联系方式（选填）",
        }
        widgets = {
            "content": forms.Textarea(attrs={"rows": 4, "placeholder": "请填写正文…"}),
            "contact_info": forms.TextInput(attrs={"placeholder": "电话或房号，选填"}),
        }


# ---------- 户主端社区服务：家政预约、快递代收、物品报失 ----------


class ServiceBookingForm(forms.ModelForm):
    class Meta:
        model = ServiceBooking
        fields = ("service_type", "preferred_date", "preferred_time", "contact_phone", "address_remark", "remark")
        labels = {
            "service_type": "服务类型",
            "preferred_date": "期望日期",
            "preferred_time": "期望时段",
            "contact_phone": "联系电话",
            "address_remark": "地址备注",
            "remark": "备注说明",
        }
        widgets = {
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
            "remark": forms.Textarea(attrs={"rows": 3}),
        }


class ParcelRecordForm(forms.ModelForm):
    class Meta:
        model = ParcelRecord
        fields = ("carrier", "pickup_code", "remark")
        labels = {"carrier": "快递公司", "pickup_code": "取件码", "remark": "备注"}
        widgets = {"carrier": forms.TextInput(attrs={"placeholder": "如：顺丰、菜鸟"})}


class LostItemReportForm(forms.ModelForm):
    class Meta:
        model = LostItemReport
        fields = ("item_desc", "lost_place", "lost_time", "contact_phone", "remark")
        labels = {
            "item_desc": "物品描述",
            "lost_place": "丢失地点",
            "lost_time": "丢失时间说明",
            "contact_phone": "联系电话",
            "remark": "补充说明",
        }
        widgets = {"remark": forms.Textarea(attrs={"rows": 3})}


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
