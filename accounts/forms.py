from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from .models import UserProfile


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
