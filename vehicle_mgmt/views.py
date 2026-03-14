from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.models import UserProfile
from .models import Vehicle, ParkingSpace, TempParkingRequest, ViolationRecord
from .forms import VehicleForm, TempParkingRequestForm


def _require_household(request):
    """仅户主可访问。"""
    if not request.user.is_authenticated:
        return redirect("accounts:login_select_role")
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != UserProfile.Role.HOUSEHOLD:
        messages.warning(request, "仅户主可使用车辆管理。")
        return redirect("community_core:home")
    return None


@login_required(login_url="accounts:login_select_role")
def household_vehicle_list(request):
    """我的车辆列表。"""
    denied = _require_household(request)
    if denied:
        return denied
    vehicles = Vehicle.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "vehicle_mgmt/household_vehicle_list.html", {"vehicles": vehicles})


@login_required(login_url="accounts:login_select_role")
def household_vehicle_create(request):
    """登记车辆。"""
    denied = _require_household(request)
    if denied:
        return denied
    if request.method == "POST":
        form = VehicleForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, "车辆已登记。")
            return redirect("vehicle_mgmt:household_vehicle_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = VehicleForm()
    return render(request, "vehicle_mgmt/household_vehicle_form.html", {"form": form, "is_edit": False})


@login_required(login_url="accounts:login_select_role")
def household_vehicle_edit(request, pk):
    """编辑车辆。"""
    denied = _require_household(request)
    if denied:
        return denied
    vehicle = get_object_or_404(Vehicle, pk=pk, user=request.user)
    if request.method == "POST":
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, "车辆信息已更新。")
            return redirect("vehicle_mgmt:household_vehicle_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = VehicleForm(instance=vehicle)
    return render(request, "vehicle_mgmt/household_vehicle_form.html", {"form": form, "vehicle": vehicle, "is_edit": True})


@login_required(login_url="accounts:login_select_role")
def household_vehicle_delete(request, pk):
    """删除车辆登记。"""
    denied = _require_household(request)
    if denied:
        return denied
    vehicle = get_object_or_404(Vehicle, pk=pk, user=request.user)
    if request.method == "POST":
        vehicle.delete()
        messages.success(request, "已删除该车辆登记。")
        return redirect("vehicle_mgmt:household_vehicle_list")
    return render(request, "vehicle_mgmt/household_vehicle_confirm_delete.html", {"vehicle": vehicle})


@login_required(login_url="accounts:login_select_role")
def household_parking_list(request):
    """车位状态（全部车位列表，只读）。"""
    denied = _require_household(request)
    if denied:
        return denied
    space_type = request.GET.get("type", "").strip()
    qs = ParkingSpace.objects.all().order_by("zone", "code")
    if space_type and space_type in dict(ParkingSpace.SpaceType.choices):
        qs = qs.filter(space_type=space_type)
    return render(
        request,
        "vehicle_mgmt/household_parking_list.html",
        {"spaces": qs, "type_filter": space_type},
    )


@login_required(login_url="accounts:login_select_role")
def household_temp_request_list(request):
    """临停申请列表。"""
    denied = _require_household(request)
    if denied:
        return denied
    requests = TempParkingRequest.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "vehicle_mgmt/household_temp_request_list.html", {"requests": requests})


@login_required(login_url="accounts:login_select_role")
def household_temp_request_create(request):
    """提交临停申请。"""
    denied = _require_household(request)
    if denied:
        return denied
    if request.method == "POST":
        form = TempParkingRequestForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, "临停申请已提交，请等待审批。")
            return redirect("vehicle_mgmt:household_temp_request_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = TempParkingRequestForm()
    return render(request, "vehicle_mgmt/household_temp_request_form.html", {"form": form})


@login_required(login_url="accounts:login_select_role")
def household_violation_list(request):
    """违规记录（本人关联的违规）。"""
    denied = _require_household(request)
    if denied:
        return denied
    records = ViolationRecord.objects.filter(user=request.user).order_by("-occurred_at", "-created_at")
    return render(request, "vehicle_mgmt/household_violation_list.html", {"records": records})
