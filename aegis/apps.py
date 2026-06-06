from django.apps import AppConfig


class AegisConfig(AppConfig):
    name = 'aegis'

    def ready(self):
        import aegis.signals  # noqa: F401
