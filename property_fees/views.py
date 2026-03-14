from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F

from accounts.models import UserProfile
from .models import Bill, Payment


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
