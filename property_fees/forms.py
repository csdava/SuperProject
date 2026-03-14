from django import forms
from .models import FeeType, Bill, Payment


class FeeTypeForm(forms.ModelForm):
    class Meta:
        model = FeeType
        fields = ("name", "code", "unit")
        labels = {"name": "费用名称", "code": "编号", "unit": "单位"}


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ("room", "fee_type", "period", "amount", "due_date", "remark")
        labels = {
            "room": "房间",
            "fee_type": "费用类型",
            "period": "账期",
            "amount": "应收金额",
            "due_date": "到期日",
            "remark": "备注",
        }
        widgets = {
            "period": forms.TextInput(attrs={"placeholder": "如：2024-01"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ("bill", "amount", "payment_method", "remark")
        labels = {
            "bill": "账单",
            "amount": "缴费金额",
            "payment_method": "支付方式",
            "remark": "备注",
        }
