from django import forms
from .models import Vehicle, TempParkingRequest


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ("plate_number", "brand_model", "color")
        labels = {"plate_number": "车牌号", "brand_model": "品牌型号", "color": "颜色"}
        widgets = {
            "plate_number": forms.TextInput(attrs={"placeholder": "如：京A12345"}),
        }


class TempParkingRequestForm(forms.ModelForm):
    class Meta:
        model = TempParkingRequest
        fields = ("plate_number", "start_time", "end_time", "purpose")
        labels = {
            "plate_number": "车牌号",
            "start_time": "预计进入时间",
            "end_time": "预计离开时间",
            "purpose": "事由（选填）",
        }
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean(self):
        data = super().clean()
        start = data.get("start_time")
        end = data.get("end_time")
        if start and end and end <= start:
            self.add_error("end_time", "离开时间须晚于进入时间。")
        return data
