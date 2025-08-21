from django.apps import AppConfig


class OnboardingConfig(AppConfig):
    name = "onboarding"
    verbose_name = "HR Onboarding System"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from . import signals  # noqa: F401
