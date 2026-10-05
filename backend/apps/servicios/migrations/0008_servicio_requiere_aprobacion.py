"""
Si un servicio pedido desde la app queda esperando el visto bueno del centro.

Nace en True para todos: AME pidió revisar cada pedido (APROBACION_TURNOS_SPEC.md
§3.3). El campo existe desde ahora para que el día que quiera que algún servicio
se confirme solo sea destildar un check y no una migración con datos encima.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('servicios', '0007_servicio_fechas_reserva'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicio',
            name='requiere_aprobacion',
            field=models.BooleanField(
                default=True,
                help_text=(
                    'Si está activo, el turno pedido desde la app queda pendiente '
                    'hasta que alguien del centro lo acepte o lo rechace.'
                ),
                verbose_name='Requiere aprobación del centro',
            ),
        ),
    ]
