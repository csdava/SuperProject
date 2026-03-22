from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from urllib.parse import urlencode
from django.db import models
from django.http import JsonResponse
from django.core.paginator import Paginator

from .forms import (
    RegisterForm,
    LoginForm,
    AdminUserProfileForm,
    SystemConfigForm,
    HouseholdComfortSettingForm,
)
from .models import UserProfile, LoginLog, AuditLog, SystemConfig, HouseholdComfortSetting

# 工单待处理数（管理台展示）
try:
    from repair.models import RepairOrder
except ImportError:
    RepairOrder = None


def _get_or_create_profile(user):
    """确保用户有 profile（如超级用户首次登录）。"""
    profile = getattr(user, "profile", None)
    if profile is None:
        if user.is_superuser:
            profile = UserProfile.objects.create(
                user=user,
                role=UserProfile.Role.ADMIN,
                is_approved=True,
            )
        else:
            profile = UserProfile.objects.create(
                user=user,
                role=UserProfile.Role.HOUSEHOLD,
                is_approved=False,
            )
    return profile


def register(request):
    """注册：仅户主、维修人员；需管理员审批后才能登录。"""
    if request.user.is_authenticated:
        return redirect("community_core:home")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "注册成功。您的账号需经管理员审批通过后才能登录，请耐心等待。",
            )
            return redirect("accounts:login_select_role")
        else:
            messages.error(request, "请修正以下错误后重试。")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def login_select_role(request):
    """登录第一步：选择身份（户主 / 管理员 / 维修人员）。"""
    if request.user.is_authenticated:
        return redirect("community_core:home")
    if request.method == "POST":
        role = request.POST.get("role")
        if role in (UserProfile.Role.HOUSEHOLD, UserProfile.Role.ADMIN, UserProfile.Role.MAINTENANCE):
            request.session["login_role"] = role
            return redirect("accounts:login_form")
        messages.error(request, "请选择有效身份。")
    return render(request, "accounts/login_select_role.html")


def login_form(request):
    """登录第二步：输入用户名、密码；校验身份与审批状态。"""
    if request.user.is_authenticated:
        return redirect("community_core:home")
    role = request.session.get("login_role")
    if not role or role not in (
        UserProfile.Role.HOUSEHOLD,
        UserProfile.Role.ADMIN,
        UserProfile.Role.MAINTENANCE,
    ):
        messages.warning(request, "请先选择登录身份。")
        return redirect("accounts:login_select_role")

    def _client_ip(req):
        raw = req.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or req.META.get("REMOTE_ADDR") or ""
        return raw or None  # GenericIPAddressField 需要 None 而非空串

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        username_attempted = (request.POST.get("username") or "").strip()[:150]
        if form.is_valid():
            user = form.get_user()
            profile = _get_or_create_profile(user)
            if profile.role != role:
                LoginLog.objects.create(user=user, username_attempted=username_attempted or user.username, success=False, ip_address=_client_ip(request))
                messages.error(
                    request,
                    f"您选择的身份与账号不符。该账号身份为：{profile.get_role_display()}。",
                )
            elif not profile.can_login:
                LoginLog.objects.create(user=user, username_attempted=username_attempted or user.username, success=False, ip_address=_client_ip(request))
                messages.error(
                    request,
                    "您的账号尚未通过管理员审批，暂无法登录。请等待审批或联系物业。",
                )
            else:
                LoginLog.objects.create(user=user, username_attempted=username_attempted or user.username, success=True, ip_address=_client_ip(request))
                auth_login(request, user)
                request.session["login_role"] = role
                messages.success(request, f"欢迎，{user.username}。")
                return redirect(_redirect_by_role(role))
        else:
            LoginLog.objects.create(username_attempted=username_attempted, success=False, ip_address=_client_ip(request))
            messages.error(request, "用户名或密码错误，请重试。")
    else:
        form = LoginForm()
    role_display = dict(UserProfile.Role.choices).get(role, role)
    return render(
        request,
        "accounts/login_form.html",
        {"form": form, "role": role, "role_display": role_display},
    )


def _redirect_by_role(role):
    """按身份返回首页或对应工作台。"""
    if role == UserProfile.Role.ADMIN:
        return "accounts:dashboard_admin"
    if role == UserProfile.Role.MAINTENANCE:
        return "accounts:dashboard_maintenance"
    return "accounts:dashboard_household"


def logout_view(request):
    """退出登录。"""
    auth_logout(request)
    if "login_role" in request.session:
        del request.session["login_role"]
    messages.info(request, "您已退出登录。")
    return redirect("community_core:home")


