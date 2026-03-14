from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q

from django.contrib.auth import get_user_model

from accounts.models import UserProfile
from .models import (
    RepairOrder,
    RepairEvaluation,
    MaintenancePreference,
    RepairProgressLog,
    RepairPartUsage,
    MaintenanceSchedule,
    MaintenancePayslip,
    MaintenanceCert,
    TrainingMaterial,
    InspectionTask,
    InspectionCheckIn,
    InspectionAbnormality,
)
from .forms import (
    CreateRepairForm,
    EvaluationForm,
    MaintenanceOrderUpdateForm,
    ProgressLogForm,
    PartUsageForm,
    InspectionCheckInForm,
    InspectionAbnormalityForm,
    AdminOrderAssignForm,
)

User = get_user_model()


def _require_household(request):
    """仅户主可访问报修模块。"""
    if not request.user.is_authenticated:
        return redirect("accounts:login_select_role")
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != UserProfile.Role.HOUSEHOLD:
        messages.warning(request, "仅户主可提交与查看报修工单。")
        return redirect("community_core:home")
    return None


@login_required(login_url="accounts:login_select_role")
def household_repair_list(request):
    """我的工单列表（报修进度 / 历史工单）。"""
    denied = _require_household(request)
    if denied:
        return denied
    status = request.GET.get("status", "").strip()
    qs = RepairOrder.objects.filter(reporter=request.user).select_related("room", "room__unit", "room__unit__building")
    if status:
        qs = qs.filter(status=status)
    orders = qs.order_by("-created_at")
    return render(
        request,
        "repair/household_repair_list.html",
        {"orders": orders, "status_filter": status},
    )


@login_required(login_url="accounts:login_select_role")
def household_repair_create(request):
    """我要报修：提交工单。"""
    denied = _require_household(request)
    if denied:
        return denied
    if request.method == "POST":
        form = CreateRepairForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.reporter = request.user
            order.save()
            messages.success(request, "报修已提交，请等待物业处理。")
            return redirect("repair:household_repair_detail", pk=order.pk)
        messages.error(request, "请修正以下错误。")
    else:
        form = CreateRepairForm()
        form.fields["room"].queryset = request.user.owned_rooms.all().select_related("unit", "unit__building")
        form.fields["room"].required = False
        form.fields["room"].empty_label = "（选填）"
    return render(request, "repair/household_repair_create.html", {"form": form})


@login_required(login_url="accounts:login_select_role")
def household_repair_detail(request, pk):
    """工单详情（报修进度）+ 已完成可评价。"""
    denied = _require_household(request)
    if denied:
        return denied
    order = get_object_or_404(RepairOrder, pk=pk, reporter=request.user)
    evaluation = getattr(order, "evaluation", None)
    can_evaluate = order.status == RepairOrder.Status.COMPLETED and not evaluation
    eval_form = None
    if can_evaluate:
        if request.method == "POST":
            eval_form = EvaluationForm(request.POST)
            if eval_form.is_valid():
                eval_form.save(commit=False)
                eval_form.instance.order = order
                eval_form.save()
                messages.success(request, "感谢您的评价。")
                return redirect("repair:household_repair_detail", pk=pk)
            messages.error(request, "请修正以下错误。")
        else:
            eval_form = EvaluationForm()
    return render(
        request,
        "repair/household_repair_detail.html",
        {"order": order, "evaluation": evaluation, "can_evaluate": can_evaluate, "eval_form": eval_form},
    )


# ---------- 管理员端：工单管理 ----------


def _require_admin(request):
    """仅管理员可访问。"""
    if not request.user.is_authenticated:
        return redirect("accounts:login_select_role")
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != UserProfile.Role.ADMIN:
        messages.warning(request, "只有管理员可以访问工单管理。")
        return redirect("community_core:home")
    return None


def _maintenance_user_queryset():
    """已审批的维修人员（用于指派下拉）。"""
    return User.objects.filter(
        profile__role=UserProfile.Role.MAINTENANCE,
        profile__is_approved=True,
    ).order_by("username")


