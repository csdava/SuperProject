from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q

from django import forms
from django.contrib.auth import get_user_model

from accounts.models import UserProfile
from django.utils import timezone

from .models import (
    Resident,
    Room,
    Building,
    Unit,
    ResidentTag,
    OwnershipChange,
    UserMessage,
    UserFeedback,
    Announcement,
    CommunityActivity,
    ActivityRegistration,
    NeighborhoodPost,
    ServiceBooking,
    ParcelRecord,
    LostItemReport,
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
    AnnouncementForm,
    CommunityActivityForm,
    NeighborhoodPostForm,
    ServiceBookingForm,
    ParcelRecordForm,
    LostItemReportForm,
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


# ---------- 管理员端：社区服务（公告、活动） ----------


@login_required(login_url="accounts:login_select_role")
def admin_announcement_list(request):
    """公告列表（筛选：全部/已发布/草稿）。"""
    denied = _require_admin(request)
    if denied:
        return denied
    status_filter = request.GET.get("status", "").strip()
    qs = Announcement.objects.all().order_by("-is_pinned", "-published_at", "-created_at")
    if status_filter == "published":
        qs = qs.filter(is_published=True)
    elif status_filter == "draft":
        qs = qs.filter(is_published=False)
    return render(
        request,
        "community_core/admin_announcement_list.html",
        {"announcements": qs, "status_filter": status_filter},
    )


@login_required(login_url="accounts:login_select_role")
def admin_announcement_create(request):
    """发布公告。"""
    denied = _require_admin(request)
    if denied:
        return denied
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            if obj.is_published:
                obj.published_at = timezone.now()
            obj.save()
            messages.success(request, "公告已保存。")
            return redirect("community_core:admin_announcement_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = AnnouncementForm()
    return render(request, "community_core/admin_announcement_form.html", {"form": form, "is_edit": False})


@login_required(login_url="accounts:login_select_role")
def admin_announcement_edit(request, pk):
    """编辑公告。"""
    denied = _require_admin(request)
    if denied:
        return denied
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == "POST":
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.is_published and not announcement.published_at:
                obj.published_at = timezone.now()
            obj.save()
            messages.success(request, "公告已更新。")
            return redirect("community_core:admin_announcement_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = AnnouncementForm(instance=announcement)
    return render(
        request,
        "community_core/admin_announcement_form.html",
        {"form": form, "announcement": announcement, "is_edit": True},
    )


@login_required(login_url="accounts:login_select_role")
def admin_announcement_delete(request, pk):
    """删除公告。"""
    denied = _require_admin(request)
    if denied:
        return denied
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == "POST":
        announcement.delete()
        messages.success(request, "公告已删除。")
        return redirect("community_core:admin_announcement_list")
    return render(request, "community_core/admin_announcement_confirm_delete.html", {"announcement": announcement})


@login_required(login_url="accounts:login_select_role")
def admin_announcement_toggle_pin(request, pk):
    """置顶/取消置顶。"""
    denied = _require_admin(request)
    if denied:
        return denied
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.is_pinned = not announcement.is_pinned
    announcement.save(update_fields=["is_pinned", "updated_at"])
    messages.success(request, "已取消置顶。" if not announcement.is_pinned else "已置顶。")
    return redirect("community_core:admin_announcement_list")


@login_required(login_url="accounts:login_select_role")
def admin_activity_list(request):
    """社区活动列表（可按状态筛选）。"""
    denied = _require_admin(request)
    if denied:
        return denied
    status_filter = request.GET.get("status", "").strip()
    qs = CommunityActivity.objects.all().order_by("-start_time")
    if status_filter:
        qs = qs.filter(status=status_filter)
    from django.db.models import Count
    qs = qs.annotate(reg_count=Count("registrations", filter=Q(registrations__status="registered")))
    return render(
        request,
        "community_core/admin_activity_list.html",
        {"activities": qs, "status_filter": status_filter},
    )


@login_required(login_url="accounts:login_select_role")
def admin_activity_create(request):
    """发布活动。"""
    denied = _require_admin(request)
    if denied:
        return denied
    if request.method == "POST":
        form = CommunityActivityForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, "活动已保存。")
            return redirect("community_core:admin_activity_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = CommunityActivityForm()
    return render(request, "community_core/admin_activity_form.html", {"form": form, "is_edit": False})


@login_required(login_url="accounts:login_select_role")
def admin_activity_edit(request, pk):
    """编辑活动。"""
    denied = _require_admin(request)
    if denied:
        return denied
    activity = get_object_or_404(CommunityActivity, pk=pk)
    if request.method == "POST":
        form = CommunityActivityForm(request.POST, instance=activity)
        if form.is_valid():
            form.save()
            messages.success(request, "活动已更新。")
            return redirect("community_core:admin_activity_detail", pk=pk)
        messages.error(request, "请修正表单错误。")
    else:
        form = CommunityActivityForm(instance=activity)
    return render(
        request,
        "community_core/admin_activity_form.html",
        {"form": form, "activity": activity, "is_edit": True},
    )


@login_required(login_url="accounts:login_select_role")
def admin_activity_detail(request, pk):
    """活动详情与报名管理（报名名单、活动总结）。"""
    denied = _require_admin(request)
    if denied:
        return denied
    activity = get_object_or_404(
        CommunityActivity.objects.prefetch_related("registrations__user"),
        pk=pk,
    )
    registrations = activity.registrations.filter(status=ActivityRegistration.RegStatus.REGISTERED).select_related("user")
    return render(
        request,
        "community_core/admin_activity_detail.html",
        {"activity": activity, "registrations": registrations},
    )


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


# ---------- 户主端：社区公告与活动 ----------


@login_required(login_url="accounts:login_select_role")
def household_announcement_list(request):
    """户主查看已发布公告列表。"""
    denied = _require_household(request)
    if denied:
        return denied
    announcements = Announcement.objects.filter(is_published=True).order_by("-is_pinned", "-published_at", "-created_at")[:50]
    return render(request, "community_core/household_announcement_list.html", {"announcements": announcements})


@login_required(login_url="accounts:login_select_role")
def household_announcement_detail(request, pk):
    """户主查看公告详情。"""
    denied = _require_household(request)
    if denied:
        return denied
    announcement = get_object_or_404(Announcement, pk=pk, is_published=True)
    return render(request, "community_core/household_announcement_detail.html", {"announcement": announcement})


@login_required(login_url="accounts:login_select_role")
def household_activity_list(request):
    """户主查看已发布/进行中的活动列表。"""
    denied = _require_household(request)
    if denied:
        return denied
    now = timezone.now()
    activities = (
        CommunityActivity.objects.filter(status=CommunityActivity.Status.PUBLISHED)
        .filter(end_time__gte=now)
        .order_by("start_time")[:30]
    )
    return render(request, "community_core/household_activity_list.html", {"activities": activities})


@login_required(login_url="accounts:login_select_role")
def household_activity_detail(request, pk):
    """户主查看活动详情，可报名/取消报名。"""
    denied = _require_household(request)
    if denied:
        return denied
    activity = get_object_or_404(CommunityActivity, pk=pk, status=CommunityActivity.Status.PUBLISHED)
    registration = activity.registrations.filter(user=request.user).first()
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "register" and not registration:
            if activity.max_participants:
                from django.db.models import Count
                current = activity.registrations.filter(status=ActivityRegistration.RegStatus.REGISTERED).count()
                if current >= activity.max_participants:
                    messages.warning(request, "报名人数已满。")
                    return redirect("community_core:household_activity_detail", pk=pk)
            ActivityRegistration.objects.create(activity=activity, user=request.user)
            messages.success(request, "报名成功。")
            return redirect("community_core:household_activity_detail", pk=pk)
        if action == "cancel" and registration and registration.status == ActivityRegistration.RegStatus.REGISTERED:
            registration.status = ActivityRegistration.RegStatus.CANCELLED
            registration.save(update_fields=["status"])
            messages.success(request, "已取消报名。")
            return redirect("community_core:household_activity_detail", pk=pk)
    registration = activity.registrations.filter(user=request.user).first()
    return render(
        request,
        "community_core/household_activity_detail.html",
        {"activity": activity, "registration": registration},
    )


# ---------- 户主端：邻里圈 ----------


@login_required(login_url="accounts:login_select_role")
def household_neighborhood_feed(request):
    """邻里圈动态流：全部/动态/二手/互助，仅显示正常状态。"""
    denied = _require_household(request)
    if denied:
        return denied
    post_type = request.GET.get("type", "").strip()
    qs = NeighborhoodPost.objects.filter(status=NeighborhoodPost.PostStatus.NORMAL).select_related("user").order_by("-created_at")
    if post_type and post_type in dict(NeighborhoodPost.PostType.choices):
        qs = qs.filter(post_type=post_type)
    qs = qs[:80]
    return render(
        request,
        "community_core/household_neighborhood_feed.html",
        {"posts": qs, "type_filter": post_type},
    )


@login_required(login_url="accounts:login_select_role")
def household_neighborhood_create(request):
    """发布动态/二手/互助。"""
    denied = _require_household(request)
    if denied:
        return denied
    if request.method == "POST":
        form = NeighborhoodPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            messages.success(request, "发布成功。")
            return redirect("community_core:household_neighborhood_feed")
        messages.error(request, "请修正表单错误。")
    else:
        form = NeighborhoodPostForm()
    return render(request, "community_core/household_neighborhood_form.html", {"form": form})


@login_required(login_url="accounts:login_select_role")
def household_neighborhood_detail(request, pk):
    """帖子详情（仅正常状态可见）。"""
    denied = _require_household(request)
    if denied:
        return denied
    post = get_object_or_404(NeighborhoodPost.objects.select_related("user"), pk=pk, status=NeighborhoodPost.PostStatus.NORMAL)
    return render(request, "community_core/household_neighborhood_detail.html", {"post": post})


@login_required(login_url="accounts:login_select_role")
def household_neighborhood_my_posts(request):
    """我的发布：本人所有帖子，可删除。"""
    denied = _require_household(request)
    if denied:
        return denied
    posts = NeighborhoodPost.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "community_core/household_neighborhood_my_posts.html", {"posts": posts})


@login_required(login_url="accounts:login_select_role")
def household_neighborhood_delete(request, pk):
    """删除本人发布的帖子。"""
    denied = _require_household(request)
    if denied:
        return denied
    post = get_object_or_404(NeighborhoodPost, pk=pk, user=request.user)
    if request.method == "POST":
        post.delete()
        messages.success(request, "已删除。")
        return redirect("community_core:household_neighborhood_my_posts")
    return render(request, "community_core/household_neighborhood_confirm_delete.html", {"post": post})


# ---------- 户主端：社区服务（家政预约、快递代收、物品报失） ----------


@login_required(login_url="accounts:login_select_role")
def household_service_booking_list(request):
    """我的家政预约列表。"""
    denied = _require_household(request)
    if denied:
        return denied
    bookings = ServiceBooking.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "community_core/household_service_booking_list.html", {"bookings": bookings})


@login_required(login_url="accounts:login_select_role")
def household_service_booking_create(request):
    """提交家政预约。"""
    denied = _require_household(request)
    if denied:
        return denied
    if request.method == "POST":
        form = ServiceBookingForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, "预约已提交，请等待物业联系。")
            return redirect("community_core:household_service_booking_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = ServiceBookingForm()
    return render(request, "community_core/household_service_booking_form.html", {"form": form})


@login_required(login_url="accounts:login_select_role")
def household_parcel_list(request):
    """我的快递代收记录。"""
    denied = _require_household(request)
    if denied:
        return denied
    parcels = ParcelRecord.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "community_core/household_parcel_list.html", {"parcels": parcels})


