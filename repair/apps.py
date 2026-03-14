from django.apps import AppConfig


class RepairConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "repair"
    verbose_name = "报事报修管理"

    def ready(self):
        from . import signals  # noqa: F401
