from django.apps import AppConfig


class InventarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.inventario'
    verbose_name = 'Inventory'

    def ready(self):
        """Import signals when app is ready"""
        import apps.inventario.signals  # noqa
