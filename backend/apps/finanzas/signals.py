from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.empleados.models import Sucursal
from .models import TransactionCategory


@receiver(post_save, sender=Sucursal)
def create_system_categories(sender, instance, created, **kwargs):
    """
    Automatically create system categories when a new branch is created.
    These categories are protected and cannot be deleted.
    """
    if created:
        # Define system categories
        system_categories = [
            {
                'name': 'Servicios',
                'type': TransactionCategory.CategoryType.INCOME,
                'description': 'Ingresos por servicios realizados a clientes',
                'color': '#10B981',  # Green
                'icon': 'briefcase',
                'order': 1
            },
            {
                'name': 'Productos',
                'type': TransactionCategory.CategoryType.INCOME,
                'description': 'Ingresos por venta de productos',
                'color': '#3B82F6',  # Blue
                'icon': 'package',
                'order': 2
            },
            {
                'name': 'Salarios',
                'type': TransactionCategory.CategoryType.EXPENSE,
                'description': 'Pagos de salarios a empleados',
                'color': '#F59E0B',  # Amber
                'icon': 'users',
                'order': 1
            },
            {
                'name': 'Alquileres de Equipos',
                'type': TransactionCategory.CategoryType.EXPENSE,
                'description': 'Costos de alquiler de máquinas y equipos',
                'color': '#EF4444',  # Red
                'icon': 'tool',
                'order': 2
            },
        ]

        # Create each system category
        for category_data in system_categories:
            TransactionCategory.objects.get_or_create(
                branch=instance,
                name=category_data['name'],
                type=category_data['type'],
                defaults={
                    'description': category_data['description'],
                    'color': category_data['color'],
                    'icon': category_data['icon'],
                    'order': category_data['order'],
                    'is_system_category': True,
                    'is_active': True,
                }
            )

        print(f"✅ Created system categories for branch: {instance.nombre}")
