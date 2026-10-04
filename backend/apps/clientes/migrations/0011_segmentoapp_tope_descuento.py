"""
Tope en pesos del descuento de la app, por segmento.

Lo pidió AME el 04/10/2026: 15% pero nunca más de $5.000 por compra. Va en el
segmento y no en la integración porque acompaña al porcentaje — si mañana VIP
tiene 20%, su tope puede ser otro.

Nace en NULL, que significa "sin tope": es el comportamiento que había hasta
hoy, así que la migración no cambia nada por sí sola. El tope se carga desde el
CRM.
"""
from decimal import Decimal

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0010_codigorecuperacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='segmentoapp',
            name='tope_descuento',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Máximo en pesos que puede descontar el cupón, por compra. Vacío = sin tope',
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(Decimal('0.01'))],
                verbose_name='Tope del descuento',
            ),
        ),
    ]
