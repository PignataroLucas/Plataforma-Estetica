"""
Tests de la franja de respuesta del centro.

Es la lógica más fácil de arruinar del circuito de aprobación y la más barata de
testear: funciones puras, sin base. Lo que se cuida acá son las dos cosas que
hacen que el vencimiento sea usable en vez de dañino:

1. **Que el reloj no corra de noche.** Un pedido de las 23:10 con tres horas de
   plazo no puede vencer a las 02:10: a la mañana el centro encontraría un
   rechazo automático de algo que habría aceptado.
2. **Que no se ofrezca un horario que nadie va a poder aprobar.** Pedido el lunes
   23:30 para el martes 08:00, con la franja abriendo a las 09:00, no tiene
   ningún momento posible de aprobación.
"""
from datetime import datetime, time, timedelta

import pytest
from django.utils import timezone

from apps.turnos.ventana import (
    VentanaInvalida,
    hay_ventana_suficiente,
    sumar_horas_de_respuesta,
    vencimiento_de,
)

INICIO = time(9, 0)
FIN = time(20, 0)


def momento(anio, mes, dia, hora, minuto=0):
    """Datetime aware en hora local, que es como se razona la franja."""
    return timezone.make_aware(datetime(anio, mes, dia, hora, minuto))


class SucursalFalsa:
    """
    Lo mínimo que la función necesita de una sucursal.

    Se usa un doble y no el modelo porque estas funciones son puras: pedir base
    para probarlas sería atarlas a algo de lo que no dependen.
    """

    def __init__(self, horas=3, inicio=INICIO, fin=FIN):
        self.horas_para_responder = horas
        self.respuesta_hora_inicio = inicio
        self.respuesta_hora_fin = fin


class TestSumarHorasDeRespuesta:
    def test_dentro_de_la_franja_suma_derecho(self):
        resultado = sumar_horas_de_respuesta(
            momento(2026, 10, 5, 10, 0), 3, hora_inicio=INICIO, hora_fin=FIN
        )
        assert resultado == momento(2026, 10, 5, 13, 0)

    def test_antes_de_abrir_arranca_en_la_apertura(self):
        """Un pedido de las 07:00 no gana las dos horas que el centro duerme."""
        resultado = sumar_horas_de_respuesta(
            momento(2026, 10, 5, 7, 0), 3, hora_inicio=INICIO, hora_fin=FIN
        )
        assert resultado == momento(2026, 10, 5, 12, 0)

    def test_de_noche_sigue_al_dia_siguiente(self):
        """
        El caso que motiva todo el módulo: 23:10 con tres horas no vence a las
        02:10, vence a las 12:00 del día siguiente.
        """
        resultado = sumar_horas_de_respuesta(
            momento(2026, 10, 5, 23, 10), 3, hora_inicio=INICIO, hora_fin=FIN
        )
        assert resultado == momento(2026, 10, 6, 12, 0)

    def test_cruza_el_cierre_y_sigue_al_dia_siguiente(self):
        """A las 19:00 queda una hora de hoy; las otras dos salen de mañana."""
        resultado = sumar_horas_de_respuesta(
            momento(2026, 10, 5, 19, 0), 3, hora_inicio=INICIO, hora_fin=FIN
        )
        assert resultado == momento(2026, 10, 6, 11, 0)

    def test_justo_en_la_apertura(self):
        resultado = sumar_horas_de_respuesta(
            momento(2026, 10, 5, 9, 0), 3, hora_inicio=INICIO, hora_fin=FIN
        )
        assert resultado == momento(2026, 10, 5, 12, 0)

    def test_justo_en_el_cierre_cuenta_como_cerrado(self):
        """A las 20:00 clavadas la franja ya terminó: el plazo arranca mañana."""
        resultado = sumar_horas_de_respuesta(
            momento(2026, 10, 5, 20, 0), 3, hora_inicio=INICIO, hora_fin=FIN
        )
        assert resultado == momento(2026, 10, 6, 12, 0)

    def test_un_plazo_mas_largo_que_la_franja_cruza_varios_dias(self):
        """25 horas sobre una franja de 11: hoy 11, mañana 11, y 3 el tercer día."""
        resultado = sumar_horas_de_respuesta(
            momento(2026, 10, 5, 9, 0), 25, hora_inicio=INICIO, hora_fin=FIN
        )
        assert resultado == momento(2026, 10, 7, 12, 0)

    def test_plazo_cero_devuelve_el_arranque_de_la_franja(self):
        """Con plazo cero el pedido vence apenas el centro podría mirarlo."""
        resultado = sumar_horas_de_respuesta(
            momento(2026, 10, 5, 2, 0), 0, hora_inicio=INICIO, hora_fin=FIN
        )
        assert resultado == momento(2026, 10, 5, 9, 0)

    def test_el_resultado_es_aware(self):
        """
        Si volviera naive, compararlo contra `fecha_hora_inicio` reventaría recién
        en producción y con una excepción que no explica nada.
        """
        resultado = sumar_horas_de_respuesta(
            momento(2026, 10, 5, 10, 0), 3, hora_inicio=INICIO, hora_fin=FIN
        )
        assert timezone.is_aware(resultado)

    @pytest.mark.parametrize('inicio,fin', [
        (time(20, 0), time(9, 0)),   # invertida
        (time(9, 0), time(9, 0)),    # de ancho cero
    ])
    def test_una_franja_imposible_falla_fuerte(self, inicio, fin):
        """Mejor una excepción clara que un bucle que no termina nunca."""
        with pytest.raises(VentanaInvalida):
            sumar_horas_de_respuesta(
                momento(2026, 10, 5, 10, 0), 3, hora_inicio=inicio, hora_fin=fin
            )


