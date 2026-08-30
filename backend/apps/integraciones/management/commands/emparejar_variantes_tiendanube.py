"""
Pair local products with their Tienda Nube variant, by name.

Same shape and the same conservative criteria as `emparejar_sku_conto`, because
the failure mode is the same: a wrong pairing puts the wrong product in the
cart, and the clienta paga por algo que no eligió.

The variant id is what travels in the checkout URL (COMPRA_EN_APP_SPEC.md §5.2),
so a product without it simply cannot be bought from the app.

Read-only by default: propone y vos mirás. Solo `--aplicar` escribe.

    python manage.py emparejar_variantes_tiendanube             # propone
    python manage.py emparejar_variantes_tiendanube --aplicar   # escribe los seguros
"""
import unicodedata
from decimal import Decimal
from difflib import SequenceMatcher

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.integraciones.models import TiendanubeIntegration
from apps.integraciones.tiendanube import TiendanubeClient, TiendanubeError
from apps.inventario.models import Producto

# Mismos dos escalones que el emparejador de Conto: muy parecido y sin
# competencia, o parecido con el segundo muy lejos. Un emparejamiento errado es
# peor que dejarlo para una persona.
AUTO_RULES = [
    (0.88, 0.08),
    (0.70, 0.25),
]
FLOOR = 0.55

# Cuánto puede diferir el precio antes de que un parecido de nombre deje de
# ser creíble. Generoso a propósito: los precios se desfasan solos entre la
# plataforma y Tienda Nube —el sync corre cada tanto (§6.2) y allá puede haber
# una promoción cargada—, así que solo tiene que atajar los disparates. Un
# producto de $19.000 emparejado con uno de $100 es 190 veces, no 1,5.
TOLERANCIA_DE_PRECIO = Decimal('0.5')


def normalize(text):
    """Uppercase, strip accents, keep only letters, digits and single spaces."""
    text = unicodedata.normalize('NFKD', text or '')
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = ''.join(c if c.isalnum() else ' ' for c in text.upper())
    return ' '.join(text.split())


def similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def normalize_sku(sku):
    """Mismo criterio que `ContoScope.normalize_sku`, para que un SKU se lea igual
    venga de donde venga."""
    return (sku or '').strip().upper()


def _a_decimal(valor):
    """El precio de Tienda Nube viene como texto, y a veces no viene."""
    try:
        return Decimal(str(valor))
    except (TypeError, ValueError, ArithmeticError):
        return None


def _precio_creible(producto, candidato):
    """
    Si el precio hace verosímil que sean el mismo producto.

    Es un **testigo, no un emparejador**: solo sirve para desconfiar. Un nombre
    puede parecerse por casualidad —"Serum" contra "Serum Retinol"— y ahí el
    precio es lo único que delata que son cosas distintas.

    Cuando falta cualquiera de los dos precios devuelve verdadero: sin dato no
    se puede desconfiar, y bloquear por ausencia dejaría sin emparejar a
    productos perfectamente válidos.
    """
    nuestro = producto.precio_venta
    suyo = candidato['variantes'][0].get('precio')
    if not nuestro or not suyo or nuestro <= 0 or suyo <= 0:
        return True

    mayor, menor = max(nuestro, suyo), min(nuestro, suyo)
    return (mayor - menor) / mayor <= TOLERANCIA_DE_PRECIO


def nombre_de(valor):
    """
    Tienda Nube devuelve los textos por idioma: `{'es': 'Serum', 'pt': ...}`.

    Se prefiere español y se cae al primero que haya: una tienda argentina que
    igual tenga otro idioma cargado no tiene por qué quedar sin emparejar.
    """
    if isinstance(valor, dict):
        return valor.get('es') or next((v for v in valor.values() if v), '')
    return valor or ''


