"""
Break down product income by month, to decide `import_from`.

The center stopped loading Tienda Nube sales by hand at some point, and importing
from Conto over a period that was already loaded would double the income. This
measures where the hole starts instead of guessing: the month where
INCOME_PRODUCT falls to zero — or to services-only noise — is the earliest date
`import_from` can safely take.

Read-only. Meant to be run against production the same way as `diagnostico_sku`:

    docker-compose exec -e DATABASE_URL='<DATABASE_PUBLIC_URL>' \\
        backend python manage.py diagnostico_ingresos
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth

from apps.empleados.models import Sucursal
from apps.finanzas.models import Transaction


class Command(BaseCommand):
    help = 'Desglosa los ingresos por producto mes a mes, por sucursal'

    def add_arguments(self, parser):
        parser.add_argument(
            '--meses', type=int, default=18,
            help='Cuántos meses hacia atrás mostrar (por defecto 18)'
        )
        parser.add_argument(
            '--sucursal', type=int,
            help='Limitar a una sucursal. Por defecto, todas'
        )

    def handle(self, *args, **options):
        branches = Sucursal.objects.select_related('centro_estetica').order_by('id')
        if options.get('sucursal'):
            branches = branches.filter(pk=options['sucursal'])

        if not branches.exists():
            self.stdout.write(self.style.ERROR('No hay sucursales.'))
            return

        for branch in branches:
            self._report(branch, options['meses'])

    def _report(self, branch, meses):
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'{branch.centro_estetica.nombre} — {branch.nombre} (id {branch.pk})'
        ))

        base = (
            Transaction.objects
            .filter(branch=branch, type='INCOME_PRODUCT')
            .annotate(mes=TruncMonth('date'))
        )

        rows = list(
            base.values('mes')
            .annotate(
                n=Count('id'),
                total=Sum('amount'),
                # `registered_by` is null for anything the platform generated on
                # its own, so it is what tells a sale loaded by a person apart
                # from an imported one.
                a_mano=Count('id', filter=Q(registered_by__isnull=False)),
            )
            .order_by('-mes')[:meses]
        )

        # Counted apart on purpose: `conto_sales` is a many-to-many, and joining
        # it into the aggregate above would multiply the rows and inflate `total`.
        de_conto = dict(
            base.filter(conto_sales__isnull=False)
            .values('mes')
            .annotate(n=Count('id', distinct=True))
            .values_list('mes', 'n')
        )
        for row in rows:
            row['de_conto'] = de_conto.get(row['mes'], 0)

        if not rows:
            self.stdout.write('  Sin ingresos por producto registrados.')
            return

        self.stdout.write(
            f'  {"Mes":<9} {"Ventas":>7} {"Monto":>16} '
            f'{"A mano":>7} {"De Conto":>9}'
        )
        for row in rows:
            mes = row['mes'].strftime('%Y-%m')
            vacio = row['a_mano'] == 0 and row['de_conto'] == 0
            linea = (
                f'  {mes:<9} {row["n"]:>7} {row["total"]:>15,.2f} '
                f'{row["a_mano"]:>7} {row["de_conto"]:>9}'
            )
            self.stdout.write(self.style.WARNING(linea) if vacio else linea)

        self._conclusion(rows)

    def _conclusion(self, rows):
        """
        The months are ordered newest first, so the run of months with nothing
        loaded by hand at the top is exactly the hole Conto would fill.
        """
        hueco = []
        for row in rows:
            if row['a_mano'] > 0:
                break
            hueco.append(row['mes'])

        self.stdout.write('')
        if not hueco:
            self.stdout.write(self.style.WARNING(
                '  El mes más reciente ya tiene ventas cargadas a mano. '
                'Importar desde ahí duplicaría ingresos.'
            ))
            return

        desde = min(hueco)
        self.stdout.write(self.style.SUCCESS(
            f'  Sin carga manual desde {desde.strftime("%Y-%m")}. '
            f'"Importar desde" puede arrancar en {desde.strftime("%Y-%m-01")}.'
        ))
        self.stdout.write(
            '  Ojo: los meses sin ninguna transacción no aparecen en la tabla. '
            'Verificá que el hueco sea continuo antes de decidir.'
        )
