from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F

from accounts.models import UserProfile
from .models import FeeType, Bill, Payment
from .forms import FeeTypeForm, BillForm, PaymentForm


def _require_household(request):
    """仅户主可访问；返回 None 表示通过，否则返回 redirect 响应。"""
    if not request.user.is_authenticated:
        return redirect("accounts:login_select_role")
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != UserProfile.Role.HOUSEHOLD:
        messages.warning(request, "仅户主可查看费用中心。")
        return redirect("community_core:home")
    return None


def _my_bills_queryset(user):
    """当前户主名下的账单（其绑定房间的账单）。"""
    return Bill.objects.filter(room__owner_user=user).select_related("room", "room__unit", "room__unit__building", "fee_type")


@login_required(login_url="accounts:login_select_role")
def household_bill_list(request):
    """我的账单（仅本人绑定房间的账单），可按状态筛选。"""
    denied = _require_household(request)
    if denied:
        return denied
    status_filter = request.GET.get("status", "").strip()
    qs = _my_bills_queryset(request.user).order_by("-period", "-created_at")
    if status_filter and status_filter in dict(Bill.Status.choices):
        qs = qs.filter(status=status_filter)
    # 待缴总额（未缴清账单的 应收-已缴 之和）
    unpaid = _my_bills_queryset(request.user).filter(
        status__in=(Bill.Status.PENDING, Bill.Status.OVERDUE, Bill.Status.PARTIAL)
    )
    total_due = unpaid.aggregate(s=Sum(F("amount") - F("paid_amount")))["s"] or 0
    return render(
        request,
        "property_fees/household_bill_list.html",
        {"bills": qs, "status_filter": status_filter, "total_due": total_due},
    )


@login_required(login_url="accounts:login_select_role")
def household_bill_detail(request, pk):
    """账单详情（含缴费记录）。"""
    denied = _require_household(request)
    if denied:
        return denied
    bill = get_object_or_404(Bill.objects.select_related("room", "room__unit", "room__unit__building", "fee_type"), pk=pk)
    if bill.room.owner_user_id != request.user.id:
        messages.warning(request, "无权查看该账单。")
        return redirect("property_fees:household_bill_list")
    payments = bill.payments.select_related("operator").order_by("-paid_at")
    remaining_due = bill.amount - bill.paid_amount
    return render(
        request,
        "property_fees/household_bill_detail.html",
        {"bill": bill, "payments": payments, "remaining_due": remaining_due},
    )


@login_required(login_url="accounts:login_select_role")
def household_payment_list(request):
    """缴费记录（本人名下所有账单的缴费记录）。"""
    denied = _require_household(request)
    if denied:
        return denied
    payments = (
        Payment.objects.filter(bill__room__owner_user=request.user)
        .select_related("bill", "bill__fee_type", "bill__room", "operator")
        .order_by("-paid_at")[:80]
    )
    return render(request, "property_fees/household_payment_list.html", {"payments": payments})


# ---------- 管理员端：财务管理 ----------


def _require_admin(request):
    """仅管理员可访问。"""
    if not request.user.is_authenticated:
        return redirect("accounts:login_select_role")
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != UserProfile.Role.ADMIN:
        messages.warning(request, "只有管理员可访问财务管理。")
        return redirect("community_core:home")
    return None


@login_required(login_url="accounts:login_select_role")
def admin_fee_type_list(request):
    """费用标准设置：费用类型列表、新增、编辑。"""
    denied = _require_admin(request)
    if denied:
        return denied
    types = FeeType.objects.all().order_by("name")
    return render(request, "property_fees/admin_fee_type_list.html", {"fee_types": types})


