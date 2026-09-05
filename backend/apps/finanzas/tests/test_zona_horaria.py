"""
Regresión de zona horaria: "hoy" se calcula en hora de Argentina, no en UTC.

El servidor corre en UTC y el centro trabaja en Buenos Aires (-03). Entre las
21:00 y la medianoche de Argentina la fecha UTC ya es la del día siguiente, así
que `timezone.now().date()` devuelve mañana. En producción eso hizo que el
dashboard mostrara "sábado 5 de septiembre" un viernes a la noche y que los
cobros de Mi Caja quedaran fechados el día siguiente: la plata aparecía, pero
contada en el día equivocado.

Todos los tests de acá congelan el reloj dentro de esa ventana. Es la única
forma de ver el bug: a las tres de la tarde la fecha UTC y la local coinciden y
el código roto pasa igual.

Están juntos en un archivo a propósito. No son tests "de finanzas": son tests de
un mismo error repartido entre dashboard, turnos y caja, y se entienden mejor
leídos de corrido.
"""
import io
import tokenize
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone as tz
from decimal import Decimal
from pathlib import Path
from unittest import mock

import pytest
from django.conf import settings
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.clientes.models import Cliente
from apps.empleados.models import CentroEstetica, Sucursal, Usuario
from apps.finanzas.models import Transaction, TransactionCategory
from apps.servicios.models import Servicio
from apps.turnos.models import Turno

# Viernes 4 de septiembre de 2026, 21:16 en Buenos Aires: la hora exacta a la
# que se reportó el bug. En UTC ya es sábado 5.
NOCHE_UTC = datetime(2026, 9, 5, 0, 16, tzinfo=tz.utc)
VIERNES = date(2026, 9, 4)   # el día real, en Argentina
SABADO = date(2026, 9, 5)    # lo que devuelve UTC


@contextmanager
def reloj(momento=NOCHE_UTC):
    """
    Congela `timezone.now()`. Alcanza con parchear ese nombre: nadie en el
    backend importa `now` directo, y `localdate()`/`localtime()` lo resuelven
    contra el módulo, igual que los `auto_now_add`.
    """
    with mock.patch('django.utils.timezone.now', return_value=momento):
        yield


def hora_local(hh, mm=0, dia=VIERNES):
    """Un instante de ese día a esa hora de Buenos Aires, devuelto aware."""
    return timezone.make_aware(datetime(dia.year, dia.month, dia.day, hh, mm))


@pytest.fixture
def centro(db):
    """Un centro con lo mínimo para tener turnos y cobrar un servicio."""
    centro = CentroEstetica.objects.create(
        nombre='AME', telefono='1111', email='ame@test.local'
    )
    sucursal = Sucursal.objects.create(
        centro_estetica=centro, nombre='Principal', direccion='Calle 1',
        telefono='1111', ciudad='CABA', provincia='CABA',
    )
    admin = Usuario.objects.create_user(
        username='admin', password='x', rol='ADMIN',
        centro_estetica=centro, sucursal=sucursal,
    )
    servicio = Servicio.objects.create(
        sucursal=sucursal, nombre='Mio Up y Vela',
        duracion_minutos=60, precio=Decimal('27000.00'),
    )
    cliente = Cliente.objects.create(
        centro_estetica=centro, nombre='Aldana', apellido='Ausilio', telefono='11',
    )
    return {
        'centro': centro, 'sucursal': sucursal, 'admin': admin,
        'servicio': servicio, 'cliente': cliente,
    }