@login_required(login_url="accounts:login_select_role")
def admin_order_list(request):
    """管理员工单列表：筛选（状态、指派人、关键字、日期）。"""
    denied = _require_admin(request)
    if denied:
        return denied
    status_filter = request.GET.get("status", "").strip()
    assigned_id = request.GET.get("assigned", "").strip()
    q = request.GET.get("q", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    qs = (
        RepairOrder.objects.all()
        .select_related("reporter", "room", "room__unit", "room__unit__building", "assigned_to")
        .order_by("-created_at")
    )
    if status_filter:
        qs = qs.filter(status=status_filter)
    if assigned_id:
        qs = qs.filter(assigned_to_id=assigned_id)
    if q:
        qs = qs.filter(
            Q(title__icontains=q) | Q(description__icontains=q) | Q(reporter__username__icontains=q)
        )
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    maintenance_users = _maintenance_user_queryset()
    context = {
        "orders": qs,
        "status_filter": status_filter,
        "assigned_id": assigned_id,
        "q": q,
        "date_from": date_from,
        "date_to": date_to,
        "maintenance_users": maintenance_users,
    }
    return render(request, "repair/admin_order_list.html", context)


@login_required(login_url="accounts:login_select_role")
def admin_order_detail(request, pk):
    """管理员工单详情：查看、指派、管理备注、取消。"""
    denied = _require_admin(request)
    if denied:
        return denied
    order = get_object_or_404(
        RepairOrder.objects.select_related(
            "reporter", "room", "room__unit", "room__unit__building", "assigned_to"
        ).prefetch_related("progress_logs", "progress_logs__created_by", "part_usages"),
        pk=pk,
    )
    assign_form = AdminOrderAssignForm(
        assignee_queryset=_maintenance_user_queryset(),
        initial={
            "assigned_to": order.assigned_to,
            "admin_remark": order.admin_remark or "",
        },
    )

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "assign":
            assign_form = AdminOrderAssignForm(
                request.POST,
                assignee_queryset=_maintenance_user_queryset(),
            )
            if assign_form.is_valid():
                order.assigned_to = assign_form.cleaned_data.get("assigned_to")
                order.admin_remark = assign_form.cleaned_data.get("admin_remark") or ""
                if order.assigned_to and order.status == RepairOrder.Status.PENDING:
                    order.status = RepairOrder.Status.ASSIGNED
                order.save(update_fields=["assigned_to", "admin_remark", "status", "updated_at"])
                messages.success(request, "指派与备注已保存。")
                return redirect("repair:admin_order_detail", pk=pk)
            messages.error(request, "请修正表单错误。")
        elif action == "cancel" and order.status != RepairOrder.Status.CANCELLED:
            order.status = RepairOrder.Status.CANCELLED
            order.save(update_fields=["status", "updated_at"])
            messages.success(request, "工单已取消。")
            return redirect("repair:admin_order_detail", pk=pk)

    evaluation = getattr(order, "evaluation", None)
    progress_logs = order.progress_logs.select_related("created_by").all()[:30]
    part_usages = order.part_usages.all()
    context = {
        "order": order,
        "assign_form": assign_form,
        "evaluation": evaluation,
        "progress_logs": progress_logs,
        "part_usages": part_usages,
    }
    return render(request, "repair/admin_order_detail.html", context)


# ---------- 维修人员端：我的工单 ----------


def _require_maintenance(request):
    """仅维修人员可访问。"""
    if not request.user.is_authenticated:
        return redirect("accounts:login_select_role")
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != UserProfile.Role.MAINTENANCE:
        messages.warning(request, "仅维修人员可访问该页面。")
        return redirect("community_core:home")
    return None


def _my_orders_queryset(user):
    """当前维修人员可见的工单：未派单或已派给自己的。"""
    return RepairOrder.objects.filter(
        Q(assigned_to__isnull=True) | Q(assigned_to=user)
    ).exclude(status=RepairOrder.Status.CANCELLED).select_related(
        "reporter", "room", "room__unit", "room__unit__building", "assigned_to"
    )


@login_required(login_url="accounts:login_select_role")
def maintenance_order_list(request):
    """我的工单列表：待处理 / 处理中 / 已完成。"""
    denied = _require_maintenance(request)
    if denied:
        return denied
    status_filter = request.GET.get("status", "").strip()
    qs = _my_orders_queryset(request.user).order_by("-created_at")
    if status_filter == "pending":
        qs = qs.filter(status__in=(RepairOrder.Status.PENDING, RepairOrder.Status.ASSIGNED))
    elif status_filter == "in_progress":
        qs = qs.filter(assigned_to=request.user, status=RepairOrder.Status.IN_PROGRESS)
    elif status_filter == "completed":
        qs = qs.filter(assigned_to=request.user, status=RepairOrder.Status.COMPLETED)
    orders = qs
    # 统计数字（当前用户）
    my_assigned = RepairOrder.objects.filter(assigned_to=request.user).exclude(status=RepairOrder.Status.CANCELLED)
    stats = {
        "pending": my_assigned.filter(status__in=(RepairOrder.Status.PENDING, RepairOrder.Status.ASSIGNED)).count(),
        "in_progress": my_assigned.filter(status=RepairOrder.Status.IN_PROGRESS).count(),
        "completed": my_assigned.filter(status=RepairOrder.Status.COMPLETED).count(),
    }
    return render(
        request,
        "repair/maintenance_order_list.html",
        {"orders": orders, "status_filter": status_filter, "stats": stats},
    )


@login_required(login_url="accounts:login_select_role")
def maintenance_order_detail(request, pk):
    """工单详情：接单、开始处理、完工、填写备注。"""
    denied = _require_maintenance(request)
    if denied:
        return denied
    order = get_object_or_404(RepairOrder, pk=pk)
    if order.status == RepairOrder.Status.CANCELLED:
        messages.warning(request, "该工单已取消。")
        return redirect("repair:maintenance_order_list")
    if order.assigned_to and order.assigned_to != request.user:
        messages.warning(request, "该工单已派给他人，您无法操作。")
        return redirect("repair:maintenance_order_list")
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "accept":
            order.assigned_to = request.user
            order.status = RepairOrder.Status.ASSIGNED
            order.save(update_fields=["assigned_to", "status", "updated_at"])
            messages.success(request, "已接单。")
            return redirect("repair:maintenance_order_detail", pk=pk)
        if action == "reassign":
            target_id = request.POST.get("target_user_id")
            if target_id:
                target = User.objects.filter(
                    pk=target_id,
                    profile__role=UserProfile.Role.MAINTENANCE,
                ).exclude(pk=request.user.pk).first()
                if target:
                    order.assigned_to = target
                    order.save(update_fields=["assigned_to", "updated_at"])
                    messages.success(request, f"已转派给 {target.username}。")
                    return redirect("repair:maintenance_order_detail", pk=pk)
            messages.error(request, "请选择有效的转派对象。")
        if action == "start":
            order.status = RepairOrder.Status.IN_PROGRESS
            order.save(update_fields=["status", "updated_at"])
            messages.success(request, "已开始处理。")
            return redirect("repair:maintenance_order_detail", pk=pk)
        if action == "complete":
            order.status = RepairOrder.Status.COMPLETED
            order.completed_at = timezone.now()
            if request.POST.get("cost_amount"):
                try:
                    from decimal import Decimal
                    order.cost_amount = Decimal(request.POST.get("cost_amount"))
                    order.cost_note = request.POST.get("cost_note", "")[:200]
                except Exception:
                    pass
            order.save(update_fields=["status", "completed_at", "updated_at", "cost_amount", "cost_note"])
            messages.success(request, "已标记完工。")
            return redirect("repair:maintenance_order_detail", pk=pk)
        if action == "add_progress":
            progress_form = ProgressLogForm(request.POST)
            if progress_form.is_valid():
                log = progress_form.save(commit=False)
                log.order = order
                log.created_by = request.user
                log.save()
                messages.success(request, "进度已上报。")
                return redirect("repair:maintenance_order_detail", pk=pk)
            messages.error(request, "请填写进度内容。")
        if action == "add_part":
            part_form = PartUsageForm(request.POST)
            if part_form.is_valid():
                part = part_form.save(commit=False)
                part.order = order
                part.save()
                messages.success(request, "配件已登记。")
                return redirect("repair:maintenance_order_detail", pk=pk)
            messages.error(request, "请修正配件信息。")
        form = MaintenanceOrderUpdateForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, "备注已更新。")
            return redirect("repair:maintenance_order_detail", pk=pk)
        messages.error(request, "请修正以下错误。")
    else:
        form = MaintenanceOrderUpdateForm(instance=order)
    progress_form = ProgressLogForm()
    part_form = PartUsageForm()
    progress_logs = order.progress_logs.select_related("created_by").all()[:20]
    part_usages = order.part_usages.all()
    maintenance_users = []
    if order.assigned_to == request.user and order.status not in (
        RepairOrder.Status.COMPLETED,
        RepairOrder.Status.CANCELLED,
    ):
        maintenance_users = list(
            User.objects.filter(profile__role=UserProfile.Role.MAINTENANCE)
            .exclude(pk=request.user.pk)
            .values("id", "username")
        )
    return render(
        request,
        "repair/maintenance_order_detail.html",
        {
            "order": order,
            "form": form,
            "maintenance_users": maintenance_users,
            "progress_logs": progress_logs,
            "part_usages": part_usages,
            "progress_form": progress_form,
            "part_form": part_form,
        },
    )