@login_required(login_url="accounts:login_select_role")
def dashboard_household(request):
    """户主工作台：温湿度提醒 + 快捷入口。"""
    profile = _get_or_create_profile(request.user)
    if profile.role != UserProfile.Role.HOUSEHOLD:
        messages.warning(request, "您当前身份无权访问户主工作台。")
        return redirect(_redirect_by_role(profile.role))

    comfort, _created = HouseholdComfortSetting.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = HouseholdComfortSettingForm(request.POST, instance=comfort)
        if form.is_valid():
            form.save()
            messages.success(request, "已保存温湿度舒适范围。")
            return redirect("accounts:dashboard_household")
    else:
        form = HouseholdComfortSettingForm(instance=comfort)

    # 当前温湿度数据：优先从系统参数读取；项目未对接硬件时可用默认值演示。
    def _get_system_float(key: str, default: float) -> float:
        try:
            obj = SystemConfig.objects.get(key=key)
            return float((obj.value or "").strip())
        except Exception:
            return default

    current_temp = _get_system_float("current_temperature_c", default=26.0)
    current_humidity = _get_system_float("current_humidity_rh", default=55.0)

    # 根据用户设置阈值生成提醒文案
    if current_temp > comfort.temp_max:
        temp_advice = "气温较高，小心中暑"
    elif current_temp < comfort.temp_min:
        temp_advice = "气温较低，注意保暖"
    else:
        temp_advice = "气温适宜，今天是舒适的一天"

    if current_humidity > comfort.humidity_max:
        humidity_advice = "今天可能降雨，带把伞吧"
    elif current_humidity < comfort.humidity_min:
        humidity_advice = "今天过于干燥，注意补水"
    else:
        humidity_advice = "湿度适宜，今天是平静的一天"

    context = {
        "comfort": comfort,
        "form": form,
        "current_temp": current_temp,
        "current_humidity": current_humidity,
        "temp_advice": temp_advice,
        "humidity_advice": humidity_advice,
    }
    return render(request, "accounts/dashboard_household.html", context)


@login_required(login_url="accounts:login_select_role")
def household_current_sensor(request):
    """户主工作台轮询接口：返回最新温湿度 + 提醒文案。"""
    profile = _get_or_create_profile(request.user)
    if profile.role != UserProfile.Role.HOUSEHOLD:
        return JsonResponse({"error": "forbidden"}, status=403)

    comfort, _created = HouseholdComfortSetting.objects.get_or_create(user=request.user)

    def _get_system_float(key: str, default: float) -> float:
        try:
            obj = SystemConfig.objects.get(key=key)
            return float((obj.value or "").strip())
        except Exception:
            return default

    current_temp = _get_system_float("current_temperature_c", default=26.0)
    current_humidity = _get_system_float("current_humidity_rh", default=55.0)

    # 根据用户设置阈值生成提醒文案
    if current_temp > comfort.temp_max:
        temp_advice = "气温较高，小心中暑"
    elif current_temp < comfort.temp_min:
        temp_advice = "气温较低，注意保暖"
    else:
        temp_advice = "气温适宜，今天是舒适的一天"

    if current_humidity > comfort.humidity_max:
        humidity_advice = "今天可能降雨，带把伞吧"
    elif current_humidity < comfort.humidity_min:
        humidity_advice = "今天过于干燥，注意补水"
    else:
        humidity_advice = "湿度适宜，今天是平静的一天"

    return JsonResponse(
        {
            "current_temp": round(current_temp, 1),
            "current_humidity": round(current_humidity, 1),
            "temp_advice": temp_advice,
            "humidity_advice": humidity_advice,
            # 返回区间，便于前端展示（一般不会频繁变化）
            "comfort": {
                "temp_min": float(comfort.temp_min),
                "temp_max": float(comfort.temp_max),
                "humidity_min": float(comfort.humidity_min),
                "humidity_max": float(comfort.humidity_max),
            },
        }
    )


@login_required(login_url="accounts:login_select_role")
def dashboard_maintenance(request):
    """维修人员工作台（占位）。"""
    profile = _get_or_create_profile(request.user)
    if profile.role != UserProfile.Role.MAINTENANCE:
        messages.warning(request, "您当前身份无权访问维修人员工作台。")
        return redirect(_redirect_by_role(profile.role))
    return render(request, "accounts/dashboard_maintenance.html")


