from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from .models import UserProfile, SystemConfig, HouseholdComfortSetting


class RegisterForm(UserCreationForm):
    """注册表单：仅开放户主、维修人员；管理员由后台创建。"""

    role = forms.ChoiceField(
        label="身份",
        choices=[
            (UserProfile.Role.HOUSEHOLD, "户主"),
            (UserProfile.Role.MAINTENANCE, "维修人员"),
        ],
        widget=forms.RadioSelect,
    )

    class Meta:
        model = User
        fields = ("username", "password1", "password2")
        labels = {"username": "用户名"}

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data["role"],
                is_approved=False,
            )
        return user


class LoginForm(AuthenticationForm):
    """登录表单：用户名、密码（身份在视图中与 session 中的已选身份校验）。"""

    username = forms.CharField(label="用户名", max_length=150)
    password = forms.CharField(label="密码", widget=forms.PasswordInput)


class AdminUserProfileForm(forms.Form):
    """管理员端：修改用户身份与审批状态。"""

    role = forms.ChoiceField(label="身份", choices=UserProfile.Role.choices)
    is_approved = forms.BooleanField(label="已审批", required=False)


class SystemConfigForm(forms.ModelForm):
    """基础参数配置编辑。"""

    class Meta:
        model = SystemConfig
        fields = ("key", "value", "description")
        widgets = {"value": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        self.edit_key = kwargs.pop("edit_key", None)  # 编辑时传入，key 只读
        super().__init__(*args, **kwargs)
        if self.edit_key is not None:
            self.fields["key"].disabled = True


class HouseholdComfortSettingForm(forms.ModelForm):
    """户主舒适温湿度范围设置。"""

    class Meta:
        model = HouseholdComfortSetting
        fields = ("temp_min", "temp_max", "humidity_min", "humidity_max")
        widgets = {
            "temp_min": forms.NumberInput(attrs={"step": "0.1", "required": "required"}),
            "temp_max": forms.NumberInput(attrs={"step": "0.1", "required": "required"}),
            "humidity_min": forms.NumberInput(attrs={"step": "0.1", "required": "required"}),
            "humidity_max": forms.NumberInput(attrs={"step": "0.1", "required": "required"}),
        }

    def clean(self):
        cleaned = super().clean()
        temp_min = cleaned.get("temp_min")
        temp_max = cleaned.get("temp_max")
        humidity_min = cleaned.get("humidity_min")
        humidity_max = cleaned.get("humidity_max")

        if temp_min is not None and temp_max is not None and temp_min > temp_max:
            raise forms.ValidationError("温度下限不能大于温度上限。")

        if humidity_min is not None and humidity_max is not None and humidity_min > humidity_max:
            raise forms.ValidationError("湿度下限不能大于湿度上限。")

        # 简单边界：湿度理论上 0~100
        if humidity_min is not None and (humidity_min < 0 or humidity_min > 100):
            raise forms.ValidationError("湿度下限需在 0~100 之间。")
        if humidity_max is not None and (humidity_max < 0 or humidity_max > 100):
            raise forms.ValidationError("湿度上限需在 0~100 之间。")

        return cleaned
