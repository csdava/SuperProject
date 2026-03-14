from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from accounts.models import UserProfile
from .models import VisitorInvite
from .forms import VisitorInviteForm


def _require_household(request):
    """仅户主可访问。"""
    if not request.user.is_authenticated:
        return redirect("accounts:login_select_role")
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != UserProfile.Role.HOUSEHOLD:
        messages.warning(request, "仅户主可使用访客管理。")
        return redirect("community_core:home")
    return None


@login_required(login_url="accounts:login_select_role")
def household_invite_list(request):
    """我的访客邀请列表（访客记录）。"""
    denied = _require_household(request)
    if denied:
        return denied
    # 将已过期的有效邀请标记为过期
    VisitorInvite.objects.filter(
        inviter=request.user,
        status=VisitorInvite.Status.ACTIVE,
        valid_until__lt=timezone.now(),
    ).update(status=VisitorInvite.Status.EXPIRED)
    invites = (
        VisitorInvite.objects.filter(inviter=request.user)
        .select_related("room", "room__unit", "room__unit__building")
        .order_by("-created_at")
    )
    return render(request, "visitor_access/household_invite_list.html", {"invites": invites})


@login_required(login_url="accounts:login_select_role")
def household_invite_create(request):
    """邀请访客。"""
    denied = _require_household(request)
    if denied:
        return denied
    if not request.user.owned_rooms.exists():
        messages.warning(request, "请先在住户管理中绑定您的房间后再邀请访客。")
        return redirect("community_core:household_profile_index")
    if request.method == "POST":
        form = VisitorInviteForm(request.POST, user=request.user)
        if form.is_valid():
            inv = form.save(commit=False)
            inv.inviter = request.user
            inv.save()
            messages.success(request, "邀请已创建，请将邀请链接或邀请码发给访客。")
            return redirect("visitor_access:household_invite_detail", pk=inv.pk)
        messages.error(request, "请修正表单错误。")
    else:
        from datetime import timedelta
        now = timezone.now()
        form = VisitorInviteForm(
            user=request.user,
            initial={
                "valid_from": now,
                "valid_until": now + timedelta(days=1),
            },
        )
    return render(request, "visitor_access/household_invite_form.html", {"form": form})


@login_required(login_url="accounts:login_select_role")
def household_invite_detail(request, pk):
    """邀请详情（含邀请码与链接，用于分享给访客）。"""
    denied = _require_household(request)
    if denied:
        return denied
    invite = get_object_or_404(
        VisitorInvite.objects.select_related("room", "room__unit", "room__unit__building"),
        pk=pk,
        inviter=request.user,
    )
    if invite.status == VisitorInvite.Status.ACTIVE and timezone.now() > invite.valid_until:
        invite.status = VisitorInvite.Status.EXPIRED
        invite.save(update_fields=["status"])
    # 用于分享的完整链接（访客出示给门岗）
    from django.urls import reverse
    invite_url = request.build_absolute_uri(reverse("visitor_access:invite_show", kwargs={"token": invite.token}))
    return render(
        request,
        "visitor_access/household_invite_detail.html",
        {"invite": invite, "invite_url": invite_url},
    )


@login_required(login_url="accounts:login_select_role")
def household_invite_cancel(request, pk):
    """取消邀请。"""
    denied = _require_household(request)
    if denied:
        return denied
    invite = get_object_or_404(VisitorInvite, pk=pk, inviter=request.user)
    if request.method == "POST":
        if invite.status == VisitorInvite.Status.ACTIVE:
            invite.status = VisitorInvite.Status.CANCELLED
            invite.save(update_fields=["status"])
            messages.success(request, "已取消该邀请。")
        else:
            messages.warning(request, "该邀请已不可取消。")
        return redirect("visitor_access:household_invite_list")
    return render(request, "visitor_access/household_invite_confirm_cancel.html", {"invite": invite})


def invite_show(request, token):
    """访客出示页面（无需登录）：凭 token 查看邀请信息，供门岗核验。"""
    invite = get_object_or_404(
        VisitorInvite.objects.select_related("room", "room__unit", "room__unit__building"),
        token=token,
    )
    if invite.status != VisitorInvite.Status.ACTIVE:
        return render(request, "visitor_access/invite_show.html", {"invite": invite, "invalid": True})
    now = timezone.now()
    if now < invite.valid_from or now > invite.valid_until:
        return render(request, "visitor_access/invite_show.html", {"invite": invite, "invalid": True})
    return render(request, "visitor_access/invite_show.html", {"invite": invite, "invalid": False})