@login_required(login_url="accounts:login_select_role")
def dashboard_admin(request):
    """管理员工作台：今日待办 / 数据看板 / 快捷操作。"""
    profile = _get_or_create_profile(request.user)
    is_admin = profile.role == UserProfile.Role.ADMIN or request.user.is_superuser
    if not is_admin:
        messages.warning(request, "您当前身份无权访问管理后台。")
        return redirect(_redirect_by_role(profile.role))
    # 今日与近期数据
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    pending_approvals = UserProfile.objects.filter(is_approved=False).count()
    total_users = User.objects.count()
    approved_users = UserProfile.objects.filter(is_approved=True).count()
    role_stats = (
        UserProfile.objects.values("role")
        .order_by("role")
        .annotate(count=models.Count("id"))
    )
    pending_orders = 0
    if RepairOrder is not None:
        pending_orders = RepairOrder.objects.filter(
            status__in=(RepairOrder.Status.PENDING, RepairOrder.Status.ASSIGNED)
        ).count()

    context = {
        "pending_approvals": pending_approvals,
        "total_users": total_users,
        "approved_users": approved_users,
        "today": today_start.date(),
        "role_stats": role_stats,
        "pending_orders": pending_orders,
    }
    return render(request, "accounts/dashboard_admin.html", context)


def _require_admin(request):
    """要求管理员身份，否则返回重定向。"""
    if not request.user.is_authenticated:
        return redirect("accounts:login_select_role")
    profile = _get_or_create_profile(request.user)
    if profile.role != UserProfile.Role.ADMIN and not request.user.is_superuser:
        messages.warning(request, "您当前身份无权访问该页面。")
        return redirect(_redirect_by_role(profile.role))
    return None


@login_required(login_url="accounts:login_select_role")
def admin_user_list(request):
    """系统管理 - 用户账号管理：列表、按身份筛选、搜索、批量审批。"""
    r = _require_admin(request)
    if r is not None:
        return r

    # 批量通过审批
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "bulk_approve":
            user_ids = request.POST.getlist("user_ids")
            if not user_ids:
                messages.warning(request, "请先勾选要审批的用户。")
            else:
                users = User.objects.filter(id__in=user_ids).select_related("profile")
                approved_count = 0
                for user in users:
                    profile = _get_or_create_profile(user)
                    if not profile.is_approved:
                        profile.is_approved = True
                        profile.save(update_fields=["is_approved"])
                        approved_count += 1
                        AuditLog.objects.create(
                            user=request.user,
                            action="用户审批",
                            message=f"批量审批：用户 {user.username} 通过",
                        )
                if approved_count:
                    messages.success(request, f"已批量通过 {approved_count} 个用户的审批。")
                else:
                    messages.info(request, "所选用户均已审批，无需重复操作。")
        # 保留当前筛选条件与搜索关键字
        params = {}
        role_filter_post = request.POST.get("role") or ""
        is_approved_filter_post = request.POST.get("is_approved") or ""
        search_post = (request.POST.get("q") or "").strip()
        if role_filter_post:
            params["role"] = role_filter_post
        if is_approved_filter_post in ("0", "1"):
            params["is_approved"] = is_approved_filter_post
        if search_post:
            params["q"] = search_post
        redirect_url = reverse("accounts:admin_user_list")
        if params:
            redirect_url = f"{redirect_url}?{urlencode(params)}"
        return redirect(redirect_url)

    # 列表筛选与搜索（GET）
    qs = User.objects.all().select_related("profile").order_by("-id")
    role_filter = request.GET.get("role")
    if role_filter and role_filter in dict(UserProfile.Role.choices):
        qs = qs.filter(profile__role=role_filter)
    is_approved_filter = request.GET.get("is_approved")
    if is_approved_filter == "0":
        qs = qs.filter(profile__is_approved=False)
    elif is_approved_filter == "1":
        qs = qs.filter(profile__is_approved=True)
    search = (request.GET.get("q") or "").strip()
    if search:
        qs = qs.filter(username__icontains=search)
    paginator = Paginator(qs, 20)
    page = request.GET.get("page", 1)
    page_obj = paginator.get_page(page)
    context = {
        "page_obj": page_obj,
        "role_choices": UserProfile.Role.choices,
        "role_filter": role_filter,
        "is_approved_filter": is_approved_filter,
        "q": search,
    }
    return render(request, "accounts/admin_user_list.html", context)


