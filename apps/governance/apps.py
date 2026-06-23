from django.apps import AppConfig


class GovernanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.governance"
    verbose_name = "Committee & Governance"

    def ready(self):
        import apps.governance.signals  # noqa: F401
