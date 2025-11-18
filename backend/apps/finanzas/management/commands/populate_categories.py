"""
Management command to populate default financial transaction categories
for all branches or a specific branch.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.empleados.models import Sucursal
from apps.finanzas.models import TransactionCategory


# Default system categories (names in Spanish for UI display)
DEFAULT_CATEGORIES = {
    'EXPENSE': {
        'Alquileres': {
            'color': '#EF4444',
            'order': 1,
            'subcategories': ['Alquiler Local', 'Alquiler Equipamiento', 'Alquiler Máquina']
        },
        'Salarios y Cargas Sociales': {
            'color': '#F59E0B',
            'order': 2,
            'subcategories': ['Sueldos Personal', 'Comisiones', 'Cargas Sociales', 'Aguinaldo']
        },
        'Insumos y Productos': {
            'color': '#8B5CF6',
            'order': 3,
            'subcategories': ['Productos Tratamiento', 'Material Descartable', 'Productos Limpieza']
        },
        'Servicios': {
            'color': '#3B82F6',
            'order': 4,
            'subcategories': ['Luz', 'Agua', 'Gas', 'Internet', 'Teléfono']
        },
        'Marketing y Publicidad': {
            'color': '#EC4899',
            'order': 5,
            'subcategories': ['Publicidad Digital', 'Publicidad Tradicional', 'Eventos y Promociones']
        },
        'Mantenimiento': {
            'color': '#6366F1',
            'order': 6,
            'subcategories': ['Mantenimiento Edificio', 'Mantenimiento Equipos', 'Reparaciones']
        },
        'Impuestos y Tasas': {
            'color': '#EF4444',
            'order': 7,
            'subcategories': ['Impuestos Nacionales', 'Impuestos Provinciales', 'Tasas Municipales']
        },
        'Otros Gastos': {
            'color': '#6B7280',
            'order': 8,
            'subcategories': []
        }
    },
    'INCOME': {
        'Servicios': {
            'color': '#10B981',
            'order': 1,
            'subcategories': []  # Will be generated dynamically from services offered
        },
        'Venta de Productos': {
            'color': '#059669',
            'order': 2,
            'subcategories': []
        },
        'Otros Ingresos': {
            'color': '#6B7280',
            'order': 3,
            'subcategories': []
        }
    }
}


class Command(BaseCommand):
    help = 'Populate default transaction categories for branches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--branch-id',
            type=int,
            help='Specific branch ID to populate categories for'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Populate categories for all branches'
        )

    def handle(self, *args, **options):
        branch_id = options.get('branch_id')
        all_branches = options.get('all')

        if branch_id:
            # Populate for specific branch
            try:
                branch = Sucursal.objects.get(id=branch_id)
                self.populate_branch_categories(branch)
            except Sucursal.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Branch with ID {branch_id} does not exist')
                )
                return

        elif all_branches:
            # Populate for all branches
            branches = Sucursal.objects.all()
            self.stdout.write(f'Found {branches.count()} branches')

            for branch in branches:
                self.populate_branch_categories(branch)

        else:
            self.stdout.write(
                self.style.ERROR('Please specify --branch-id or --all')
            )
            return

        self.stdout.write(
            self.style.SUCCESS('✅ Category population completed successfully!')
        )

    @transaction.atomic
    def populate_branch_categories(self, branch):
        """Populate categories for a specific branch"""
        self.stdout.write(f'\n📍 Populating categories for branch: {branch.nombre}')

        created_count = 0
        skipped_count = 0

        # Process each category type (INCOME, EXPENSE)
        for category_type, categories in DEFAULT_CATEGORIES.items():
            self.stdout.write(f'\n  Processing {category_type} categories...')

            # Process each main category
            for category_name, category_data in categories.items():
                # Check if main category already exists
                main_category, created = TransactionCategory.objects.get_or_create(
                    branch=branch,
                    name=category_name,
                    type=category_type,
                    parent_category=None,
                    defaults={
                        'color': category_data['color'],
                        'order': category_data['order'],
                        'is_system_category': True,
                        'is_active': True
                    }
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'    ✅ Created: {category_name}')
                    )
                    created_count += 1
                else:
                    self.stdout.write(f'    ⏭️  Skipped (exists): {category_name}')
                    skipped_count += 1

                # Process subcategories
                for subcategory_name in category_data.get('subcategories', []):
                    subcategory, sub_created = TransactionCategory.objects.get_or_create(
                        branch=branch,
                        name=subcategory_name,
                        type=category_type,
                        parent_category=main_category,
                        defaults={
                            'color': category_data['color'],
                            'is_system_category': True,
                            'is_active': True
                        }
                    )

                    if sub_created:
                        self.stdout.write(
                            self.style.SUCCESS(f'      ✅ Created subcategory: {subcategory_name}')
                        )
                        created_count += 1
                    else:
                        self.stdout.write(f'      ⏭️  Skipped (exists): {subcategory_name}')
                        skipped_count += 1

        self.stdout.write(
            f'\n  📊 Summary for {branch.nombre}: {created_count} created, {skipped_count} skipped'
        )
