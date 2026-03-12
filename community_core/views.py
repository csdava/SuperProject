from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from accounts.models import UserProfile
from .models import Resident, Room, Building


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