@login_required(login_url="accounts:login_select_role")
def maintenance_order_stats(request):
    """工单统计（当前维修人员）。"""
    denied = _require_maintenance(request)
    if denied:
        return denied
    user = request.user
    base = RepairOrder.objects.filter(assigned_to=user).exclude(status=RepairOrder.Status.CANCELLED)
    stats = {
        "pending": base.filter(status__in=(RepairOrder.Status.PENDING, RepairOrder.Status.ASSIGNED)).count(),
        "in_progress": base.filter(status=RepairOrder.Status.IN_PROGRESS).count(),
        "completed": base.filter(status=RepairOrder.Status.COMPLETED).count(),
        "completed_total": base.filter(status=RepairOrder.Status.COMPLETED).count(),
    }
    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    stats["completed_this_month"] = base.filter(
        status=RepairOrder.Status.COMPLETED,
        completed_at__gte=month_start,
    ).count()
    return render(request, "repair/maintenance_order_stats.html", {"stats": stats})


# ---------- 维修人员端：接单处理 ----------

# 超时阈值（小时）
OVERDUE_HOURS = 24


@login_required(login_url="accounts:login_select_role")
def maintenance_available_orders(request):
    """可接单工单列表（未派单），手动接单。"""
    denied = _require_maintenance(request)
    if denied:
        return denied
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(hours=OVERDUE_HOURS)
    orders = (
        RepairOrder.objects.filter(assigned_to__isnull=True)
        .exclude(status=RepairOrder.Status.CANCELLED)
        .filter(status__in=(RepairOrder.Status.PENDING, RepairOrder.Status.ASSIGNED))
        .select_related("reporter", "room", "room__unit", "room__unit__building")
        .order_by("created_at")
    )
    return render(request, "repair/maintenance_available_orders.html", {"orders": orders, "overdue_cutoff": cutoff})


