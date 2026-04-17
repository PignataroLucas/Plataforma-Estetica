from django.apps import AppConfig


class ServiciosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.servicios'
    verbose_name = 'Servicios'

    def ready(self):
        from . import signals  # noqa: F401