@login_required(login_url="accounts:login_select_role")
def household_parcel_create(request):
    """登记快递代收。"""
    denied = _require_household(request)
    if denied:
        return denied
    if request.method == "POST":
        form = ParcelRecordForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, "已登记，取件后可在列表中标记已取。")
            return redirect("community_core:household_parcel_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = ParcelRecordForm()
    return render(request, "community_core/household_parcel_form.html", {"form": form})


@login_required(login_url="accounts:login_select_role")
def household_parcel_mark_taken(request, pk):
    """标记快递已取（仅接受 POST）。"""
    denied = _require_household(request)
    if denied:
        return denied
    if request.method != "POST":
        return redirect("community_core:household_parcel_list")
    parcel = get_object_or_404(ParcelRecord, pk=pk, user=request.user)
    if parcel.status == ParcelRecord.Status.PENDING:
        parcel.status = ParcelRecord.Status.TAKEN
        parcel.taken_at = timezone.now()
        parcel.save(update_fields=["status", "taken_at"])
        messages.success(request, "已标记为已取。")
    return redirect("community_core:household_parcel_list")


@login_required(login_url="accounts:login_select_role")
def household_lost_report_list(request):
    """我的物品报失列表。"""
    denied = _require_household(request)
    if denied:
        return denied
    reports = LostItemReport.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "community_core/household_lost_report_list.html", {"reports": reports})


@login_required(login_url="accounts:login_select_role")
def household_lost_report_create(request):
    """提交物品报失。"""
    denied = _require_household(request)
    if denied:
        return denied
    if request.method == "POST":
        form = LostItemReportForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, "报失已提交，如有找到会联系您。")
            return redirect("community_core:household_lost_report_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = LostItemReportForm()
    return render(request, "community_core/household_lost_report_form.html", {"form": form})
