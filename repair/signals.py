from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Count

from accounts.models import UserProfile
from .models import RepairOrder, MaintenancePreference


@receiver(post_save, sender=RepairOrder)
def maybe_auto_assign_order(sender, instance, created, **kwargs):
    """新工单创建且未指派时，若有维修人员开启自动接单，则派给当前待办最少的一人。"""
    if not created or instance.assigned_to_id is not None:
        return
    prefs = MaintenancePreference.objects.filter(auto_accept=True).values_list("user_id", flat=True)
    if not prefs:
        return
    from django.contrib.auth import get_user_model
    User = get_user_model()
    maintenance_ids = list(
        UserProfile.objects.filter(role=UserProfile.Role.MAINTENANCE, user_id__in=prefs)
        .values_list("user_id", flat=True)
    )
    if not maintenance_ids:
        return
    # 统计每人当前未完成工单数（待处理+处理中）
    from django.db.models import F
    from django.db.models.functions import Coalesce
    workload = (
        RepairOrder.objects.filter(
            assigned_to_id__in=maintenance_ids,
            status__in=(RepairOrder.Status.PENDING, RepairOrder.Status.ASSIGNED, RepairOrder.Status.IN_PROGRESS),
        )
        .values("assigned_to_id")
        .annotate(n=Count("id"))
    )
    by_user = {w["assigned_to_id"]: w["n"] for w in workload}
    # 选人数最少的（未出现的视为 0）
    best_id = min(maintenance_ids, key=lambda uid: by_user.get(uid, 0))
    from django.utils import timezone
    RepairOrder.objects.filter(pk=instance.pk).update(
        assigned_to_id=best_id,
        status=RepairOrder.Status.ASSIGNED,
        updated_at=timezone.now(),
    )
