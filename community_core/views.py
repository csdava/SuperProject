from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q

from django import forms
from django.contrib.auth import get_user_model

from accounts.models import UserProfile
from .models import (
    Resident,
    Room,
    Building,
    Unit,
    ResidentTag,
    OwnershipChange,
    UserMessage,
    UserFeedback,
)
from .forms import (
    HouseholdProfileForm,
    HouseholdFeedbackForm,
    BuildingForm,
    UnitForm,
    RoomForm,
    ResidentForm,
    ResidentTagForm,
    OwnershipChangeForm,
)

User = get_user_model()


def home(request):
    """智慧社区管理系统 - 首页（入口页）。"""
    return render(request, "community_core/home.html")


def _require_admin(request):
    """仅允许管理员访问的简单检查。"""
    if not request.user.is_authenticated:
        return redirect("accounts:login_select_role")
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != UserProfile.Role.ADMIN:
        messages.warning(request, "只有管理员可以访问该页面。")
        return redirect("community_core:home")
    return None


@login_required(login_url="accounts:login_select_role")
def resident_list(request):
    """住户列表 + 搜索。"""
    denied = _require_admin(request)
    if denied:
        return denied

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    building_id = request.GET.get("building", "").strip()

    residents = Resident.objects.select_related("room", "room__unit", "room__unit__building")

    if q:
        residents = residents.filter(
            Q(name__icontains=q)
            | Q(phone__icontains=q)
            | Q(room__room_no__icontains=q)
            | Q(room__unit__name__icontains=q)
            | Q(room__unit__building__name__icontains=q)
        )
    if status:
        residents = residents.filter(status=status)
    if building_id:
        residents = residents.filter(room__unit__building_id=building_id)

    residents = residents.order_by("room__unit__building__name", "room__unit__name", "room__room_no", "-is_householder")
    buildings = Building.objects.all().order_by("name")

    context = {
        "residents": residents,
        "q": q,
        "status": status,
        "building_id": building_id,
        "buildings": buildings,
    }
    return render(request, "community_core/admin_resident_list.html", context)


@login_required(login_url="accounts:login_select_role")
def resident_detail(request, pk: int):
    """住户详情：所在房间 + 家庭成员。"""
    denied = _require_admin(request)
    if denied:
        return denied

    resident = get_object_or_404(
        Resident.objects.select_related("room", "room__unit", "room__unit__building").prefetch_related(
            "tags", "room__residents", "room__ownership_changes"
        ),
        pk=pk,
    )
    room = resident.room
    family_members = room.residents.exclude(pk=resident.pk).order_by("-is_householder", "name")
    ownership_changes = room.ownership_changes.all()

    context = {
        "resident": resident,
        "room": room,
        "family_members": family_members,
        "ownership_changes": ownership_changes,
    }
    return render(request, "community_core/admin_resident_detail.html", context)


# ---------- 管理员端：楼栋 / 单元 ----------


@login_required(login_url="accounts:login_select_role")
def admin_building_list(request):
    """楼栋列表。"""
    denied = _require_admin(request)
    if denied:
        return denied
    buildings = Building.objects.prefetch_related("units").order_by("name")
    return render(request, "community_core/admin_building_list.html", {"buildings": buildings})


@login_required(login_url="accounts:login_select_role")
def admin_building_detail(request, pk):
    """楼栋详情：单元列表、新增单元。"""
    denied = _require_admin(request)
    if denied:
        return denied
    building = get_object_or_404(Building.objects.prefetch_related("units"), pk=pk)
    if request.method == "POST" and request.POST.get("action") == "add_unit":
        form = UnitForm(request.POST)
        if form.is_valid():
            form.instance.building = building
            form.save()
            messages.success(request, "单元已添加。")
            return redirect("community_core:admin_building_detail", pk=pk)
        messages.error(request, "请修正表单错误。")
    else:
        form = UnitForm(initial={"building": building})
    form.fields["building"].widget = forms.HiddenInput()
    form.fields["building"].queryset = Building.objects.filter(pk=building.pk)
    units = building.units.order_by("name")
    return render(
        request,
        "community_core/admin_building_detail.html",
        {"building": building, "units": units, "unit_form": form},
    )


