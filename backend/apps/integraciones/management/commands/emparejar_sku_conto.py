"""
Pair local products with Conto's catalog by name, and write the SKU.

Needed because Conto's codes are opaque timestamps (`PROD-1778370118853`), so
nobody can assign them by hand without typos. The product *name* is the only
human-meaningful key shared by both systems.

Read-only by default: it proposes and you look. Only `--aplicar` writes.

    python manage.py emparejar_sku_conto              # propone
    python manage.py emparejar_sku_conto --aplicar     # escribe los seguros
"""
import unicodedata
from datetime import timedelta
from difflib import SequenceMatcher

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.integraciones.models import ContoIntegration
from apps.integraciones.services import ContoClient, ContoError
from apps.inventario.models import Producto

# A pairing is written without asking when the name match is strong AND clearly
# ahead of the runner-up. Conservative on purpose: a wrong pairing sends income
# and stock to the wrong product, which is worse than leaving it for a human.
#
# Two tiers, because Conto's names are often the local name plus a suffix
# ("SERUM ÁCIDO HIALURÓNICO DOBLE PESO MOLECULAR - HIDRATACIÓN"), which caps the
# similarity around 0.80 even when the match is obvious. A large gap to the
# runner-up carries as much signal as a high score.
AUTO_RULES = [
    (0.88, 0.08),   # muy parecido y sin competencia cercana
    (0.70, 0.25),   # parecido, pero el segundo queda muy lejos
]
# Below this, the product is reported as having no counterpart in Conto instead
# of cluttering the list that needs decisions.
FLOOR = 0.55
# Window used to find out which SKUs actually appear in sales.
SALES_WINDOW = timedelta(days=90)


def normalize(text):
    """Uppercase, strip accents, keep only letters, digits and single spaces."""
    text = unicodedata.normalize('NFKD', text or '')
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = ''.join(c if c.isalnum() else ' ' for c in text.upper())
    return ' '.join(text.split())


def similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


