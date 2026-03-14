from django import forms
from django.utils import timezone
from .models import VisitorInvite


class VisitorInviteForm(forms.ModelForm):
    """户主创建访客邀请。"""

    class Meta:
        model = VisitorInvite
        fields = ("visitor_name", "visitor_phone", "id_number", "purpose", "room", "valid_from", "valid_until")
        labels = {
            "visitor_name": "访客姓名",
            "visitor_phone": "访客电话",
            "id_number": "访客证件号（选填）",
            "purpose": "来访事由（选填）",
            "room": "到访房间",
            "valid_from": "有效期起",
            "valid_until": "有效期止",
        }
        widgets = {
            "valid_from": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "valid_until": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["room"].queryset = self.user.owned_rooms.select_related("unit", "unit__building").all()
            self.fields["room"].empty_label = None
        self.fields["room"].required = True

    def clean(self):
        data = super().clean()
        valid_from = data.get("valid_from")
        valid_until = data.get("valid_until")
        if valid_from and valid_until and valid_until <= valid_from:
            self.add_error("valid_until", "有效期止须晚于有效期起。")
        return data