@login_required(login_url="accounts:login_select_role")
def admin_building_create(request):
    """新增楼栋。"""
    denied = _require_admin(request)
    if denied:
        return denied
    if request.method == "POST":
        form = BuildingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "楼栋已添加。")
            return redirect("community_core:admin_building_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = BuildingForm()
    return render(request, "community_core/admin_building_form.html", {"form": form, "is_edit": False})


@login_required(login_url="accounts:login_select_role")
def admin_building_edit(request, pk):
    """编辑楼栋。"""
    denied = _require_admin(request)
    if denied:
        return denied
    building = get_object_or_404(Building, pk=pk)
    if request.method == "POST":
        form = BuildingForm(request.POST, instance=building)
        if form.is_valid():
            form.save()
            messages.success(request, "楼栋已更新。")
            return redirect("community_core:admin_building_detail", pk=pk)
        messages.error(request, "请修正表单错误。")
    else:
        form = BuildingForm(instance=building)
    return render(request, "community_core/admin_building_form.html", {"form": form, "building": building, "is_edit": True})


@login_required(login_url="accounts:login_select_role")
def admin_unit_edit(request, pk):
    """编辑单元。"""
    denied = _require_admin(request)
    if denied:
        return denied
    unit = get_object_or_404(Unit.objects.select_related("building"), pk=pk)
    if request.method == "POST":
        form = UnitForm(request.POST, instance=unit)
        if form.is_valid():
            form.save()
            messages.success(request, "单元已更新。")
            return redirect("community_core:admin_building_detail", pk=unit.building_id)
        messages.error(request, "请修正表单错误。")
    else:
        form = UnitForm(instance=unit)
    return render(request, "community_core/admin_unit_form.html", {"form": form, "unit": unit})


# ---------- 管理员端：房间 ----------


@login_required(login_url="accounts:login_select_role")
def admin_room_list(request):
    """房间列表（可按楼栋/单元筛选）。"""
    denied = _require_admin(request)
    if denied:
        return denied
    from django.db.models import Count
    building_id = request.GET.get("building", "").strip()
    unit_id = request.GET.get("unit", "").strip()
    qs = (
        Room.objects.select_related("unit", "unit__building")
        .annotate(resident_count=Count("residents"))
        .order_by("unit__building__name", "unit__name", "room_no")
    )
    if building_id:
        qs = qs.filter(unit__building_id=building_id)
    if unit_id:
        qs = qs.filter(unit_id=unit_id)
    buildings = Building.objects.all().order_by("name")
    units = Unit.objects.select_related("building").order_by("building__name", "name") if building_id else []
    if building_id:
        units = Unit.objects.filter(building_id=building_id).order_by("name")
    context = {
        "rooms": qs,
        "buildings": buildings,
        "units": units,
        "building_id": building_id,
        "unit_id": unit_id,
    }
    return render(request, "community_core/admin_room_list.html", context)


@login_required(login_url="accounts:login_select_role")
def admin_room_detail(request, pk):
    """房间详情：房间信息、住户列表、添加住户、产权变更。"""
    denied = _require_admin(request)
    if denied:
        return denied
    room = get_object_or_404(
        Room.objects.select_related("unit", "unit__building").prefetch_related("residents", "residents__tags"),
        pk=pk,
    )
    residents = room.residents.all().order_by("-is_householder", "name")
    ownership_changes = room.ownership_changes.select_related("operator").order_by("-changed_at")[:20]

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_resident":
            resident_form = ResidentForm(request.POST)
            if resident_form.is_valid():
                resident = resident_form.save(commit=False)
                resident.room = room
                resident.save()
                resident_form.save_m2m()
                messages.success(request, "住户已添加。")
                return redirect("community_core:admin_room_detail", pk=pk)
            messages.error(request, "请修正表单错误。")
            ownership_form = OwnershipChangeForm(initial={"room": room, "old_owner_name": room.owner_name})
        elif action == "add_ownership":
            ownership_form = OwnershipChangeForm(request.POST)
            if ownership_form.is_valid():
                obj = ownership_form.save(commit=False)
                obj.room = room
                obj.old_owner_name = room.owner_name or ""
                obj.new_owner_name = ownership_form.cleaned_data["new_owner_name"]
                obj.reason = ownership_form.cleaned_data.get("reason") or ""
                obj.operator = request.user
                obj.save()
                room.owner_name = obj.new_owner_name
                room.save(update_fields=["owner_name"])
                messages.success(request, "产权变更已登记。")
                return redirect("community_core:admin_room_detail", pk=pk)
            messages.error(request, "请修正表单错误。")
            resident_form = ResidentForm()
        else:
            resident_form = ResidentForm()
            ownership_form = OwnershipChangeForm(initial={"room": room, "old_owner_name": room.owner_name})
    else:
        resident_form = ResidentForm()
        ownership_form = OwnershipChangeForm(initial={"room": room, "old_owner_name": room.owner_name})
    ownership_form.fields["room"].widget = forms.HiddenInput()
    ownership_form.initial["room"] = room

    context = {
        "room": room,
        "residents": residents,
        "ownership_changes": ownership_changes,
        "resident_form": resident_form,
        "ownership_form": ownership_form,
    }
    return render(request, "community_core/admin_room_detail.html", context)


@login_required(login_url="accounts:login_select_role")
def admin_room_create(request):
    """新增房间。"""
    denied = _require_admin(request)
    if denied:
        return denied
    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "房间已添加。")
            return redirect("community_core:admin_room_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = RoomForm()
    return render(request, "community_core/admin_room_form.html", {"form": form, "is_edit": False})


@login_required(login_url="accounts:login_select_role")
def admin_room_edit(request, pk):
    """编辑房间。"""
    denied = _require_admin(request)
    if denied:
        return denied
    room = get_object_or_404(Room.objects.select_related("unit", "unit__building"), pk=pk)
    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, "房间已更新。")
            return redirect("community_core:admin_room_detail", pk=pk)
        messages.error(request, "请修正表单错误。")
    else:
        form = RoomForm(instance=room)
    return render(request, "community_core/admin_room_form.html", {"form": form, "room": room, "is_edit": True})


