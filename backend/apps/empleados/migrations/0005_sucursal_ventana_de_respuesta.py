"""
Franja en la que la sucursal responde los pedidos de turno de la app.

No es el horario del local: es cuándo alguien mira los pedidos. El plazo de
`horas_para_responder` corre solo dentro de esta franja, que es lo que evita que
un pedido hecho a las 23:10 venza de madrugada (APROBACION_TURNOS_SPEC.md §2.2).

Los defaults son los que definió AME el 05/10/2026: 09:00 a 20:00, tres horas.
"""
import datetime

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empleados', '0004_alter_centroestetica_logo'),
    ]

    operations = [
        migrations.AddField(
            model_name='sucursal',
            name='respuesta_hora_inicio',
            field=models.TimeField(
                default=datetime.time(9, 0),
                help_text='Desde qué hora se miran los pedidos de turno de la app',
                verbose_name='Responde pedidos desde',
            ),
        ),
        migrations.AddField(
            model_name='sucursal',
            name='respuesta_hora_fin',
            field=models.TimeField(
                default=datetime.time(20, 0),
                help_text='Hasta qué hora se miran los pedidos de turno de la app',
                verbose_name='Responde pedidos hasta',
            ),
        ),
        migrations.AddField(
            model_name='sucursal',
            name='horas_para_responder',
            field=models.PositiveSmallIntegerField(
                default=3,
                help_text=(
                    'Cuánto dura un pedido antes de vencer, contando solo las '
                    'horas de la franja de respuesta'
                ),
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name='Horas para responder',
            ),
        ),
        migrations.AddField(
            model_name='sucursal',
            name='email_avisos',
            field=models.EmailField(
                blank=True,
                help_text=(
                    'A dónde llegan los pedidos de turno de la app. '
                    'Vacío usa el email de la sucursal.'
                ),
                max_length=254,
                verbose_name='Email para avisos',
            ),
        ),
    ]
