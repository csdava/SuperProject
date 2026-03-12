"""
智慧社区管理系统 - Django 项目配置
Django 6.0.3 | 数据库: SQLite | 前端: HTML
"""

from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 安全与调试（生产环境请修改）
SECRET_KEY = "django-insecure-(1ruhbma-4=%rw5rxa76dun-)_ycay5_+f2!yg8-ik262vi!n5"
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]


# 已安装应用：Django 内置 + 智慧社区业务应用
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",  # 登录/注册/身份与审批
    # 智慧社区业务模块
    "community_core",      # 社区基础管理（住户、楼栋）
    "property_fees",       # 物业收费系统
    "repair",              # 报事报修管理
    "visitor_access",      # 访客与出入管理
    "security",            # 智慧安防监控
    "life_services",       # 社区生活服务
    "vehicle_mgmt",        # 车辆管理
    "facility_mgmt",       # 设备设施管理
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "DjangoProject333.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "DjangoProject333.wsgi.application"


# 数据库配置 - SQLite（开发/小型部署）
# 生产环境可切换为 PostgreSQL/MySQL，硬件数据可走独立库
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "timeout": 20,
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# 国际化与时区（中文）
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# 静态文件与媒体文件
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# 登录/登出（先选身份再登录）
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"  # 实际按身份在 views 中重定向到对应工作台
LOGOUT_REDIRECT_URL = "/"