@login_required(login_url="accounts:login_select_role")
def maintenance_accept_order(request, pk):
    """一键接单（从可接单列表 POST）。"""
    denied = _require_maintenance(request)
    if denied:
        return denied
    order = get_object_or_404(
        RepairOrder,
        pk=pk,
        assigned_to__isnull=True,
        status__in=(RepairOrder.Status.PENDING, RepairOrder.Status.ASSIGNED),
    )
    if request.method == "POST":
        order.assigned_to = request.user
        order.status = RepairOrder.Status.ASSIGNED
        order.save(update_fields=["assigned_to", "status", "updated_at"])
        messages.success(request, "已接单。")
        return redirect("repair:maintenance_order_detail", pk=pk)
    return redirect("repair:maintenance_available_orders")


@login_required(login_url="accounts:login_select_role")
def maintenance_accept_settings(request):
    """自动接单开关。"""
    denied = _require_maintenance(request)
    if denied:
        return denied
    pref, _ = MaintenancePreference.objects.get_or_create(user=request.user, defaults={"auto_accept": False})
    if request.method == "POST":
        pref.auto_accept = request.POST.get("auto_accept") == "1"
        pref.save()
        messages.success(request, "接单设置已保存。")
        return redirect("repair:maintenance_accept_settings")
    return render(request, "repair/maintenance_accept_settings.html", {"pref": pref})


@login_required(login_url="accounts:login_select_role")
def maintenance_overdue_list(request):
    """工单超时提醒：超过设定时长仍未完成的工单。"""
    denied = _require_maintenance(request)
    if denied:
        return denied
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(hours=OVERDUE_HOURS)
    orders = (
        RepairOrder.objects.exclude(status__in=(RepairOrder.Status.COMPLETED, RepairOrder.Status.CANCELLED))
        .filter(created_at__lt=cutoff)
        .select_related("reporter", "assigned_to", "room")
        .order_by("created_at")
    )
    return render(
        request,
        "repair/maintenance_overdue_list.html",
        {"orders": orders, "overdue_hours": OVERDUE_HOURS},
    )


# ---------- 维修人员端：个人中心 ----------


@login_required(login_url="accounts:login_select_role")
def maintenance_profile_index(request):
    """维修人员个人中心首页。"""
    denied = _require_maintenance(request)
    if denied:
        return denied
    return render(request, "repair/maintenance_profile_index.html")