class Command(BaseCommand):
    help = 'Empareja productos locales con el catálogo de Conto por nombre'

    def add_arguments(self, parser):
        parser.add_argument(
            '--integration-id', type=int,
            help='Integración a usar. Por defecto, la única que exista'
        )
        parser.add_argument(
            '--aplicar', action='store_true',
            help='Escribir los emparejamientos seguros. Sin esto, solo propone'
        )
        parser.add_argument(
            '--todos', action='store_true',
            help='Incluir productos que ya tienen SKU (por defecto solo los vacíos)'
        )

    def handle(self, *args, **options):
        integration = self._get_integration(options)
        scope_branch = integration.branch

        self.stdout.write(f'Sucursal: {scope_branch}')

        client = ContoClient(integration)

        try:
            catalog = [
                {
                    'sku': p.get('sku'),
                    'nombre': p.get('nombre') or '',
                    'activo': p.get('activo', True),
                }
                for p in client.iter_stock()
                if (p.get('sku') or '').strip()
            ]
            vendidos = self._skus_con_ventas(client, integration)
        except ContoError as exc:
            raise CommandError(f'No se pudo leer Conto: {exc}')

        if not catalog:
            raise CommandError('Conto no devolvió productos')

        # Conto's catalog holds the same product twice: once with a slug code and
        # once with a generated `PROD-<timestamp>` one. Both match the name
        # perfectly, so name similarity alone can never break the tie.
        #
        # Two signals resolve it, and they agree: Conto marks the slug duplicates
        # as inactive, and only the generated codes appear in sales. Sales are the
        # more fundamental of the two — pairing exists to attribute income — but
        # requiring both is cheap and neither is a naming convention that could
        # change. Anything failing either test is only used as a fallback.
        preferidos = [
            c for c in catalog if c['activo'] and c['sku'] in vendidos
        ]
        inactivos = sum(1 for c in catalog if not c['activo'])
        self.stdout.write(
            f'Catálogo de Conto: {len(catalog)} productos · '
            f'{inactivos} inactivos · '
            f'{len(preferidos)} activos con ventas en {SALES_WINDOW.days} días'
        )

        productos = Producto.objects.filter(sucursal=scope_branch)
        if not options['todos']:
            productos = productos.filter(sku='')
        productos = list(productos.order_by('nombre'))

        self.stdout.write(f'Productos locales a emparejar: {len(productos)}')

        if not productos:
            self.stdout.write(self.style.SUCCESS(
                'No hay productos sin SKU. Nada que emparejar.'
            ))
            return

        # SKUs already used in this branch cannot be assigned again: the
        # unique_sku_per_sucursal constraint would reject them.
        tomados = set(
            Producto.objects.filter(sucursal=scope_branch)
            .exclude(sku='')
            .values_list('sku', flat=True)
        )

        seguros, dudosos, sin_candidato = [], [], []

        for producto in productos:
            # Candidates that sell come first. Only if none of them resembles the
            # product do we fall back to the rest of the catalog.
            ranked = self._rank(producto, preferidos, tomados)
            fuente = 'con ventas'
            if not ranked or ranked[0][0] < FLOOR:
                fallback = self._rank(producto, catalog, tomados)
                if fallback and fallback[0][0] > (ranked[0][0] if ranked else 0):
                    ranked, fuente = fallback, 'sin ventas'

            if not ranked or ranked[0][0] < FLOOR:
                sin_candidato.append(producto)
                continue

            best_score, best = ranked[0]
            runner_up = ranked[1][0] if len(ranked) > 1 else 0.0
            margin = best_score - runner_up

            if any(best_score >= s and margin >= m for s, m in AUTO_RULES):
                seguros.append((producto, best, best_score, fuente))
                tomados.add(best['sku'])
            else:
                dudosos.append((producto, ranked[:3], fuente))

        self._report(seguros, dudosos, sin_candidato)

        if not options['aplicar']:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                'Modo propuesta: no se escribió nada. '
                'Volvé a correr con --aplicar para guardar los seguros.'
            ))
            return

        self._apply(seguros)

    # -- helpers ----------------------------------------------------------- #

    def _rank(self, producto, pool, tomados):
        """Candidates sorted by name similarity, best first."""
        return sorted(
            (
                (similarity(producto.nombre, c['nombre']), c)
                for c in pool
                if c['sku'] not in tomados
            ),
            key=lambda x: -x[0],
        )

    def _skus_con_ventas(self, client, integration):
        """
        SKUs that appear in real sales, on the channels being imported.

        This is what breaks the tie between Conto's duplicate catalog entries,
        and it is the better signal anyway: pairing exists to attribute income.
        """
        desde = timezone.now() - SALES_WINDOW
        canales = integration.channels_to_import or []
        vistos = set()

        for voucher in client.iter_sales(desde):
            if canales and voucher.get('canal') not in canales:
                continue
            for item in voucher.get('items') or []:
                if item.get('tipo') == 'PRODUCTO' and item.get('sku'):
                    vistos.add(item['sku'])

        return vistos

    def _get_integration(self, options):
        queryset = ContoIntegration.objects.select_related('branch', 'center')
        if options.get('integration_id'):
            queryset = queryset.filter(pk=options['integration_id'])

        integration = queryset.first()
        if not integration:
            raise CommandError('No hay ninguna integración cargada.')
        if queryset.count() > 1:
            raise CommandError('Hay más de una integración. Usá --integration-id.')
        if not integration.is_linked:
            raise CommandError(
                'La integración no tiene una cuenta verificada. '
                'Verificá la vinculación primero.'
            )
        return integration

    def _report(self, seguros, dudosos, sin_candidato):
        if seguros:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(
                f'Emparejamientos seguros ({len(seguros)}):'
            ))
            for producto, match, score, fuente in seguros:
                self.stdout.write(
                    f'  {score:.0%}  {producto.nombre[:38]:<38} → '
                    f'{match["sku"]:<22} {match["nombre"][:34]}  [{fuente}]'
                )

        if dudosos:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                f'Requieren decisión humana ({len(dudosos)}):'
            ))
            for producto, candidatos, fuente in dudosos:
                self.stdout.write(
                    f'  {producto.nombre}  (id {producto.id})  [{fuente}]'
                )
                for score, c in candidatos:
                    self.stdout.write(
                        f'      {score:.0%}  {c["sku"]:<22} {c["nombre"][:50]}'
                    )

        if sin_candidato:
            self.stdout.write('')
            self.stdout.write(
                f'Sin candidato parecido ({len(sin_candidato)}) — '
                f'probablemente no existan en Conto:'
            )
            for producto in sin_candidato:
                self.stdout.write(f'  {producto.nombre}  (id {producto.id})')

    def _apply(self, seguros):
        if not seguros:
            self.stdout.write('')
            self.stdout.write('No hay emparejamientos seguros para aplicar.')
            return

        with transaction.atomic():
            for producto, match, _score, _fuente in seguros:
                producto.sku = match['sku']
                producto.save(update_fields=['sku', 'actualizado_en'])

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'{len(seguros)} producto(s) actualizados con su SKU de Conto.'
        ))
        self.stdout.write(
            'Los dudosos y los sin candidato quedaron sin tocar: resolvelos a mano '
            'desde el admin, o dejalos sin SKU y que Conto cree su propia versión.'
        )
