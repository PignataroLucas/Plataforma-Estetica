from django.apps import AppConfig


class TurnosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.turnos'
    verbose_name = 'Turnos'

    def ready(self):
        """
        Import signals when app is ready.
        This connects the appointment payment tracking signals.
        """
        import apps.turnos.signals  # noqa: F401