@login_required(login_url="accounts:login_select_role")
def maintenance_schedule_list(request):
    """工作排班。"""
    denied = _require_maintenance(request)
    if denied:
        return denied
    from datetime import timedelta
    today = timezone.now().date()
    month_later = today + timedelta(days=31)
    schedules = (
        MaintenanceSchedule.objects.filter(user=request.user)
        .filter(work_date__gte=today - timedelta(days=7), work_date__lte=month_later)
        .order_by("work_date", "start_time")
    )
    return render(request, "repair/maintenance_schedule_list.html", {"schedules": schedules})


@login_required(login_url="accounts:login_select_role")
def maintenance_payslip_list(request):
    """工资单。"""
    denied = _require_maintenance(request)
    if denied:
        return denied
    payslips = MaintenancePayslip.objects.filter(user=request.user).order_by("-created_at")[:24]
    return render(request, "repair/maintenance_payslip_list.html", {"payslips": payslips})


@login_required(login_url="accounts:login_select_role")
def maintenance_cert_list(request):
    """技能认证。"""
    denied = _require_maintenance(request)
    if denied:
        return denied
    certs = MaintenanceCert.objects.filter(user=request.user).order_by("-issued_at")
    return render(request, "repair/maintenance_cert_list.html", {"certs": certs})


@login_required(login_url="accounts:login_select_role")
def maintenance_training_list(request):
    """培训资料。"""
    denied = _require_maintenance(request)
    if denied:
        return denied
    materials = TrainingMaterial.objects.all().order_by("-created_at")[:50]
    return render(request, "repair/maintenance_training_list.html", {"materials": materials})


@login_required(login_url="accounts:login_select_role")
def maintenance_training_detail(request, pk):
    """培训资料详情。"""
    denied = _require_maintenance(request)
    if denied:
        return denied
    material = get_object_or_404(TrainingMaterial, pk=pk)
    return render(request, "repair/maintenance_training_detail.html", {"material": material})


# ---------- 维修人员端：巡检任务 ----------


@login_required(login_url="accounts:login_select_role")
def maintenance_inspection_list(request):
    """巡检计划 / 巡检记录：我的巡检任务列表。"""
    denied = _require_maintenance(request)
    if denied:
        return denied
    status_filter = request.GET.get("status", "").strip()
    qs = InspectionTask.objects.filter(assignee=request.user).order_by("-task_date", "-created_at")
    if status_filter:
        qs = qs.filter(status=status_filter)
    tasks = qs
    return render(
        request,
        "repair/maintenance_inspection_list.html",
        {"tasks": tasks, "status_filter": status_filter},
    )


@login_required(login_url="accounts:login_select_role")
def maintenance_inspection_detail(request, pk):
    """巡检任务详情：打卡、异常上报。"""
    denied = _require_maintenance(request)
    if denied:
        return denied
    task = get_object_or_404(InspectionTask, pk=pk, assignee=request.user)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "checkin":
            form = InspectionCheckInForm(request.POST)
            if form.is_valid():
                checkin = form.save(commit=False)
                checkin.task = task
                checkin.created_by = request.user
                checkin.save()
                if task.status == InspectionTask.Status.PENDING:
                    task.status = InspectionTask.Status.IN_PROGRESS
                    task.save(update_fields=["status"])
                messages.success(request, "打卡成功。")
                return redirect("repair:maintenance_inspection_detail", pk=pk)
            messages.error(request, "请填写打卡位置。")
        if action == "abnormality":
            ab_form = InspectionAbnormalityForm(request.POST)
            if ab_form.is_valid():
                ab = ab_form.save(commit=False)
                ab.task = task
                ab.reported_by = request.user
                ab.save()
                messages.success(request, "异常已上报。")
                return redirect("repair:maintenance_inspection_detail", pk=pk)
            messages.error(request, "请填写异常描述。")
        if action == "complete":
            task.status = InspectionTask.Status.COMPLETED
            task.save(update_fields=["status"])
            messages.success(request, "巡检已标记完成。")
            return redirect("repair:maintenance_inspection_detail", pk=pk)
    check_ins = task.check_ins.select_related("created_by").all()
    abnormalities = task.abnormalities.select_related("reported_by").all()
    return render(
        request,
        "repair/maintenance_inspection_detail.html",
        {
            "task": task,
            "check_ins": check_ins,
            "abnormalities": abnormalities,
            "checkin_form": InspectionCheckInForm(),
            "abnormality_form": InspectionAbnormalityForm(),
        },
    )
