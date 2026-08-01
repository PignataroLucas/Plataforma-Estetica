from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("servicios", "0006_servicio_beneficios_servicio_video_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="servicio",
            name="fechas_reserva",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=(
                    "Fechas puntuales (YYYY-MM-DD) en que se reserva ESTE servicio, para "
                    "cuando no hay un patrón semanal: la máquina viene el viernes 20 y "
                    "listo. Si hay fechas cargadas REEMPLAZAN a dias_reserva — el servicio "
                    "se reserva solo esos días exactos."
                ),
            ),
        ),
    ]
