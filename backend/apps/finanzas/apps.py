from django.apps import AppConfig


class FinanzasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.finanzas'
    verbose_name = 'Finanzas'

    def ready(self):
        """Import signals when app is ready"""
        import apps.finanzas.signals
