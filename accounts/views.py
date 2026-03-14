from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models

from .forms import RegisterForm, LoginForm
from .models import UserProfile

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

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            profile = _get_or_create_profile(user)
            if profile.role != role:
                messages.error(
                    request,
                    f"您选择的身份与账号不符。该账号身份为：{profile.get_role_display()}。",
                )
            elif not profile.can_login:
                messages.error(
                    request,
                    "您的账号尚未通过管理员审批，暂无法登录。请等待审批或联系物业。",
                )
            else:
                auth_login(request, user)
                request.session["login_role"] = role
                messages.success(request, f"欢迎，{user.username}。")
                return redirect(_redirect_by_role(role))
        else:
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
    """户主工作台（占位）。"""
    profile = _get_or_create_profile(request.user)
    if profile.role != UserProfile.Role.HOUSEHOLD:
        messages.warning(request, "您当前身份无权访问户主工作台。")
        return redirect(_redirect_by_role(profile.role))
    return render(request, "accounts/dashboard_household.html")


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
