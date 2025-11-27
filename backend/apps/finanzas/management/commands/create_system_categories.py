from django.core.management.base import BaseCommand
from apps.empleados.models import Sucursal
from apps.finanzas.models import TransactionCategory


class Command(BaseCommand):
    help = 'Create system categories for all existing branches'

    def handle(self, *args, **options):
        """Create system categories for all branches that don't have them"""
        
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

        sucursales = Sucursal.objects.all()
        total_sucursales = sucursales.count()
        
        self.stdout.write(f"\nProcessing {total_sucursales} branch(es)...")
        
        for sucursal in sucursales:
            self.stdout.write(f"\n📍 Branch: {sucursal.nombre}")
            created_count = 0
            
            for category_data in system_categories:
                category, created = TransactionCategory.objects.get_or_create(
                    branch=sucursal,
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
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✅ Created: {category.name} ({category.get_type_display()})")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠️  Already exists: {category.name}")
                    )
            
            if created_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"  🎉 {created_count} new categor{'y' if created_count == 1 else 'ies'} created")
                )
            else:
                self.stdout.write("  ℹ️  All system categories already exist")
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✅ Done! Processed {total_sucursales} branch(es)\n")
        )
