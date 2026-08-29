"""
Ensayar la vuelta de una compra de la app, sin que nadie compre.

    python manage.py simular_venta_app --cupon APP-XK4M2PQR
    python manage.py simular_venta_app --cupon APP-XK4M2PQR --deshacer

Arma el comprobante que mandaría Conto por una venta hecha con ese cupón y lo
pasa por el importador de siempre. Sirve para ver de verdad —no en un test— la
transacción creada, la venta marcada como originada en la app, el cupón marcado
como usado y la clienta identificada.

**Por qué hace falta.** Los pasos 10 y 11 del §4 del COMPRA_EN_APP_SPEC.md son
los únicos que no se pueden ejercitar contra la tienda de demostración: Conto
mira la cuenta del centro, que está atada a la tienda real, así que una compra en
la demo nunca vuelve por ahí. Sin esto, la mitad de atrás queda sin probar hasta
la primera venta de producción.

**Lo que esto NO prueba, y es justamente lo que falta confirmar:** que Conto
mande el campo `cupon` en el comprobante. Eso lo contesta `verificar_conto`
contra producción (§7.1). Acá el campo se da por venido, porque el objetivo es
probar nuestra mitad.

El comprobante se arma con `id` derivado del código del cupón, así que correrlo
dos veces sobre el mismo cupón no duplica nada: cae en la misma fila y el
importador es idempotente.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as db_transaction
from django.utils import timezone

from apps.integraciones.models import ContoIntegration, ContoSale, CuponApp
from apps.integraciones.sync import SalesImporter
from apps.inventario.models import Producto

CENTAVO = Decimal('0.01')

# Prefijo del `id` del comprobante simulado. Que se distinga a simple vista en el
# admin importa: estas filas generan transacciones reales en el módulo
# financiero, y confundir una con una venta de verdad ensucia la caja.
PREFIJO = 'SIM-'


class Command(BaseCommand):
    help = 'Simula la venta que volvería de Conto por un cupón de la app'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cupon',
            required=True,
            help='Código del cupón emitido por la app (con el prefijo APP-)',
        )
        parser.add_argument(
            '--producto',
            type=int,
            action='append',
            dest='productos',
            help='ID del producto vendido. Repetible. Por defecto, uno del centro',
        )
        parser.add_argument(
            '--cantidad',
            type=int,
            default=1,
            help='Unidades de cada producto (default: 1)',
        )
        parser.add_argument(
            '--deshacer',
            action='store_true',
            help='Borra la venta simulada, sus transacciones, y libera el cupón',
        )
        # Genera ingresos en el módulo financiero. En la base del centro eso es
        # plata que no entró, y desde adentro no hay forma de distinguir un
        # ensayo de un error.
        parser.add_argument(
            '--forzar',
            action='store_true',
            help='Permite correrlo con DEBUG apagado. Crea transacciones reales',
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options['forzar']:
            raise CommandError(
                "Esto crea transacciones en el módulo financiero, así que con "
                "DEBUG apagado no corre. Si de verdad querés ensayar contra esta "
                "base, pasá --forzar y acordate de --deshacer después."
            )

        cupon = self._buscar_cupon(options['cupon'])
        integration = self._integracion_de_conto(cupon)

        if options['deshacer']:
            return self._deshacer(cupon, integration)

        return self._simular(cupon, integration, options)

    # -- simular ----------------------------------------------------------- #

    def _simular(self, cupon, integration, options):
        # Sin esto, volver a correrlo reimporta el mismo comprobante y crea una
        # transacción nueva: `_process_sale` hace `transactions.set(...)`, que
        # reemplaza el vínculo pero no borra la fila anterior. Quedaría un
        # ingreso huérfano en el módulo financiero por cada corrida — justo la
        # basura que este comando existe para no dejar.
        ya_existe = ContoSale.objects.filter(
            integration=integration, voucher_id=f'{PREFIJO}{cupon.code}'
        ).exists()
        if ya_existe:
            raise CommandError(
                f"Ya hay una venta simulada para {cupon.code}. Deshacela antes "
                f"de volver a ensayar:\n"
                f"  python manage.py simular_venta_app --cupon {cupon.code} --deshacer"
            )

        productos = self._resolver_productos(cupon, options['productos'])
        cantidad = max(1, options['cantidad'])

        voucher = self._armar_voucher(cupon, productos, cantidad)

        self.stdout.write(f"Cupón: {cupon.code} ({cupon.percentage}%)")
        self.stdout.write(f"Clienta del cupón: {cupon.cliente or 's/d'}")
        for producto in productos:
            self.stdout.write(
                f"  {cantidad} x {producto.nombre} "
                f"(SKU {producto.sku or 's/d'}) @ {producto.precio_venta_final}"
            )
        self.stdout.write(f"Descuento: {voucher['descuento_cupon']}")
        self.stdout.write(f"Total: {voucher['total']}")
        self.stdout.write('')

        # La fila se crea acá y el importador la vuelve a encontrar por
        # (integración, voucher_id). Es el mismo camino que usa el botón
        # «Reprocesar» del admin.
        with db_transaction.atomic():
            venta = ContoSale.objects.create(
                integration=integration,
                voucher_id=voucher['id'],
                payload=voucher,
                channel=voucher['canal'],
                status=ContoSale.Status.PENDING,
            )

        resultado = SalesImporter(integration).reprocess(venta)
        venta.refresh_from_db()
        cupon.refresh_from_db()

        self._informar(venta, cupon, resultado)

    def _armar_voucher(self, cupon, productos, cantidad):
        """
        El comprobante como lo mandaría Conto.

        La coherencia importa más que los números: el importador compara la suma
        de las líneas contra el total declarado y marca un descuadre si no dan.
        Un ensayo que arranca descuadrado no prueba nada, así que el descuento se
        calcula sobre el subtotal y el total sale de restarlo.

        El descuento viaja como una línea de tipo DESCUENTO —así lo manda Conto—
        *y* en el campo `descuento_cupon`, que es la columna que después lee la
        atribución.
        """
        lineas = []
        subtotal = Decimal('0.00')
        for producto in productos:
            unitario = producto.precio_venta_final
            subtotal += unitario * cantidad
            lineas.append({
                'tipo': 'PRODUCTO',
                'sku': producto.sku or '',
                'nombre': producto.nombre,
                'cantidad': cantidad,
                'precio_unitario': f'{unitario}',
                'costo_unitario': f'{producto.precio_costo or 0}',
            })

        descuento = (subtotal * cupon.percentage / 100).quantize(
            CENTAVO, rounding=ROUND_HALF_UP
        )
        total = subtotal.quantize(CENTAVO) - descuento

        if descuento > 0:
            lineas.append({
                'tipo': 'DESCUENTO',
                'nombre': f'Cupón {cupon.code}',
                'cantidad': 1,
                'precio_unitario': f'{descuento}',
            })

        ahora = timezone.localtime()
        return {
            'id': f'{PREFIJO}{cupon.code}',
            'tipo': 'VENTA',
            'relacionada_con': None,
            # Tiene que ser un canal que la integración importe, o el importador
            # la omite antes de llegar a crear nada.
            'canal': 'tiendanube',
            'orden_externa_id': f'{PREFIJO}{cupon.pk}',
            'fecha': ahora.strftime('%Y-%m-%d'),
            'actualizado_en': ahora.isoformat(),
            'estado': 'PAGADO',
            'medio_pago': 'transferencia',
            'gateway_origen': 'mercadopago',
            'total': f'{total}',
            'cliente': None,
            'items': lineas,
            # Los cuatro campos que Conto agregó en agosto de 2026. `origen_venta`
            # viene 'store' a propósito: una compra desde la app llega igual que
            # una del navegador, y por eso la atribución va por el cupón (§6.3).
            'origen_venta': 'store',
            'app_origen': None,
            'cupon': cupon.code,
            'descuento_cupon': f'{descuento}',
        }

    def _informar(self, venta, cupon, resultado):
        estado = venta.get_status_display()
        self.stdout.write(f"Comprobante {venta.voucher_id}: {estado}")

        if resultado.errors:
            for error in resultado.errors:
                self.stdout.write(self.style.ERROR(f"  {error}"))
            raise CommandError('La venta simulada no se pudo importar')

        transacciones = list(venta.transactions.all())
        for transaccion in transacciones:
            self.stdout.write(
                f"  Transacción #{transaccion.pk}: {transaccion.get_type_display()} "
                f"${transaccion.amount} — {transaccion.description}"
            )

        if venta.total_discrepancy is not None:
            self.stdout.write(self.style.WARNING(
                f"  Descuadre contra el total: {venta.total_discrepancy}"
            ))

        self.stdout.write('')
        if venta.es_venta_de_la_app:
            self.stdout.write(self.style.SUCCESS(
                f"Atribuida a la app por el cupón {venta.cupon_app.code}"
            ))
            self.stdout.write(f"Cupón usado el: {cupon.used_at}")
            clienta = transacciones[0].client if transacciones else None
            self.stdout.write(f"Clienta en las transacciones: {clienta or 's/d'}")
        else:
            self.stdout.write(self.style.ERROR(
                "NO quedó atribuida a la app. El código llegó en el comprobante "
                "pero no matcheó ningún CuponApp del centro."
            ))

        self.stdout.write('')
        self.stdout.write(
            f"Para revertirlo: python manage.py simular_venta_app "
            f"--cupon {cupon.code} --deshacer"
        )

    # -- deshacer ---------------------------------------------------------- #

    def _deshacer(self, cupon, integration):
        """
        Sacar el ensayo de encima.

        Importa que exista: sin esto, cada ensayo deja ingresos que no entraron
        en el módulo financiero y en los números de analytics (§5.7). El cupón
        también se libera, para poder volver a ensayar con el mismo.
        """
        venta = ContoSale.objects.filter(
            integration=integration, voucher_id=f'{PREFIJO}{cupon.code}'
        ).first()

        if venta is None:
            self.stdout.write('No hay ninguna venta simulada para ese cupón.')
            return

        with db_transaction.atomic():
            transacciones = list(venta.transactions.all())
            borradas = len(transacciones)
            for transaccion in transacciones:
                transaccion.delete()
            venta.delete()

            if cupon.used_at:
                cupon.used_at = None
                cupon.save(update_fields=['used_at'])

        self.stdout.write(f"Venta simulada borrada, con {borradas} transacción(es).")
        self.stdout.write(f"Cupón {cupon.code} liberado para volver a ensayar.")

    # -- resolución -------------------------------------------------------- #

    def _buscar_cupon(self, codigo):
        cupon = (
            CuponApp.objects
            .filter(code__iexact=codigo.strip())
            .select_related('cliente', 'integration__center')
            .first()
        )
        if cupon is None:
            raise CommandError(
                f"No existe el cupón {codigo!r}. Los emite la app al tocar "
                f"«Comprar»; mirá los últimos en el admin, en «Cupones de la app»."
            )
        return cupon

    def _integracion_de_conto(self, cupon):
        centro = cupon.integration.center
        integration = (
            ContoIntegration.objects
            .filter(center=centro)
            .select_related('branch', 'center')
            .first()
        )
        if integration is None:
            raise CommandError(
                f"El centro «{centro.nombre}» no tiene integración con Conto, "
                f"que es por donde vuelven las ventas."
            )
        if integration.branch is None:
            raise CommandError(
                "La integración con Conto no tiene sucursal asignada: las "
                "transacciones no sabrían dónde ir."
            )
        return integration

    def _resolver_productos(self, cupon, ids):
        """
        Qué se vendió.

        El carrito vive en el teléfono y no se guarda del lado del servidor, así
        que el cupón no sabe qué se compró. Si no se pasa nada, se agarra un
        producto con SKU del centro: sin SKU el importador no lo encuentra y la
        transacción queda sin producto asociado.
        """
        centro = cupon.integration.center
        base = Producto.objects.filter(
            sucursal__centro_estetica=centro, activo=True
        ).exclude(sku='')

        if ids:
            productos = list(base.filter(id__in=ids))
            faltantes = set(ids) - {p.id for p in productos}
            if faltantes:
                raise CommandError(
                    f"Estos productos no son del centro «{centro.nombre}», no "
                    f"están activos o no tienen SKU: {sorted(faltantes)}"
                )
            return productos

        producto = base.order_by('id').first()
        if producto is None:
            raise CommandError(
                f"El centro «{centro.nombre}» no tiene ningún producto activo "
                f"con SKU para armar la venta."
            )
        return [producto]
