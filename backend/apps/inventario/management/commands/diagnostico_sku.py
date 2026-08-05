"""
Read-only diagnostic of the state of Producto.sku per branch.

The SKU is going to be the join key against Conto's catalog, so before adding a
unique constraint we need to know what the current data looks like: how many are
empty, how many collide, and whether normalizing (upper + strip) creates new
collisions.

This command does NOT modify anything.

    docker-compose exec backend python manage.py diagnostico_sku
"""
from collections import Counter, defaultdict

from django.core.management.base import BaseCommand

from apps.empleados.models import Sucursal
from apps.inventario.models import Producto


def normalizar(sku):
    """Same normalization the integration will use: uppercase, no surrounding spaces."""
    return (sku or '').strip().upper()


class Command(BaseCommand):
    help = 'Reporta el estado de Producto.sku por sucursal (solo lectura)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sucursal-id',
            type=int,
            help='Analizar solo una sucursal'
        )
        parser.add_argument(
            '--detalle',
            action='store_true',
            help='Listar los productos con problemas, no solo los totales'
        )

    def handle(self, *args, **options):
        sucursales = Sucursal.objects.all().order_by('centro_estetica', 'nombre')
        if options.get('sucursal_id'):
            sucursales = sucursales.filter(id=options['sucursal_id'])

        if not sucursales.exists():
            self.stdout.write(self.style.ERROR('No hay sucursales que analizar'))
            return

        detalle = options.get('detalle')
        total_global = defaultdict(int)

        for sucursal in sucursales:
            productos = list(
                Producto.objects.filter(sucursal=sucursal).only(
                    'id', 'nombre', 'sku', 'codigo_barras', 'activo'
                )
            )

            self.stdout.write('')
            self.stdout.write(self.style.MIGRATE_HEADING(
                f'{sucursal.centro_estetica.nombre} / {sucursal.nombre} (id {sucursal.id})'
            ))

            if not productos:
                self.stdout.write('  Sin productos cargados')
                continue

            vacios = [p for p in productos if not normalizar(p.sku)]
            con_sku = [p for p in productos if normalizar(p.sku)]

            # Collisions on the raw value vs. on the normalized value.
            crudos = Counter(p.sku for p in con_sku)
            normalizados = Counter(normalizar(p.sku) for p in con_sku)

            dup_crudos = {k: v for k, v in crudos.items() if v > 1}
            dup_norm = {k: v for k, v in normalizados.items() if v > 1}
            # Collisions that appear only after normalizing (e.g. "abc" vs "ABC ").
            dup_solo_al_normalizar = {
                k: v for k, v in dup_norm.items() if k not in dup_crudos
            }

            con_barras = [p for p in productos if p.codigo_barras]

            self.stdout.write(f'  Productos:                  {len(productos)}')
            self.stdout.write(f'  Con SKU:                    {len(con_sku)}')

            estilo_vacios = self.style.WARNING if vacios else self.style.SUCCESS
            self.stdout.write(estilo_vacios(
                f'  SKU vacío (a backfillear):  {len(vacios)}'
            ))

            estilo_dup = self.style.ERROR if dup_norm else self.style.SUCCESS
            self.stdout.write(estilo_dup(
                f'  SKU duplicado:              {len(dup_norm)} valores, '
                f'{sum(dup_norm.values())} productos'
            ))

            if dup_solo_al_normalizar:
                self.stdout.write(self.style.WARNING(
                    f'    de los cuales {len(dup_solo_al_normalizar)} colisionan '
                    f'solo al normalizar (mayúsculas/espacios)'
                ))

            self.stdout.write(f'  Con código de barras:       {len(con_barras)}')

            total_global['productos'] += len(productos)
            total_global['vacios'] += len(vacios)
            total_global['dup_productos'] += sum(dup_norm.values())

            if detalle:
                if vacios:
                    self.stdout.write('')
                    self.stdout.write('  Sin SKU:')
                    for p in vacios:
                        activo = '' if p.activo else ' [inactivo]'
                        self.stdout.write(f'    #{p.id} {p.nombre}{activo}')

                if dup_norm:
                    self.stdout.write('')
                    self.stdout.write('  SKU duplicados:')
                    for sku_norm in sorted(dup_norm):
                        self.stdout.write(f'    {sku_norm}:')
                        for p in con_sku:
                            if normalizar(p.sku) == sku_norm:
                                activo = '' if p.activo else ' [inactivo]'
                                self.stdout.write(
                                    f'      #{p.id} {p.nombre} '
                                    f'(sku crudo: {p.sku!r}){activo}'
                                )

        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Total'))
        self.stdout.write(f"  Productos:        {total_global['productos']}")
        self.stdout.write(f"  Sin SKU:          {total_global['vacios']}")
        self.stdout.write(f"  En colisión:      {total_global['dup_productos']}")

        self.stdout.write('')
        if total_global['dup_productos'] or total_global['vacios']:
            self.stdout.write(self.style.WARNING(
                'Hay que resolver vacíos y colisiones antes de agregar el '
                'constraint único por sucursal.'
            ))
            self.stdout.write(
                '  Corré con --detalle para ver qué productos son.'
            )
        else:
            self.stdout.write(self.style.SUCCESS(
                'El constraint único por sucursal se puede aplicar sin backfill.'
            ))
