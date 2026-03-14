from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from .models import UserProfile, SystemConfig


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