@login_required(login_url="accounts:login_select_role")
def admin_user_edit(request, user_id):
    """系统管理 - 用户账号管理：修改身份、审批状态，并记录操作日志。"""
    r = _require_admin(request)
    if r is not None:
        return r
    user = get_object_or_404(User, pk=user_id)
    profile = _get_or_create_profile(user)
    initial = {"role": profile.role, "is_approved": profile.is_approved}
    if request.method == "POST":
        form = AdminUserProfileForm(request.POST)
        if form.is_valid():
            old_role, old_approved = profile.role, profile.is_approved
            profile.role = form.cleaned_data["role"]
            profile.is_approved = form.cleaned_data["is_approved"]
            profile.save()
            if profile.role == UserProfile.Role.ADMIN:
                user.is_staff = True
                user.save(update_fields=["is_staff"])
            msg_parts = []
            if old_approved != profile.is_approved:
                msg_parts.append("审批" if profile.is_approved else "拒绝")
                AuditLog.objects.create(
                    user=request.user,
                    action="用户审批",
                    message=f"用户 {user.username}：{'通过' if profile.is_approved else '拒绝'}",
                )
            if old_role != profile.role:
                msg_parts.append("修改角色")
                AuditLog.objects.create(
                    user=request.user,
                    action="修改角色",
                    message=f"用户 {user.username} 身份由 {dict(UserProfile.Role.choices).get(old_role, old_role)} 改为 {profile.get_role_display()}",
                )
            if msg_parts:
                messages.success(request, "已保存并记录操作日志。")
            else:
                messages.success(request, "已保存。")
            return redirect("accounts:admin_user_list")
    else:
        form = AdminUserProfileForm(initial=initial)
    context = {"form": form, "edit_user": user, "profile": profile}
    return render(request, "accounts/admin_user_edit.html", context)


@login_required(login_url="accounts:login_select_role")
def admin_login_log_list(request):
    """系统管理 - 登录日志列表。"""
    r = _require_admin(request)
    if r is not None:
        return r
    qs = LoginLog.objects.select_related("user").order_by("-created_at")
    success_filter = request.GET.get("success")
    if success_filter == "1":
        qs = qs.filter(success=True)
    elif success_filter == "0":
        qs = qs.filter(success=False)
    search = (request.GET.get("q") or "").strip()
    if search:
        qs = qs.filter(username_attempted__icontains=search)
    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    context = {"page_obj": page_obj, "success_filter": success_filter, "q": search}
    return render(request, "accounts/admin_login_log_list.html", context)


@login_required(login_url="accounts:login_select_role")
def admin_audit_log_list(request):
    """系统管理 - 操作日志列表。"""
    r = _require_admin(request)
    if r is not None:
        return r
    qs = AuditLog.objects.select_related("user").order_by("-created_at")
    action_filter = request.GET.get("action", "").strip()
    if action_filter:
        qs = qs.filter(action=action_filter)
    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    actions = list(AuditLog.objects.values_list("action", flat=True).distinct().order_by("action"))
    context = {"page_obj": page_obj, "action_filter": action_filter, "actions": actions}
    return render(request, "accounts/admin_audit_log_list.html", context)


@login_required(login_url="accounts:login_select_role")
def admin_system_config_list(request):
    """系统管理 - 基础参数配置列表。"""
    r = _require_admin(request)
    if r is not None:
        return r
    items = SystemConfig.objects.all().order_by("key")
    context = {"config_list": items}
    return render(request, "accounts/admin_system_config_list.html", context)


@login_required(login_url="accounts:login_select_role")
def admin_system_config_edit(request, pk):
    """系统管理 - 基础参数配置编辑。"""
    r = _require_admin(request)
    if r is not None:
        return r
    obj = get_object_or_404(SystemConfig, pk=pk)
    if request.method == "POST":
        form = SystemConfigForm(request.POST, instance=obj, edit_key=obj.key)
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                user=request.user,
                action="参数配置",
                message=f"修改参数 {obj.key}",
            )
            messages.success(request, "已保存。")
            return redirect("accounts:admin_system_config_list")
    else:
        form = SystemConfigForm(instance=obj, edit_key=obj.key)
    context = {"form": form, "config": obj}
    return render(request, "accounts/admin_system_config_edit.html", context)


@login_required(login_url="accounts:login_select_role")
def admin_system_config_create(request):
    """系统管理 - 基础参数配置新增。"""
    r = _require_admin(request)
    if r is not None:
        return r
    if request.method == "POST":
        form = SystemConfigForm(request.POST)
        if form.is_valid():
            obj = form.save()
            AuditLog.objects.create(
                user=request.user,
                action="参数配置",
                message=f"新增参数 {obj.key}",
            )
            messages.success(request, "已添加。")
            return redirect("accounts:admin_system_config_list")
    else:
        form = SystemConfigForm()
    context = {"form": form}
    return render(request, "accounts/admin_system_config_edit.html", context)
