from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Core'
    verbose_name = 'Trello-like Core App'

    def ready(self):
        import Core.signals  # noqa: F401 — registers signal handlers