class Command(BaseCommand):
    help = 'Empareja productos locales con su variante de Tienda Nube por nombre'

    def add_arguments(self, parser):
        parser.add_argument(
            '--centro', type=int,
            help='Centro a emparejar. Por defecto, el único que tenga tienda vinculada'
        )
        parser.add_argument(
            '--aplicar', action='store_true',
            help='Escribir los emparejamientos seguros. Sin esto, solo propone'
        )
        parser.add_argument(
            '--todos', action='store_true',
            help='Incluir productos que ya tienen variante (por defecto solo los vacíos)'
        )

    def handle(self, *args, **options):
        integration = self._get_integration(options)
        self.stdout.write(f'Tienda: {integration.store_name or integration.store_id}')

        try:
            catalogo = self._catalogo(integration)
        except TiendanubeError as exc:
            raise CommandError(f'No se pudo leer Tienda Nube: {exc}')

        if not catalogo:
            raise CommandError('Tienda Nube no devolvió productos')

        # Un producto con varias variantes (talles, tamaños) no se puede resolver
        # por nombre: cuál de las dos es la correcta no está en el nombre del
        # producto. Van a la lista de decisiones humanas.
        emparejables = [c for c in catalogo if len(c['variantes']) == 1]
        multiples = [c for c in catalogo if len(c['variantes']) > 1]

        self.stdout.write(
            f'Catálogo de Tienda Nube: {len(catalogo)} productos · '
            f'{len(multiples)} con más de una variante'
        )

        productos = Producto.objects.filter(
            sucursal__centro_estetica=integration.center,
            activo=True,
        )
        if not options['todos']:
            productos = productos.filter(tiendanube_product_id='')
        productos = list(productos.order_by('nombre'))

        self.stdout.write(f'Productos locales a emparejar: {len(productos)}')
        if not productos:
            self.stdout.write(self.style.SUCCESS(
                'No hay productos sin variante. Nada que emparejar.'
            ))
            return

        # Una variante ya asignada no se puede reasignar: dos productos nuestros
        # apuntando a la misma variante mandarían al carrito el artículo
        # equivocado para uno de los dos.
        tomadas = set(
            Producto.objects.filter(sucursal__centro_estetica=integration.center)
            .exclude(tiendanube_variant_id='')
            .values_list('tiendanube_variant_id', flat=True)
        )

        seguros, dudosos, sin_candidato = [], [], []

        # Primera pasada: el SKU. Un SKU que coincide no es un parecido, es una
        # certeza, así que estos no pasan por similitud de nombre ni por el
        # testigo del precio — y de paso resuelven el caso que el nombre no
        # puede: cuatro productos que se llaman casi igual.
        por_sku, productos = self._emparejar_por_sku(productos, catalogo, tomadas)
        seguros.extend(por_sku)

        for producto in productos:
            ranked = self._rank(producto, emparejables, tomadas)

            if not ranked or ranked[0][0] < FLOOR:
                # Antes de darlo por perdido: puede ser uno de los de varias
                # variantes, y entonces la decisión es de una persona.
                con_variantes = self._rank(producto, multiples, tomadas)
                if con_variantes and con_variantes[0][0] >= FLOOR:
                    dudosos.append((producto, con_variantes[:3], 'varias variantes'))
                else:
                    sin_candidato.append(producto)
                continue

            mejor_score, mejor = ranked[0]
            segundo = ranked[1][0] if len(ranked) > 1 else 0.0
            margen = mejor_score - segundo

            pasa_el_nombre = any(
                mejor_score >= s and margen >= m for s, m in AUTO_RULES
            )
            if pasa_el_nombre and not _precio_creible(producto, mejor):
                # El nombre convence y el precio no. Casi siempre es un producto
                # distinto que se llama parecido, así que lo decide una persona.
                dudosos.append((producto, ranked[:3], 'precio muy distinto'))
            elif pasa_el_nombre:
                seguros.append((producto, mejor, mejor_score))
                tomadas.add(mejor['variantes'][0]['id'])
            else:
                dudosos.append((producto, ranked[:3], 'parecidos'))

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

    def _catalogo(self, integration):
        """
        El catálogo de la tienda, reducido a lo que hace falta para emparejar.

        Se trae el precio además del SKU: no sirve para emparejar, pero sí para
        desconfiar de un parecido de nombre (`_precio_creible`).
        """
        catalogo = []
        for p in TiendanubeClient(integration).iter_products():
            variantes = [
                {
                    'id': str(v.get('id')),
                    'sku': v.get('sku') or '',
                    'precio': _a_decimal(v.get('price')),
                }
                for v in (p.get('variants') or [])
                if v.get('id')
            ]
            if not variantes:
                continue
            catalogo.append({
                'id': str(p.get('id')),
                'nombre': nombre_de(p.get('name')),
                'variantes': variantes,
            })
        return catalogo

    def _emparejar_por_sku(self, productos, catalogo, tomadas):
        """
        Emparejar por SKU exacto, antes de mirar nombres.

        Devuelve `(seguros, los_que_quedan)`. Los que resuelve salen de la lista
        para que la pasada por nombre no vuelva a considerarlos.

        **El SKU ya se leía de Tienda Nube y no se usaba** — se imprimía en el
        reporte de dudosos y nada más. Es la señal más fuerte que hay: dos
        productos con el mismo SKU son el mismo producto, sin importar cómo esté
        escrito el nombre de cada lado.

        Un SKU que aparece más de una vez en Tienda Nube no se usa: si el
        identificador que tenía que ser único está repetido, elegir uno es
        adivinar. Esos caen a la pasada por nombre.
        """
        por_sku = {}
        for candidato in catalogo:
            for variante in candidato['variantes']:
                sku = normalize_sku(variante['sku'])
                if not sku:
                    continue
                # None marca el repetido, para distinguirlo del ausente.
                por_sku[sku] = None if sku in por_sku else (candidato, variante)

        seguros, restantes = [], []
        for producto in productos:
            hit = por_sku.get(normalize_sku(producto.sku))
            if hit is None:
                restantes.append(producto)
                continue

            candidato, variante = hit
            if variante['id'] in tomadas:
                restantes.append(producto)
                continue

            seguros.append((producto, {**candidato, 'variantes': [variante]}, 1.0))
            tomadas.add(variante['id'])

        return seguros, restantes

    def _rank(self, producto, pool, tomadas):
        """Candidatos ordenados por parecido de nombre, el mejor primero."""
        return sorted(
            (
                (similarity(producto.nombre, c['nombre']), c)
                for c in pool
                if not all(v['id'] in tomadas for v in c['variantes'])
            ),
            key=lambda x: -x[0],
        )

    def _get_integration(self, options):
        queryset = TiendanubeIntegration.objects.filter(
            is_active=True
        ).select_related('center')
        if options.get('centro'):
            queryset = queryset.filter(center_id=options['centro'])

        integration = queryset.first()
        if not integration:
            raise CommandError(
                'No hay ninguna tienda de Tienda Nube vinculada. '
                'Usá `vincular_tiendanube` primero.'
            )
        if queryset.count() > 1:
            raise CommandError('Hay más de una tienda vinculada. Usá --centro.')
        return integration

    def _report(self, seguros, dudosos, sin_candidato):
        if seguros:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(
                f'Emparejamientos seguros ({len(seguros)}):'
            ))
            for producto, match, score in seguros:
                # El 100% por SKU y el 100% por nombre no valen lo mismo: uno es
                # una certeza y el otro un parecido perfecto. Quien revisa la
                # lista tiene que poder distinguirlos de un vistazo.
                como = 'SKU ' if score == 1.0 and producto.sku else f'{score:.0%}'
                self.stdout.write(
                    f'  {como:<5} {producto.nombre[:38]:<38} → '
                    f'variante {match["variantes"][0]["id"]:<12} {match["nombre"][:34]}'
                )

        if dudosos:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                f'Requieren decisión humana ({len(dudosos)}):'
            ))
            for producto, candidatos, motivo in dudosos:
                self.stdout.write(f'  {producto.nombre}  (id {producto.id})  [{motivo}]')
                for score, c in candidatos:
                    variantes = ', '.join(
                        v['id'] + (f" (sku {v['sku']})" if v['sku'] else '')
                        for v in c['variantes']
                    )
                    self.stdout.write(f'      {score:.0%}  {c["nombre"][:40]:<40} {variantes}')

        if sin_candidato:
            self.stdout.write('')
            self.stdout.write(
                f'Sin candidato parecido ({len(sin_candidato)}) — '
                f'probablemente no estén publicados en Tienda Nube:'
            )
            for producto in sin_candidato:
                self.stdout.write(f'  {producto.nombre}  (id {producto.id})')

    def _apply(self, seguros):
        if not seguros:
            self.stdout.write('')
            self.stdout.write('No hay emparejamientos seguros para aplicar.')
            return

        with transaction.atomic():
            for producto, match, _score in seguros:
                producto.tiendanube_product_id = match['id']
                producto.tiendanube_variant_id = match['variantes'][0]['id']
                producto.save(update_fields=[
                    'tiendanube_product_id', 'tiendanube_variant_id', 'actualizado_en',
                ])

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'{len(seguros)} producto(s) emparejados con su variante de Tienda Nube.'
        ))
        self.stdout.write(
            'Los dudosos y los sin candidato quedaron sin tocar: se completan a '
            'mano desde la ficha del producto en el CRM. Sin variante, el producto '
            'no muestra el botón de comprar en la app.'
        )
