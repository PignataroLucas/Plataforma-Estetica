"""
Tests del cron que limpia los cupones vencidos (COMPRA_EN_APP_SPEC.md §6.5).

Cada "Comprar" que no termina en compra deja un cupón vivo en la tienda del
centro. La función que los borra ya está probada en `test_cupones.py`; lo que se
cuida acá es que **algo la llame**, que es exactamente lo que faltaba.

Dos modos de fallar, los dos silenciosos:

1. **Un nombre de task mal escrito en el `beat_schedule`.** Celery no valida esa
   cadena al arrancar: el job simplemente nunca corre y nadie se entera. El test
   los importa todos, no solo el de los cupones, porque el defecto es de la
   forma y no de esta entrada.

2. **Una task que propague la excepción.** `limpiar_vencidos` no propaga a
   propósito —un cupón que no se pudo borrar se reintenta en la corrida
   siguiente—, y una envoltura que rompiera esa propiedad convertiría un error
   de red en un job fallado.
"""
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.empleados.models import CentroEstetica
from apps.integraciones.models import CuponApp, TiendanubeIntegration
from apps.integraciones.tasks import limpiar_cupones_app
from apps.integraciones.tiendanube import TiendanubeError
from config.celery import app as celery_app


def hacer_cupon_vencido(codigo='APP-VENCIDO1'):
    centro = CentroEstetica.objects.create(
        nombre='Ame', telefono='1', email=f'{codigo}@test.local'
    )
    integracion = TiendanubeIntegration.objects.create(
        center=centro, store_id=f'store-{codigo}', token='tok', is_active=True,
    )
    return CuponApp.objects.create(
        integration=integracion,
        code=codigo,
        percentage=Decimal('15.00'),
        tiendanube_coupon_id='67713598',
        issued_at=timezone.now() - timedelta(hours=3),
        expires_at=timezone.now() - timedelta(hours=2),
    )


# Job programado que apunta a una task que no existe. `apps/inventario/` no
# tiene `tasks.py`: la alerta de stock bajo vive solo como propiedad calculada
# que muestra el dashboard, y este job nunca corrió. Es anterior a este trabajo
# y arreglarlo es escribir la task, que es otro tema; se lo excluye nombrado
# para que quede registrado en vez de desaparecer.
ROTAS_CONOCIDAS = {'check-low-inventory'}


def _resuelve(ruta):
    from django.utils.module_loading import import_string

    try:
        import_string(ruta)
    except ImportError:
        return False
    return True


class TestBeatSchedule:

    def test_todas_las_tasks_programadas_existen(self):
        """
        Celery no valida el nombre de la task al arrancar: una mal escrita no
        corre nunca y no avisa. Importarlas todas es la única forma barata de
        que un typo falle acá y no en producción tres semanas después.
        """
        for nombre, config in celery_app.conf.beat_schedule.items():
            if nombre in ROTAS_CONOCIDAS:
                continue
            assert _resuelve(config['task']), (
                f"El job '{nombre}' apunta a '{config['task']}', que no existe."
            )

    def test_las_rotas_conocidas_siguen_rotas(self):
        """
        Una lista de excepciones que nadie limpia deja de ser una excepción.
        Este test falla el día que alguien escriba la task, y lo único que pide
        es sacar el nombre de `ROTAS_CONOCIDAS`.
        """
        for nombre in ROTAS_CONOCIDAS:
            config = celery_app.conf.beat_schedule.get(nombre)
            if config is None:
                pytest.fail(
                    f"'{nombre}' ya no está en el beat_schedule: sacalo de "
                    f"ROTAS_CONOCIDAS."
                )
            assert not _resuelve(config['task']), (
                f"'{nombre}' ya resuelve: sacalo de ROTAS_CONOCIDAS."
            )

    def test_la_limpieza_de_cupones_esta_programada(self):
        """
        El comando existía desde el principio y nada lo corría, que es el
        agujero que esto cierra.
        """
        tareas = {
            c['task'] for c in celery_app.conf.beat_schedule.values()
        }
        assert 'apps.integraciones.tasks.limpiar_cupones_app' in tareas


@pytest.mark.django_db
class TestTask:

    def test_borra_los_vencidos_y_devuelve_la_cuenta(self):
        cupon = hacer_cupon_vencido()

        with patch('apps.integraciones.cupones.TiendanubeClient.delete_coupon') as borrar:
            resultado = limpiar_cupones_app()

        borrar.assert_called_once_with('67713598')
        assert resultado == {'borrados': 1, 'errores': []}

        cupon.refresh_from_db()
        assert cupon.revoked_at is not None

    def test_un_error_de_tienda_nube_no_tumba_el_job(self):
        """
        Se reintenta en la corrida siguiente. Si esto propagara, un problema de
        red pasaría a ser un job fallado y una alerta que no corresponde.
        """
        hacer_cupon_vencido()

        with patch('apps.integraciones.cupones.TiendanubeClient.delete_coupon',
                   side_effect=TiendanubeError('sin red')):
            resultado = limpiar_cupones_app()

        assert resultado['borrados'] == 0
        assert len(resultado['errores']) == 1

    def test_no_toca_los_que_todavia_estan_vigentes(self):
        """
        Un cupón vigente es de una compra que puede estar pasando en este
        momento: borrarlo le sacaría el descuento a la clienta en el checkout.
        """
        cupon = hacer_cupon_vencido()
        cupon.expires_at = timezone.now() + timedelta(hours=1)
        cupon.save(update_fields=['expires_at'])

        with patch('apps.integraciones.cupones.TiendanubeClient.delete_coupon') as borrar:
            resultado = limpiar_cupones_app()

        borrar.assert_not_called()
        assert resultado['borrados'] == 0