@login_required(login_url="accounts:login_select_role")
def admin_fee_type_create(request):
    """新增费用类型。"""
    denied = _require_admin(request)
    if denied:
        return denied
    if request.method == "POST":
        form = FeeTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "费用类型已添加。")
            return redirect("property_fees:admin_fee_type_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = FeeTypeForm()
    return render(request, "property_fees/admin_fee_type_form.html", {"form": form, "is_edit": False})


@login_required(login_url="accounts:login_select_role")
def admin_fee_type_edit(request, pk):
    """编辑费用类型。"""
    denied = _require_admin(request)
    if denied:
        return denied
    fee_type = get_object_or_404(FeeType, pk=pk)
    if request.method == "POST":
        form = FeeTypeForm(request.POST, instance=fee_type)
        if form.is_valid():
            form.save()
            messages.success(request, "费用类型已更新。")
            return redirect("property_fees:admin_fee_type_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = FeeTypeForm(instance=fee_type)
    return render(request, "property_fees/admin_fee_type_form.html", {"form": form, "fee_type": fee_type, "is_edit": True})


@login_required(login_url="accounts:login_select_role")
def admin_bill_list(request):
    """账单列表（按楼栋、账期、状态筛选）。"""
    denied = _require_admin(request)
    if denied:
        return denied
    from community_core.models import Building
    building_id = request.GET.get("building", "").strip()
    period = request.GET.get("period", "").strip()
    status_filter = request.GET.get("status", "").strip()
    qs = Bill.objects.select_related("room", "room__unit", "room__unit__building", "fee_type").order_by("-period", "-created_at")
    if building_id:
        qs = qs.filter(room__unit__building_id=building_id)
    if period:
        qs = qs.filter(period=period)
    if status_filter and status_filter in dict(Bill.Status.choices):
        qs = qs.filter(status=status_filter)
    buildings = Building.objects.all().order_by("name")
    return render(
        request,
        "property_fees/admin_bill_list.html",
        {"bills": qs, "buildings": buildings, "building_id": building_id, "period": period, "status_filter": status_filter},
    )


@login_required(login_url="accounts:login_select_role")
def admin_bill_create(request):
    """生成账单（单笔）。"""
    denied = _require_admin(request)
    if denied:
        return denied
    if request.method == "POST":
        form = BillForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "账单已生成。")
            return redirect("property_fees:admin_bill_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = BillForm()
    return render(request, "property_fees/admin_bill_form.html", {"form": form, "is_edit": False})


@login_required(login_url="accounts:login_select_role")
def admin_bill_edit(request, pk):
    """编辑账单（金额、到期日、备注）。"""
    denied = _require_admin(request)
    if denied:
        return denied
    bill = get_object_or_404(Bill.objects.select_related("room", "fee_type"), pk=pk)
    if request.method == "POST":
        form = BillForm(request.POST, instance=bill)
        if form.is_valid():
            form.save()
            bill.update_status()
            messages.success(request, "账单已更新。")
            return redirect("property_fees:admin_bill_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = BillForm(instance=bill)
    return render(request, "property_fees/admin_bill_form.html", {"form": form, "bill": bill, "is_edit": True})


@login_required(login_url="accounts:login_select_role")
def admin_bill_bulk(request):
    """批量生成账单：按账期+费用类型，为指定楼栋下所有房间生成。"""
    denied = _require_admin(request)
    if denied:
        return denied
    from community_core.models import Building, Room
    if request.method == "POST":
        period = request.POST.get("period", "").strip()
        fee_type_id = request.POST.get("fee_type", "").strip()
        building_id = request.POST.get("building", "").strip()
        default_amount = request.POST.get("default_amount", "0").strip()
        if not period or not fee_type_id:
            messages.error(request, "请填写账期并选择费用类型。")
        else:
            try:
                fee_type = FeeType.objects.get(pk=fee_type_id)
                amount = float(default_amount) if default_amount else 0
                rooms = Room.objects.all()
                if building_id:
                    rooms = rooms.filter(unit__building_id=building_id)
                created = 0
                for room in rooms:
                    _, created_this = Bill.objects.get_or_create(
                        room=room,
                        fee_type=fee_type,
                        period=period,
                        defaults={"amount": amount},
                    )
                    if created_this:
                        created += 1
                messages.success(request, f"已为 {created} 个房间生成账单。")
                return redirect("property_fees:admin_bill_list")
            except FeeType.DoesNotExist:
                messages.error(request, "费用类型不存在。")
            except ValueError:
                messages.error(request, "默认金额请填写数字。")
    buildings = Building.objects.all().order_by("name")
    fee_types = FeeType.objects.all().order_by("name")
    return render(
        request,
        "property_fees/admin_bill_bulk.html",
        {"buildings": buildings, "fee_types": fee_types},
    )


@login_required(login_url="accounts:login_select_role")
def admin_payment_list(request):
    """缴费记录查询。"""
    denied = _require_admin(request)
    if denied:
        return denied
    period = request.GET.get("period", "").strip()
    qs = Payment.objects.select_related("bill", "bill__room", "bill__fee_type", "operator").order_by("-paid_at")
    if period:
        qs = qs.filter(bill__period=period)
    return render(request, "property_fees/admin_payment_list.html", {"payments": qs[:200], "period_filter": period})


@login_required(login_url="accounts:login_select_role")
def admin_payment_add(request):
    """录入缴费。"""
    denied = _require_admin(request)
    if denied:
        return denied
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.operator = request.user
            obj.save()
            messages.success(request, "缴费已录入。")
            return redirect("property_fees:admin_payment_list")
        messages.error(request, "请修正表单错误。")
    else:
        form = PaymentForm()
    return render(request, "property_fees/admin_payment_form.html", {"form": form})


@login_required(login_url="accounts:login_select_role")
def admin_fee_stats(request):
    """收费率统计（应收、实收、待收、笔数）。"""
    denied = _require_admin(request)
    if denied:
        return denied
    total_amount = Bill.objects.aggregate(s=Sum("amount"))["s"] or 0
    total_paid = Bill.objects.aggregate(s=Sum("paid_amount"))["s"] or 0
    total_due = total_amount - total_paid
    bill_count = Bill.objects.count()
    paid_count = Bill.objects.filter(status=Bill.Status.PAID).count()
    overdue_count = Bill.objects.filter(status=Bill.Status.OVERDUE).count()
    payment_count = Payment.objects.count()
    return render(
        request,
        "property_fees/admin_fee_stats.html",
        {
            "total_amount": total_amount,
            "total_paid": total_paid,
            "total_due": total_due,
            "bill_count": bill_count,
            "paid_count": paid_count,
            "overdue_count": overdue_count,
            "payment_count": payment_count,
        },
    )
