"""
Banco de pruebas de las notificaciones.

Tres usos, de menos a más invasivo:

    # 1. Revisar la redacción de todos los avisos. No toca la base.
    python manage.py simular_notificacion --listar

    # 2. Mandar uno a una cuenta concreta y ver el resultado.
    python manage.py simular_notificacion --evento cumpleanos --email sofi@mail.com

    # 3. Mandar uno de cada tipo, para revisar la tanda completa.
    python manage.py simular_notificacion --todos --email sofi@mail.com

    # Estado de la cola en este momento.
    python manage.py simular_notificacion --estado

Con ``NOTIFICACIONES_CANAL=consola`` (el default en DEBUG) las notificaciones se
imprimen en vez de salir, así que esto se puede correr sin cuenta de Expo y sin
un teléfono. Si el canal es ``expo``, el comando avisa antes de mandar de verdad.
"""
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.clientes.models import UsuarioCliente
from apps.notificaciones import canales, cola, despacho, eventos
from apps.notificaciones.models import Aviso, DispositivoPush, EnvioPush

# Token de mentira para poder simular sin haber registrado un teléfono real.
# Es válido de formato pero no apunta a ningún aparato: con el canal de consola
# no sale a ningún lado, y si alguien lo manda a Expo de verdad, Expo lo rechaza.
TOKEN_SIMULADO = 'ExponentPushToken[simulador-local-000000]'


class Command(BaseCommand):
    help = 'Simula notificaciones push: previsualiza textos, dispara avisos y muestra la cola.'

    def add_arguments(self, parser):
        parser.add_argument('--listar', action='store_true',
                            help='Muestra todos los eventos con su texto de ejemplo. No escribe nada.')
        parser.add_argument('--estado', action='store_true',
                            help='Resumen de la cola de avisos y dispositivos.')
        parser.add_argument('--evento', help='Clave del evento a disparar.')
        parser.add_argument('--todos', action='store_true',
                            help='Dispara un aviso de cada tipo.')
        parser.add_argument('--email', help='Cuenta de app destinataria.')
        parser.add_argument('--no-enviar', action='store_true',
                            help='Solo encola; no procesa la cola.')

    def handle(self, *args, **opciones):
        if opciones['listar']:
            return self._listar()
        if opciones['estado']:
            return self._estado()
        if opciones['evento'] or opciones['todos']:
            return self._disparar(opciones)

        raise CommandError(
            'Elegí algo: --listar, --estado, --evento <clave> o --todos. '
            'Ver `--help`.'
        )

    # ------------------------------------------------------------------ #

    def _listar(self):
        """Previsualiza cada aviso con sus valores de ejemplo."""
        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\nAvisos definidos ({len(eventos.EVENTOS)}). Canal activo: {canales.nombre_activo()}\n'
        ))

        for clave in eventos.claves():
            evento = eventos.obtener(clave)
            titulo = eventos.renderizar(evento.titulo, evento.ejemplo)
            cuerpo = eventos.renderizar(evento.cuerpo, evento.ejemplo)
            ruta = eventos.renderizar(evento.ruta, evento.ejemplo) or '—'
            etiqueta = 'transaccional' if evento.transaccional else 'se puede apagar'

            self.stdout.write(self.style.HTTP_INFO(f'  {clave}'))
            self.stdout.write(f'    {self.style.SUCCESS(titulo)}')
            self.stdout.write(f'    {cuerpo}')
            self.stdout.write(self.style.HTTP_NOT_MODIFIED(
                f'    {evento.categoria} · {etiqueta} · → {ruta}\n'
            ))

    def _estado(self):
        """Foto de la cola, para saber si algo se está acumulando."""
        por_estado = {
            estado: Aviso.objects.filter(estado=estado).count()
            for estado, _ in Aviso.Estado.choices
        }
        vencidos = Aviso.objects.filter(
            estado=Aviso.Estado.PENDIENTE, programado_para__lte=timezone.now()
        ).count()

        self.stdout.write(json.dumps({
            'canal': canales.nombre_activo(),
            'avisos': por_estado,
            'pendientes_vencidos': vencidos,
            'dispositivos_activos': DispositivoPush.objects.filter(activo=True).count(),
            'dispositivos_de_baja': DispositivoPush.objects.filter(activo=False).count(),
            'envios': {
                estado: EnvioPush.objects.filter(estado=estado).count()
                for estado, _ in EnvioPush.Estado.choices
            },
        }, ensure_ascii=False, indent=2))

    # ------------------------------------------------------------------ #

    def _resolver_usuario(self, email):
        if email:
            try:
                return UsuarioCliente.objects.get(email=email)
            except UsuarioCliente.DoesNotExist:
                raise CommandError(f"No existe una cuenta de app con el email '{email}'.")

        cuentas = UsuarioCliente.objects.all()[:2]
        if not cuentas:
            raise CommandError('No hay ninguna cuenta de app en la base. Creá una primero.')
        if len(cuentas) > 1:
            raise CommandError('Hay más de una cuenta: indicá cuál con --email.')
        return cuentas[0]

    def _asegurar_dispositivo(self, usuario):
        """Sin un dispositivo activo el aviso quedaría en SIN_DESTINO."""
        if usuario.dispositivos_push.filter(activo=True).exists():
            return False

        DispositivoPush.objects.update_or_create(
            token=TOKEN_SIMULADO,
            defaults={
                'usuario_cliente': usuario,
                'plataforma': DispositivoPush.Plataforma.DESCONOCIDA,
                'activo': True,
                'motivo_baja': '',
            },
        )
        return True

    def _disparar(self, opciones):
        usuario = self._resolver_usuario(opciones['email'])

        if canales.nombre_activo() == 'expo':
            self.stdout.write(self.style.WARNING(
                '⚠  El canal activo es "expo": esto manda notificaciones DE VERDAD.\n'
                '   Para simular sin enviar, corré con NOTIFICACIONES_CANAL=consola.\n'
            ))

        if self._asegurar_dispositivo(usuario):
            self.stdout.write(self.style.WARNING(
                f'   (la cuenta no tenía dispositivos: se creó uno simulado)\n'
            ))

        claves = eventos.claves() if opciones['todos'] else [opciones['evento']]
        centro = usuario.centros.first()

        # Marca de tiempo en la clave: el simulador tiene que poder correrse las
        # veces que haga falta, y la idempotencia normal lo bloquearía.
        marca = timezone.now().strftime('%Y%m%d%H%M%S')

        creados = 0
        for clave in claves:
            evento = eventos.obtener(clave)  # valida la clave y da un error claro
            aviso = despacho.crear_aviso(
                evento=clave,
                usuario_cliente=usuario,
                centro_estetica=centro,
                contexto=evento.ejemplo,
                clave=f'simulado:{marca}:{clave}',
            )
            if aviso:
                creados += 1
            else:
                self.stdout.write(self.style.WARNING(
                    f'   {clave}: no se creó (la cuenta tiene apagada la categoría '
                    f'{evento.categoria})'
                ))

        self.stdout.write(f'\nAvisos encolados para {usuario.email}: {creados}')

        if opciones['no_enviar']:
            self.stdout.write('Quedaron en la cola (--no-enviar).')
            return

        resumen = cola.procesar_pendientes()
        self.stdout.write(json.dumps(resumen, ensure_ascii=False))