def api(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def turno(centro, inicio, estado=Turno.Estado.CONFIRMADO):
    return Turno.objects.create(
        sucursal=centro['sucursal'], cliente=centro['cliente'],
        servicio=centro['servicio'], profesional=centro['admin'],
        fecha_hora_inicio=inicio,
        fecha_hora_fin=inicio + timedelta(minutes=60),
        estado=estado, monto_total=centro['servicio'].precio,
    )


def cobrar_un_servicio(centro):
    """Un cobro de Mi Caja, el camino por el que se guardaron las fechas mal."""
    return api(centro['admin']).post(
        reverse('mi-caja-venta-unificada'),
        {
            'items': [{'tipo': 'servicio_directo',
                       'servicio_id': centro['servicio'].id}],
            'payment_method': 'BANK_TRANSFER',
        },
        format='json',
    )


def transaccion(centro, fecha, creada=NOCHE_UTC, de_quien=None):
    """
    Una transacción escrita a mano, salteando la vista.

    Los tests de lectura tienen que fabricar el dato así y no cobrando de
    verdad: si el mismo bug escribe y lee, escribe SÁBADO y busca SÁBADO, los
    números cierran y el test pasa sin probar nada. Fue exactamente lo que pasó
    en producción, donde la plata aparecía pero contada en el día equivocado.
    """
    tx = Transaction.objects.create(
        branch=centro['sucursal'],
        category=TransactionCategory.objects.filter(
            branch=centro['sucursal'], type='INCOME'
        ).first(),
        type='INCOME_SERVICE', amount=Decimal('27000.00'),
        payment_method='BANK_TRANSFER', date=fecha, description='Servicio',
        registered_by=de_quien,
    )
    # created_at es auto_now_add: se fuerza por update.
    Transaction.objects.filter(pk=tx.pk).update(created_at=creada)
    tx.refresh_from_db()
    return tx


# --------------------------------------------------------------------------- #
# La ventana
# --------------------------------------------------------------------------- #

class TestLaVentanaPeligrosa:
    """
    Sin esto, todo lo de abajo podría estar pasando por el motivo equivocado: si
    el reloj congelado no cayera en la franja donde UTC y Argentina difieren,
    los tests pasarían incluso con el bug puesto.
    """

    def test_la_fecha_utc_no_es_la_fecha_local(self):
        with reloj():
            assert timezone.now().date() == SABADO, 'en UTC ya es sábado'
            assert timezone.localdate() == VIERNES, 'en Argentina todavía es viernes'

    def test_settings_apunta_a_argentina(self):
        assert settings.TIME_ZONE == 'America/Argentina/Buenos_Aires'
        assert settings.USE_TZ is True


# --------------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestDashboard:

    def test_muestra_el_dia_local_no_el_utc(self, centro):
        with reloj():
            response = api(centro['admin']).get(reverse('dashboard-home'))

        assert response.status_code == 200
        assert response.json()['fecha'] == '2026-09-04'

    def test_cuenta_el_turno_de_esta_noche(self, centro):
        de_esta_noche = turno(centro, hora_local(21, 30))

        with reloj():
            citas = api(centro['admin']).get(reverse('dashboard-home')).json()['citas_hoy']

        # Por id y no por total: con la fecha en UTC el total también daba 1,
        # pero contando el turno de mañana en lugar de éste.
        assert citas['total'] == 1
        assert [c['id'] for c in citas['proximas']] == [de_esta_noche.id]

    def test_no_cuenta_el_de_manana(self, centro):
        turno(centro, hora_local(10, 0, SABADO))

        with reloj():
            citas = api(centro['admin']).get(reverse('dashboard-home')).json()['citas_hoy']

        assert citas['total'] == 0

    def test_los_ingresos_del_dia_son_los_del_dia_local(self, centro):
        transaccion(centro, fecha=VIERNES)

        with reloj():
            response = api(centro['admin']).get(reverse('dashboard-home'))

        assert response.json()['ingresos_hoy']['ingresos'] == 27000.0


# --------------------------------------------------------------------------- #
# Turnos
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestTurnosDeHoy:
    """
    `/api/turnos/turnos/hoy/` armaba la ventana con
    `timezone.now().replace(hour=0, ...)`, que sobre un datetime UTC arranca el
    día a las 21:00 del día anterior en Argentina.
    """

    def test_incluye_un_turno_de_las_nueve_y_media_de_la_noche(self, centro):
        de_esta_noche = turno(centro, hora_local(21, 30))

        with reloj():
            response = api(centro['admin']).get(reverse('turno-hoy'))

        assert [t['id'] for t in response.json()] == [de_esta_noche.id]

    def test_no_incluye_los_de_manana(self, centro):
        turno(centro, hora_local(10, 0, SABADO))

        with reloj():
            response = api(centro['admin']).get(reverse('turno-hoy'))

        assert response.json() == []

    def test_no_incluye_los_de_anoche(self, centro):
        """
        El borde de abajo: con la ventana armada en UTC, un turno de las 20:00
        de ayer entraba como si fuera de hoy.
        """
        de_hoy = turno(centro, hora_local(15, 0))
        turno(centro, hora_local(20, 0, VIERNES - timedelta(days=1)))

        with reloj():
            response = api(centro['admin']).get(reverse('turno-hoy'))

        assert [t['id'] for t in response.json()] == [de_hoy.id]


# --------------------------------------------------------------------------- #
# Mi Caja
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestMiCaja:

    def test_un_cobro_de_las_nueve_de_la_noche_queda_fechado_hoy(self, centro):
        with reloj():
            response = cobrar_un_servicio(centro)

        assert response.status_code == 201
        assert Transaction.objects.get().date == VIERNES

    def test_mis_transacciones_sin_fecha_muestra_lo_de_esta_noche(self, centro):
        with reloj():
            cobrar_un_servicio(centro)
            response = api(centro['admin']).get(reverse('mi-caja-mis-transacciones'))

        cuerpo = response.json()
        assert cuerpo['fecha'] == '2026-09-04'
        assert len(cuerpo['transacciones']) == 1

    def test_el_resumen_del_dia_suma_lo_de_esta_noche(self, centro):
        transaccion(centro, fecha=VIERNES, de_quien=centro['admin'])

        with reloj():
            response = api(centro['admin']).get(reverse('mi-caja-resumen-dia'))

        assert Decimal(str(response.json()['total'])) == Decimal('27000.00')

    def test_no_deja_cerrar_la_caja_de_manana(self, centro):
        """
        Éste no reproduce el bug de producción: `date.today()`, que es lo que
        usaba antes, ya devolvía hora argentina porque Django pisa el TZ del
        proceso al arrancar. Queda como candado de comportamiento: la fecha
        límite tiene que seguir siendo la local, no la UTC.
        """
        with reloj():
            response = api(centro['admin']).post(
                reverse('mi-caja-cierre-caja'),
                {'fecha': SABADO.isoformat(), 'efectivo_contado': '0.00'},
                format='json',
            )

        assert response.status_code == 400

    def test_deja_cerrar_la_caja_de_hoy(self, centro):
        with reloj():
            response = api(centro['admin']).post(
                reverse('mi-caja-cierre-caja'),
                {'fecha': VIERNES.isoformat(), 'efectivo_contado': '0.00'},
                format='json',
            )

        assert response.status_code in (200, 201)


# --------------------------------------------------------------------------- #
# El comando que repara lo que ya se guardó mal
# --------------------------------------------------------------------------- #

@pytest.mark.django_db
class TestComandoDeReparacion:

    def test_corrige_una_fecha_corrida(self, centro):
        rota = transaccion(centro, fecha=SABADO)

        call_command('corregir_fechas_utc', aplicar=True)

        rota.refresh_from_db()
        assert rota.date == VIERNES

    def test_el_dry_run_no_escribe(self, centro):
        rota = transaccion(centro, fecha=SABADO)

        call_command('corregir_fechas_utc')

        rota.refresh_from_db()
        assert rota.date == SABADO

    def test_no_toca_una_fecha_elegida_a_mano(self, centro):
        """
        Una transacción cargada a las 21:00 pero fechada la semana pasada es una
        fecha que eligió una persona, no el bug. El comando no la puede mover.
        """
        a_mano = transaccion(centro, fecha=VIERNES - timedelta(days=7))

        call_command('corregir_fechas_utc', aplicar=True)

        a_mano.refresh_from_db()
        assert a_mano.date == VIERNES - timedelta(days=7)

    def test_no_toca_las_que_ya_estan_bien(self, centro):
        sana = transaccion(centro, fecha=VIERNES)

        call_command('corregir_fechas_utc', aplicar=True)

        sana.refresh_from_db()
        assert sana.date == VIERNES


# --------------------------------------------------------------------------- #
# Que no vuelva a entrar por otro lado
# --------------------------------------------------------------------------- #

class TestNingunArchivoCalculaHoyEnUTC:
    """
    Los tests de arriba cubren los caminos que ya conocemos. Éste cubre los que
    todavía no existen: cualquier archivo nuevo que calcule "hoy" en UTC salta
    acá, sin esperar a que alguien lo note un viernes a la noche.
    """

    PROHIBIDO = {
        'timezone.now().date()': 'usar timezone.localdate()',
        'datetime.now().date()': 'usar timezone.localdate()',
        'datetime.today()': 'usar timezone.localdate()',
        'date.today()': 'usar timezone.localdate()',
        'timezone.now().replace(hour=': (
            'recortar la hora sobre UTC arranca el día a las 21:00 del día '
            'anterior; filtrar con __date=timezone.localdate()'
        ),
    }

    @staticmethod
    def codigo_sin_prosa(fuente):
        """
        Las mismas líneas, con comentarios y strings en blanco.

        Sin esto el guard se dispara contra su propia explicación: los archivos
        que cuentan el bug —el comando de reparación, este mismo test— nombran
        el patrón prohibido en un comentario o en un docstring.
        """
        lineas = fuente.splitlines()
        for tok in tokenize.generate_tokens(io.StringIO(fuente).readline):
            if tok.type != tokenize.COMMENT and not \
                    tokenize.tok_name[tok.type].startswith(('STRING', 'FSTRING')):
                continue
            (fila_ini, col_ini), (fila_fin, col_fin) = tok.start, tok.end
            for fila in range(fila_ini, fila_fin + 1):
                texto = lineas[fila - 1]
                desde = col_ini if fila == fila_ini else 0
                hasta = col_fin if fila == fila_fin else len(texto)
                lineas[fila - 1] = texto[:desde] + ' ' * (hasta - desde) + texto[hasta:]
        return lineas

    def test_nadie_usa_los_patrones_de_utc(self):
        raiz = Path(settings.BASE_DIR) / 'apps'
        # Este archivo queda afuera: `test_la_fecha_utc_no_es_la_fecha_local`
        # ejecuta el patrón prohibido a propósito, es lo que demuestra que la
        # ventana elegida es la peligrosa.
        propio = Path(__file__).resolve()

        hallazgos = []
        for archivo in raiz.rglob('*.py'):
            if 'migrations' in archivo.parts or archivo.resolve() == propio:
                continue
            fuente = archivo.read_text(encoding='utf-8')
            for numero, linea in enumerate(self.codigo_sin_prosa(fuente), start=1):
                for patron, arreglo in self.PROHIBIDO.items():
                    if patron in linea:
                        relativo = archivo.relative_to(settings.BASE_DIR)
                        hallazgos.append(
                            f'{relativo}:{numero}  {patron}  →  {arreglo}'
                        )

        assert not hallazgos, (
            'Fecha calculada en UTC. Entre las 21:00 y la medianoche de '
            'Argentina eso devuelve el día siguiente:\n  '
            + '\n  '.join(hallazgos)
        )
