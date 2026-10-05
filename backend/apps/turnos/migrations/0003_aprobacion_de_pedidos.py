"""
Estado RECHAZADO, origen del turno y el plazo para resolver los pedidos.

Ver APROBACION_TURNOS_SPEC.md §3.1. Dos cosas que conviene tener presentes al
leer esto:

- **RECHAZADO no es CANCELADO.** Un turno cancelado existió y se cayó; un pedido
  rechazado nunca llegó a ser turno. Se separan porque la tasa de rechazo mide si
  la disponibilidad que publica la app se parece a la realidad del centro, y la de
  cancelación mide comportamiento de las clientas.
- **`origen` arranca en CRM para todo lo que ya existe**, que es correcto: los
  turnos cargados hasta hoy los cargó el staff. La app empieza a mandar APP desde
  este deploy.

Ningún turno existente queda con `vence_en`: los pendientes de antes no nacieron
bajo esta política y no corresponde vencerlos retroactivamente.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('empleados', '0005_sucursal_ventana_de_respuesta'),
        ('turnos', '0002_alter_turno_creado_por'),
    ]

    operations = [
        migrations.AlterField(
            model_name='turno',
            name='estado',
            field=models.CharField(
                choices=[
                    ('PENDIENTE', 'Pendiente de Confirmación'),
                    ('CONFIRMADO', 'Confirmado'),
                    ('RECHAZADO', 'Rechazado'),
                    ('COMPLETADO', 'Completado'),
                    ('CANCELADO', 'Cancelado'),
                    ('NO_SHOW', 'No Show'),
                ],
                db_index=True,
                default='PENDIENTE',
                max_length=15,
            ),
        ),
        migrations.AddField(
            model_name='turno',
            name='origen',
            field=models.CharField(
                choices=[('APP', 'App de clientas'), ('CRM', 'Cargado en el CRM')],
                db_index=True,
                default='CRM',
                help_text='De dónde salió el turno. La app manda APP; el CRM es el default.',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='turno',
            name='vence_en',
            field=models.DateTimeField(
                blank=True,
                help_text=(
                    'Hasta cuándo el centro puede aceptar o rechazar este pedido. '
                    'Solo se completa en los que esperan aprobación.'
                ),
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='turno',
            name='motivo_rechazo',
            field=models.CharField(
                blank=True,
                choices=[
                    ('SIN_DISPONIBILIDAD', 'No hay disponibilidad real'),
                    ('EQUIPO_NO_DISPONIBLE', 'El equipo no está disponible'),
                    ('DEUDA_PENDIENTE', 'La clienta tiene una deuda'),
                    ('REQUIERE_EVALUACION', 'Requiere evaluación previa'),
                    ('OTRO', 'Otro'),
                    ('VENCIDO', 'Venció sin respuesta'),
                ],
                help_text='Obligatorio al rechazar. Lo completa el sistema si vence.',
                max_length=25,
            ),
        ),
        migrations.AddField(
            model_name='turno',
            name='detalle_rechazo',
            field=models.CharField(
                blank=True,
                help_text='Aclaración opcional del motivo. Nunca se le muestra a la clienta.',
                max_length=300,
            ),
        ),
        migrations.AddField(
            model_name='turno',
            name='resuelto_por',
            field=models.ForeignKey(
                blank=True,
                help_text='Quién aceptó o rechazó el pedido. Vacío si venció sin respuesta.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='turnos_resueltos',
                to='empleados.usuario',
            ),
        ),
        migrations.AddField(
            model_name='turno',
            name='resuelto_en',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name='turno',
            index=models.Index(
                fields=['estado', 'vence_en'], name='turnos_turn_estado_vence_idx'
            ),
        ),
    ]
