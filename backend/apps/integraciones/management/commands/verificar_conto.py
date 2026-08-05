"""
Contract check against a live Conto instance.

Read-only: it queries the three endpoints and reports whether the responses
match CONTO_API_REQUIREMENTS.md. Nothing is written to our database and nothing
is written to Conto.

Runs from this project, so it is pointed at Conto's deployed URL rather than run
by Conto's team. Its output is shareable as-is: it names each requirement and
whether it is met, which turns "is it ready?" into a report instead of a
conversation.

    # against a stored integration
    docker-compose exec backend python manage.py verificar_conto

    # before any integration exists; asks for the token so it stays out of
    # the shell history
    docker-compose exec backend python manage.py verificar_conto --base-url https://conto.example
"""
from datetime import datetime, timedelta
from getpass import getpass

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.integraciones.models import ContoIntegration
from apps.integraciones.services import ContoClient, ContoError


class Check:
    """One contract requirement and how it turned out."""

    OK = 'OK'
    FAIL = 'FALLA'
    WARN = 'AVISO'
    SKIP = 'N/D'

    def __init__(self, name, status, detail=''):
        self.name = name
        self.status = status
        self.detail = detail


class Command(BaseCommand):
    help = 'Verifica que una instancia de Conto cumpla el contrato acordado'

    def add_arguments(self, parser):
        parser.add_argument(
            '--integration-id',
            type=int,
            help='Integración a usar. Por defecto, la única que exista'
        )
        parser.add_argument(
            '--base-url',
            help='Probar contra esta URL en vez de la de la integración. '
                 'Pide el token por consola para no dejarlo en el historial'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Ventana de ventas a consultar, en días (default 30)'
        )

    # -- entry point ------------------------------------------------------- #

    def handle(self, *args, **options):
        client, expected_account = self._build_client(options)
        window_start = timezone.now() - timedelta(days=options['days'])

        checks = []
        account_id = None

        # 1. Identity
        try:
            account = client.get_account()
        except ContoError as exc:
            checks.append(Check('GET /api/cuenta/', Check.FAIL, str(exc)))
            self._report(checks)
            raise CommandError('No se pudo leer la identidad de la cuenta. Se corta acá.')

        account_id = account.get('cuenta_id')
        checks.extend(self._check_account(account, expected_account))

        # 2. The endpoints must not be readable without a valid token
        checks.extend(self._check_auth_required(client))

        # 3. Stock
        checks.extend(self._check_stock(client, account_id))

        # 4. Sales
        checks.extend(self._check_sales(client, account_id, window_start))

        self._report(checks)

    def _build_client(self, options):
        """
        Build a client either from a stored integration or from ad-hoc arguments.

        The ad-hoc path exists so the contract can be checked before any
        integration record is created, which is the normal order of events.
        """
        if options.get('base_url'):
            token = getpass('Token de Conto (no se muestra): ').strip()
            if not token:
                raise CommandError('Hace falta el token')
            stub = ContoIntegration(
                base_url=options['base_url'],
                token=token,
            )
            return ContoClient(stub), None

        queryset = ContoIntegration.objects.all()
        if options.get('integration_id'):
            queryset = queryset.filter(pk=options['integration_id'])

        integration = queryset.first()
        if not integration:
            raise CommandError(
                'No hay ninguna integración cargada. Creá una en /admin o usá '
                '--base-url para probar sin guardar nada.'
            )
        if queryset.count() > 1:
            raise CommandError(
                'Hay más de una integración. Indicá cuál con --integration-id.'
            )

        return ContoClient(integration), integration.conto_account_id

    # -- individual checks -------------------------------------------------- #

    def _check_account(self, account, expected_account):
        checks = [Check('GET /api/cuenta/ responde', Check.OK)]

        for field in ('cuenta_id', 'nombre', 'activa'):
            if field in account:
                checks.append(Check(f"cuenta.{field} presente", Check.OK,
                                    repr(account[field])))
            else:
                checks.append(Check(f"cuenta.{field} presente", Check.FAIL, 'falta'))

        if account.get('activa') is False:
            checks.append(Check('Cuenta activa', Check.FAIL,
                                'la cuenta está marcada como inactiva'))

        if expected_account:
            if account.get('cuenta_id') == expected_account:
                checks.append(Check('Coincide con la cuenta vinculada', Check.OK))
            else:
                checks.append(Check(
                    'Coincide con la cuenta vinculada', Check.FAIL,
                    f"el token resuelve a {account.get('cuenta_id')!r} y la "
                    f"integración está vinculada a {expected_account!r}"
                ))

        return checks

    def _check_auth_required(self, client):
        """
        A bogus token must be rejected on every endpoint.

        If Conto is reachable on a public URL and any of these answer 200
        without a valid token, every connected business's sales data is public.
        Worth one extra request to rule out.
        """
        rogue = ContoClient(ContoIntegration(
            base_url=client.base_url,
            token='token-invalido-de-verificacion',
        ))

        checks = []
        endpoints = [
            ('/api/cuenta/', f'{client.base_url}/api/cuenta/'),
            ('/api/stock/', f'{client.base_url}/api/stock/'),
            ('/api/ventas/', f'{client.base_url}/api/ventas/'),
        ]

        for label, url in endpoints:
            try:
                rogue._request(url)
            except ContoError:
                # Any error is fine here: the point is that it did not succeed.
                checks.append(Check(f'{label} rechaza un token inválido', Check.OK))
            else:
                checks.append(Check(
                    f'{label} rechaza un token inválido', Check.FAIL,
                    'respondió 200 con un token inventado: el endpoint está abierto'
                ))

        return checks

    def _check_stock(self, client, account_id):
        url = f'{client.base_url}/api/stock/'
        try:
            payload = client._request(url)
        except ContoError as exc:
            return [Check('GET /api/stock/', Check.FAIL, str(exc))]

        checks = [Check('GET /api/stock/ responde', Check.OK)]
        checks.extend(self._check_envelope(payload, account_id, 'stock'))

        results = payload.get('results') or []
        if not results:
            checks.append(Check('stock: hay datos para inspeccionar', Check.SKIP,
                                'la respuesta vino vacía'))
            return checks

        item = results[0]
        for field, required in [
            ('sku', True), ('nombre', False), ('stock', True),
            ('costo', False), ('precio', False), ('actualizado_en', False),
        ]:
            if field in item:
                checks.append(Check(f'stock.{field}', Check.OK, repr(item[field])))
            else:
                checks.append(Check(
                    f'stock.{field}',
                    Check.FAIL if required else Check.WARN,
                    'falta'
                ))

        blank_skus = [i for i in results if not (i.get('sku') or '').strip()]
        if blank_skus:
            checks.append(Check(
                'stock: todos los ítems traen sku', Check.FAIL,
                f'{len(blank_skus)} de {len(results)} sin sku'
            ))

        return checks

    def _check_sales(self, client, account_id, window_start):
        url = f'{client.base_url}/api/ventas/'
        params = {'desde': client._format_timestamp(window_start)}
        try:
            payload = client._request(url, params)
        except ContoError as exc:
            return [Check('GET /api/ventas/', Check.FAIL, str(exc))]

        checks = [Check('GET /api/ventas/ responde', Check.OK)]
        checks.extend(self._check_envelope(payload, account_id, 'ventas'))

        results = payload.get('results') or []
        if not results:
            checks.append(Check('ventas: hay datos para inspeccionar', Check.SKIP,
                                'la ventana consultada vino vacía'))
            return checks

        voucher = results[0]
        for field, required in [
            ('id', True), ('tipo', True), ('canal', True), ('estado', True),
            ('fecha', True), ('actualizado_en', True), ('total', True),
            ('items', True), ('relacionada_con', False),
            ('orden_externa_id', False), ('medio_pago', False),
            ('gateway_origen', False), ('cliente', False),
        ]:
            if field in voucher:
                value = voucher[field]
                shown = repr(value)[:60] if field != 'items' else f'{len(value or [])} ítems'
                checks.append(Check(f'ventas.{field}', Check.OK, shown))
            else:
                checks.append(Check(
                    f'ventas.{field}',
                    Check.FAIL if required else Check.WARN,
                    'falta'
                ))

        checks.append(self._check_date_format(results))
        checks.append(self._check_item_types(results))
        checks.append(self._check_ordering(results))
        checks.extend(self._report_enums(results))

        return checks

    def _check_envelope(self, payload, account_id, label):
        checks = []

        if 'results' in payload:
            checks.append(Check(f'{label}: envelope con results', Check.OK))
        else:
            checks.append(Check(f'{label}: envelope con results', Check.FAIL, 'falta'))

        if 'next' in payload:
            checks.append(Check(f'{label}: campo next', Check.OK, repr(payload['next'])))
        else:
            checks.append(Check(f'{label}: campo next', Check.WARN,
                                'falta; sin él no se puede paginar'))

        received = payload.get('cuenta_id')
        if received is None:
            checks.append(Check(
                f'{label}: cuenta_id en la respuesta', Check.FAIL,
                'falta; es lo que valida el aislamiento en cada sincronización'
            ))
        elif account_id and received != account_id:
            checks.append(Check(
                f'{label}: cuenta_id consistente', Check.FAIL,
                f'devolvió {received!r} y se esperaba {account_id!r}'
            ))
        else:
            checks.append(Check(f'{label}: cuenta_id consistente', Check.OK))

        return checks

    def _check_date_format(self, results):
        """`fecha` must be a plain YYYY-MM-DD, not a datetime."""
        bad = []
        for voucher in results:
            value = str(voucher.get('fecha') or '')
            try:
                datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                bad.append(value)

        if bad:
            return Check(
                'ventas.fecha en formato YYYY-MM-DD', Check.FAIL,
                f'valores no válidos: {bad[:3]}'
            )
        return Check('ventas.fecha en formato YYYY-MM-DD', Check.OK)

    def _check_item_types(self, results):
        """Every line needs an explicit `tipo`, so nothing has to be inferred."""
        missing = 0
        total = 0
        for voucher in results:
            for item in voucher.get('items') or []:
                total += 1
                if not item.get('tipo'):
                    missing += 1

        if total == 0:
            return Check('items[].tipo presente', Check.SKIP, 'no hay ítems')
        if missing:
            return Check(
                'items[].tipo presente', Check.FAIL,
                f'{missing} de {total} ítems sin tipo'
            )
        return Check('items[].tipo presente', Check.OK, f'{total} ítems')

    def _check_ordering(self, results):
        """
        Ascending order by `actualizado_en`.

        Descending order silently skips records: new vouchers arriving mid-walk
        push the rest onto later pages.
        """
        stamps = [str(v.get('actualizado_en') or '') for v in results]
        if any(not s for s in stamps):
            return Check('ventas ordenadas por actualizado_en', Check.SKIP,
                         'falta actualizado_en en algún voucher')
        if stamps == sorted(stamps):
            return Check('ventas ordenadas ascendente', Check.OK)
        return Check(
            'ventas ordenadas ascendente', Check.FAIL,
            'vienen descendentes o desordenadas; la paginación va a saltear registros'
        )

    def _report_enums(self, results):
        """Surface the actual enum values, to confirm them against the spec."""
        channels, types, statuses, payments, gateways, item_types = (
            set(), set(), set(), set(), set(), set()
        )

        for voucher in results:
            channels.add(voucher.get('canal'))
            types.add(voucher.get('tipo'))
            statuses.add(voucher.get('estado'))
            payments.add(voucher.get('medio_pago'))
            gateways.add(voucher.get('gateway_origen'))
            for item in voucher.get('items') or []:
                item_types.add(item.get('tipo'))

        def show(values):
            return ', '.join(sorted(repr(v) for v in values)) or '(ninguno)'

        return [
            Check('valores de canal vistos', Check.SKIP, show(channels)),
            Check('valores de tipo vistos', Check.SKIP, show(types)),
            Check('valores de estado vistos', Check.SKIP, show(statuses)),
            Check('valores de medio_pago vistos', Check.SKIP, show(payments)),
            Check('valores de gateway_origen vistos', Check.SKIP, show(gateways)),
            Check('tipos de ítem vistos', Check.SKIP, show(item_types)),
        ]

    # -- output ------------------------------------------------------------ #

    def _report(self, checks):
        styles = {
            Check.OK: self.style.SUCCESS,
            Check.FAIL: self.style.ERROR,
            Check.WARN: self.style.WARNING,
            Check.SKIP: lambda text: text,
        }

        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Verificación del contrato de Conto'))
        self.stdout.write('')

        for check in checks:
            style = styles[check.status]
            line = f'  [{check.status:>5}] {check.name}'
            if check.detail:
                line = f'{line} — {check.detail}'
            self.stdout.write(style(line))

        failures = [c for c in checks if c.status == Check.FAIL]
        warnings = [c for c in checks if c.status == Check.WARN]

        self.stdout.write('')
        if failures:
            self.stdout.write(self.style.ERROR(
                f'{len(failures)} requisito(s) sin cumplir. La integración no puede '
                f'sincronizar todavía.'
            ))
            for check in failures:
                self.stdout.write(self.style.ERROR(f'  - {check.name}: {check.detail}'))
        else:
            self.stdout.write(self.style.SUCCESS(
                'Todos los requisitos bloqueantes se cumplen.'
            ))

        if warnings:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                f'{len(warnings)} aviso(s): no bloquean, pero se pierde información.'
            ))
            for check in warnings:
                self.stdout.write(self.style.WARNING(f'  - {check.name}: {check.detail}'))

        self.stdout.write('')