# ---------- 管理员端：住户标签 ----------


@login_required(login_url="accounts:login_select_role")
def admin_tag_list(request):
    """住户标签列表。"""
    denied = _require_admin(request)
    if denied:
        return denied
    from django.db.models import Count
    tags = ResidentTag.objects.annotate(resident_count=Count("residents")).order_by("name")
    return render(request, "community_core/admin_tag_list.html", {"tags": tags})


@login_required(login_url="accounts:login_select_role")
def admin_tag_create(request):
    """新增标签。"""
    denied = _require_admin(request)
    if denied:
        return denied
    if request.method == "POST":
        form = ResidentTagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "标签已添加。")
            return redirect("community_core:admin_tag_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = ResidentTagForm()
    return render(request, "community_core/admin_tag_form.html", {"form": form, "is_edit": False})


@login_required(login_url="accounts:login_select_role")
def admin_tag_edit(request, pk):
    """编辑标签。"""
    denied = _require_admin(request)
    if denied:
        return denied
    tag = get_object_or_404(ResidentTag, pk=pk)
    if request.method == "POST":
        form = ResidentTagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, "标签已更新。")
            return redirect("community_core:admin_tag_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = ResidentTagForm(instance=tag)
    return render(request, "community_core/admin_tag_form.html", {"form": form, "tag": tag, "is_edit": True})


@login_required(login_url="accounts:login_select_role")
def admin_tag_delete(request, pk):
    """删除标签（仅当无住户使用时）。"""
    denied = _require_admin(request)
    if denied:
        return denied
    tag = get_object_or_404(ResidentTag, pk=pk)
    if tag.residents.exists():
        messages.warning(request, "该标签已被住户使用，无法删除。")
        return redirect("community_core:admin_tag_list")
    if request.method == "POST":
        tag.delete()
        messages.success(request, "标签已删除。")
        return redirect("community_core:admin_tag_list")
    return render(request, "community_core/admin_tag_confirm_delete.html", {"tag": tag})


# ---------- 管理员端：住户编辑与产权变更 ----------


@login_required(login_url="accounts:login_select_role")
def admin_resident_edit(request, pk):
    """编辑住户信息（状态、标签等）。"""
    denied = _require_admin(request)
    if denied:
        return denied
    resident = get_object_or_404(Resident.objects.select_related("room").prefetch_related("tags"), pk=pk)
    if request.method == "POST":
        form = ResidentForm(request.POST, instance=resident)
        if form.is_valid():
            form.save()
            messages.success(request, "住户信息已更新。")
            return redirect("community_core:admin_resident_detail", pk=pk)
        messages.error(request, "请修正表单错误。")
    else:
        form = ResidentForm(instance=resident)
    return render(request, "community_core/admin_resident_edit.html", {"form": form, "resident": resident})


@login_required(login_url="accounts:login_select_role")
def admin_resident_delete(request, pk):
    """删除住户（谨慎，仅当确实需要时）。"""
    denied = _require_admin(request)
    if denied:
        return denied
    resident = get_object_or_404(Resident.objects.select_related("room"), pk=pk)
    if request.method == "POST":
        room_pk = resident.room_id
        resident.delete()
        messages.success(request, "住户已删除。")
        return redirect("community_core:admin_room_detail", pk=room_pk)
    return render(request, "community_core/admin_resident_confirm_delete.html", {"resident": resident})


@login_required(login_url="accounts:login_select_role")
def admin_ownership_list(request):
    """产权变更记录列表（可按楼栋/房间筛选）。"""
    denied = _require_admin(request)
    if denied:
        return denied
    building_id = request.GET.get("building", "").strip()
    room_id = request.GET.get("room", "").strip()
    qs = OwnershipChange.objects.select_related("room", "room__unit", "room__unit__building", "operator").order_by("-changed_at")
    if building_id:
        qs = qs.filter(room__unit__building_id=building_id)
    if room_id:
        qs = qs.filter(room_id=room_id)
    buildings = Building.objects.all().order_by("name")
    context = {"changes": qs, "buildings": buildings, "building_id": building_id, "room_id": room_id}
    return render(request, "community_core/admin_ownership_list.html", context)


@login_required(login_url="accounts:login_select_role")
def admin_ownership_add(request):
    """登记产权变更（选择房间）。"""
    denied = _require_admin(request)
    if denied:
        return denied
    if request.method == "POST":
        form = OwnershipChangeForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.operator = request.user
            room = obj.room
            obj.old_owner_name = room.owner_name or ""
            obj.save()
            room.owner_name = obj.new_owner_name
            room.save(update_fields=["owner_name"])
            messages.success(request, "产权变更已登记。")
            return redirect("community_core:admin_ownership_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = OwnershipChangeForm()
    return render(request, "community_core/admin_ownership_form.html", {"form": form})


# ---------- 户主端个人中心 ----------


def _require_household(request):
    """仅允许户主访问；返回 None 表示通过，否则返回 redirect 响应。"""
    if not request.user.is_authenticated:
        return redirect("accounts:login_select_role")
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != UserProfile.Role.HOUSEHOLD:
        messages.warning(request, "仅户主可访问个人中心。")
        return redirect("community_core:home")
    return None


def _get_household_room(request):
    """获取当前户主绑定的房间（Room.owner_user=request.user），未绑定返回 None。"""
    return Room.objects.filter(owner_user=request.user).select_related(
        "unit", "unit__building"
    ).first()


@login_required(login_url="accounts:login_select_role")
def household_profile_index(request):
    """个人中心首页（导航）。"""
    denied = _require_household(request)
    if denied:
        return denied
    room = _get_household_room(request)
    context = {"room": room}
    return render(request, "community_core/household_profile_index.html", context)


@login_required(login_url="accounts:login_select_role")
def household_personal_info(request):
    """个人信息查看与编辑。"""
    denied = _require_household(request)
    if denied:
        return denied
    user = request.user
    if request.method == "POST":
        form = HouseholdProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "个人信息已更新。")
            return redirect("community_core:household_personal_info")
        messages.error(request, "请修正以下错误。")
    else:
        form = HouseholdProfileForm(instance=user)
    return render(request, "community_core/household_personal_info.html", {"form": form})


@login_required(login_url="accounts:login_select_role")
def household_family_members(request):
    """家庭成员列表（本户住户）。"""
    denied = _require_household(request)
    if denied:
        return denied
    room = _get_household_room(request)
    if not room:
        return render(
            request,
            "community_core/household_family_members.html",
            {"room": None, "members": []},
        )
    members = room.residents.all().order_by("-is_householder", "name")
    return render(
        request,
        "community_core/household_family_members.html",
        {"room": room, "members": members},
    )


@login_required(login_url="accounts:login_select_role")
def household_housing_info(request):
    """房屋信息（绑定房间的楼栋/单元/房号等）。"""
    denied = _require_household(request)
    if denied:
        return denied
    room = _get_household_room(request)
    return render(
        request,
        "community_core/household_housing_info.html",
        {"room": room},
    )


@login_required(login_url="accounts:login_select_role")
def household_change_password(request):
    """修改密码。"""
    denied = _require_household(request)
    if denied:
        return denied
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "密码已修改，请使用新密码重新登录。")
            return redirect("community_core:household_profile_index")
        messages.error(request, "请修正以下错误。")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "community_core/household_change_password.html", {"form": form})


@login_required(login_url="accounts:login_select_role")
def household_messages(request):
    """消息通知列表。"""
    denied = _require_household(request)
    if denied:
        return denied
    message_list = UserMessage.objects.filter(user=request.user).order_by("-created_at")[:50]
    return render(
        request,
        "community_core/household_messages.html",
        {"message_list": message_list},
    )


@login_required(login_url="accounts:login_select_role")
def household_feedback(request):
    """意见反馈：提交与历史列表。"""
    denied = _require_household(request)
    if denied:
        return denied
    if request.method == "POST":
        form = HouseholdFeedbackForm(request.POST)
        if form.is_valid():
            fb = form.save(commit=False)
            fb.user = request.user
            fb.save()
            messages.success(request, "反馈已提交，感谢您的意见。")
            return redirect("community_core:household_feedback")
        messages.error(request, "请修正以下错误。")
    else:
        form = HouseholdFeedbackForm()
    feedback_list = UserFeedback.objects.filter(user=request.user).order_by("-created_at")[:30]
    return render(
        request,
        "community_core/household_feedback.html",
        {"form": form, "feedback_list": feedback_list},
    )
