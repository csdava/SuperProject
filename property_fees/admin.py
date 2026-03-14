from django.contrib import admin
from .models import FeeType, Bill, Payment


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("paid_at",)


@admin.register(FeeType)
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "unit")
    search_fields = ("name", "code")


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ("room", "fee_type", "period", "amount", "paid_amount", "status", "due_date", "paid_at")
    list_filter = ("status", "fee_type", "room__unit__building")
    search_fields = ("room__room_no", "period", "remark")
    inlines = [PaymentInline]
    readonly_fields = ("paid_amount", "paid_at", "created_at", "updated_at")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("bill", "amount", "payment_method", "paid_at", "operator")
    list_filter = ("payment_method",)
    search_fields = ("bill__room__room_no", "remark")
