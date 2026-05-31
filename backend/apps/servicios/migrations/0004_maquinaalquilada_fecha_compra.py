from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('servicios', '0003_add_alquiler_maquina'),
    ]

    operations = [
        migrations.AddField(
            model_name='maquinaalquilada',
            name='fecha_compra',
            field=models.DateField(
                blank=True,
                null=True,
                help_text=(
                    'Si la máquina se compró, fecha desde la cual deja de tener costo de '
                    'alquiler. El análisis de rentabilidad solo imputa costo a los servicios '
                    'anteriores a esta fecha.'
                ),
            ),
        ),
    ]
