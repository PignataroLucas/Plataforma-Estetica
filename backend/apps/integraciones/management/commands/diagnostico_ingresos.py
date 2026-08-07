"""
Break down product income by month, to decide `import_from`.

The center stopped loading Tienda Nube sales by hand at some point, and importing
from Conto over a period that was already loaded would double the income. This
measures where the hole starts instead of guessing.

What matters is not just how much came in each month but **how it got there**,
because only one of the three origins can collide with an import:

- `De Conto`   — already imported. Re-importing is deduplicated by `voucher_id`.
- `Mostrador`  — moved stock (Mi Caja or an inventory movement). Those are sales
                 made in person, which Conto files under `presencial` and we do
                 not import, so they cannot be duplicated by importing Tienda
                 Nube.
- `A mano`     — typed straight into Finanzas, no stock movement behind it. This
                 is the only column that can be an online sale copied by hand,
                 and therefore the only one that decides how far back to go.

Every month in the window is printed, including the empty ones. A month with no
income at all has no rows in the database, and leaving it out of the table is
what turns a hole into an invisible hole.

Read-only. Meant to be run against production the same way as `diagnostico_sku`:

    docker-compose exec -e DATABASE_URL='postgresql://...' \\
        backend python manage.py diagnostico_ingresos
"""
from datetime import date

from django.core.management.base import BaseCommand
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

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

        meses_del_periodo = self._calendar(meses)
        por_mes = self._income_by_month(branch)
        rows = [
            por_mes.get(mes, self._empty(mes)) for mes in meses_del_periodo
        ]

        if not por_mes:
            self.stdout.write(
                f'  Sin ingresos por producto en los últimos {meses} meses.'
            )
            return

        self.stdout.write(
            f'  {"Mes":<9} {"Ventas":>7} {"Monto":>16} '
            f'{"A mano":>7} {"Mostrador":>10} {"De Conto":>9}'
        )
        for row in rows:
            linea = (
                f'  {row["mes"].strftime("%Y-%m"):<9} {row["n"]:>7} '
                f'{row["total"]:>15,.2f} {row["a_mano"]:>7} '
                f'{row["mostrador"]:>10} {row["de_conto"]:>9}'
            )
            self.stdout.write(self.style.WARNING(linea) if row['n'] == 0 else linea)

        self._conclusion(rows)
        self._older_than_window(branch, meses_del_periodo[-1])

    def _calendar(self, meses):
        """Every month in the window, newest first, so the gaps are visible."""
        today = timezone.localdate()
        year, month = today.year, today.month
        out = []
        for _ in range(meses):
            out.append(date(year, month, 1))
            month -= 1
            if month == 0:
                year, month = year - 1, 12
        return out

    def _empty(self, mes):
        return {'mes': mes, 'n': 0, 'total': 0, 'a_mano': 0,
                'mostrador': 0, 'de_conto': 0}

    def _income_by_month(self, branch):
        base = (
            Transaction.objects
            .filter(branch=branch, type='INCOME_PRODUCT')
            .annotate(mes=TruncMonth('date'))
        )

        rows = {
            row['mes']: row
            for row in base.values('mes').annotate(
                n=Count('id'),
                total=Sum('amount'),
                # `inventory_movement` is what separates a sale that moved stock
                # from one typed into Finanzas. Both are forward relations, so
                # neither multiplies the rows.
                mostrador=Count('id', filter=Q(inventory_movement__isnull=False)),
                a_mano=Count('id', filter=Q(
                    inventory_movement__isnull=True, registered_by__isnull=False
                )),
            )
        }

        # Counted apart on purpose: `conto_sales` is a many-to-many, and joining
        # it into the aggregate above would multiply the rows and inflate `total`.
        for mes, n in (
            base.filter(conto_sales__isnull=False)
            .values('mes')
            .annotate(n=Count('id', distinct=True))
            .values_list('mes', 'n')
        ):
            if mes in rows:
                rows[mes]['de_conto'] = n

        for row in rows.values():
            row.setdefault('de_conto', 0)
        return rows

    def _conclusion(self, rows):
        """
        Rows are newest first, so the run of months at the top with nothing typed
        by hand is exactly the hole an import would fill.
        """
        hueco = [row for row in rows if row['a_mano'] == 0]
        corte = next((row for row in rows if row['a_mano'] > 0), None)
        if corte:
            hueco = [row for row in rows if row['mes'] > corte['mes']]

        self.stdout.write('')
        if not hueco:
            self.stdout.write(self.style.WARNING(
                '  El mes en curso ya tiene ventas cargadas a mano. '
                'Importar desde ahí duplicaría ingresos.'
            ))
            return

        desde = min(row['mes'] for row in hueco)
        self.stdout.write(self.style.SUCCESS(
            f'  Sin carga manual desde {desde.strftime("%Y-%m")}. '
            f'"Importar desde" puede arrancar en {desde.strftime("%Y-%m-01")}.'
        ))

        if corte and corte['a_mano'] < corte['n']:
            return
        if corte:
            self.stdout.write(
                f'  Para ir más atrás hay que revisar las {corte["a_mano"]} '
                f'cargadas a mano en {corte["mes"].strftime("%Y-%m")}: si son '
                f'ventas de mostrador y no de Tienda Nube, no se duplican.'
            )

    def _older_than_window(self, branch, first_month):
        """A hole is only trustworthy if nothing older is being cut off silently."""
        older = Transaction.objects.filter(
            branch=branch, type='INCOME_PRODUCT', date__lt=first_month
        ).count()
        if older:
            self.stdout.write(
                f'  Hay {older} ventas anteriores a '
                f'{first_month.strftime("%Y-%m")}, fuera de la ventana. '
                f'Usá --meses para verlas.'
            )