class TestVencimientoDe:
    def test_manda_el_plazo_cuando_el_turno_esta_lejos(self):
        sucursal = SucursalFalsa()
        vence = vencimiento_de(
            momento(2026, 10, 20, 15, 0),
            pedido_en=momento(2026, 10, 5, 10, 0),
            sucursal=sucursal,
        )
        assert vence == momento(2026, 10, 5, 13, 0)

    def test_manda_el_turno_cuando_empieza_antes_del_plazo(self):
        """Un pedido para dentro de una hora no puede seguir abierto tres."""
        sucursal = SucursalFalsa()
        inicio_turno = momento(2026, 10, 5, 11, 0)
        vence = vencimiento_de(
            inicio_turno, pedido_en=momento(2026, 10, 5, 10, 0), sucursal=sucursal
        )
        assert vence == inicio_turno

    def test_respeta_la_configuracion_de_la_sucursal(self):
        """El plazo y la franja salen de la sucursal, no de una constante."""
        sucursal = SucursalFalsa(horas=1, inicio=time(8, 0), fin=time(12, 0))
        vence = vencimiento_de(
            momento(2026, 10, 20, 15, 0),
            pedido_en=momento(2026, 10, 5, 7, 0),
            sucursal=sucursal,
        )
        assert vence == momento(2026, 10, 5, 9, 0)


class TestHayVentanaSuficiente:
    def test_el_caso_que_motiva_la_regla(self):
        """
        Lunes 23:30 pidiendo el martes 08:00: la franja abre a las 09:00, o sea
        después de que el turno empezó. No hay aprobación posible.
        """
        sucursal = SucursalFalsa()
        assert not hay_ventana_suficiente(
            momento(2026, 10, 6, 8, 0),
            ahora=momento(2026, 10, 5, 23, 30),
            sucursal=sucursal,
        )

    def test_el_mismo_pedido_mas_tarde_en_el_dia_si_entra(self):
        """Martes 12:00 sí: quedan las tres horas entre 09:00 y 12:00."""
        sucursal = SucursalFalsa()
        assert hay_ventana_suficiente(
            momento(2026, 10, 6, 12, 0),
            ahora=momento(2026, 10, 5, 23, 30),
            sucursal=sucursal,
        )

    def test_de_dia_con_tiempo_de_sobra(self):
        sucursal = SucursalFalsa()
        assert hay_ventana_suficiente(
            momento(2026, 10, 6, 8, 0),
            ahora=momento(2026, 10, 5, 10, 0),
            sucursal=sucursal,
        )

    def test_el_borde_exacto_alcanza(self):
        """
        Si el plazo termina justo cuando empieza el turno, entra. Es el límite y
        conviene fijarlo: a un minuto menos tendría que dar falso.
        """
        sucursal = SucursalFalsa()
        assert hay_ventana_suficiente(
            momento(2026, 10, 5, 13, 0),
            ahora=momento(2026, 10, 5, 10, 0),
            sucursal=sucursal,
        )
        assert not hay_ventana_suficiente(
            momento(2026, 10, 5, 12, 59),
            ahora=momento(2026, 10, 5, 10, 0),
            sucursal=sucursal,
        )

    def test_un_turno_que_ya_paso_nunca_entra(self):
        sucursal = SucursalFalsa()
        assert not hay_ventana_suficiente(
            momento(2026, 10, 5, 9, 0),
            ahora=momento(2026, 10, 5, 10, 0),
            sucursal=sucursal,
        )

    def test_una_franja_mas_larga_deja_pasar_mas_horarios(self):
        """
        La regla se deriva de la configuración: ampliar la franja amplía lo que se
        ofrece, sin tocar ninguna otra constante.
        """
        angosta = SucursalFalsa(horas=3, inicio=time(9, 0), fin=time(20, 0))
        amplia = SucursalFalsa(horas=3, inicio=time(0, 0), fin=time(23, 59))
        turno = momento(2026, 10, 6, 8, 0)
        ahora = momento(2026, 10, 5, 23, 30)

        assert not hay_ventana_suficiente(turno, ahora=ahora, sucursal=angosta)
        assert hay_ventana_suficiente(turno, ahora=ahora, sucursal=amplia)
