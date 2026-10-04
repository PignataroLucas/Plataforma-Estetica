"""
El cupón de la app deja de combinarse con otras promociones, por defecto.

Decisión de AME del 04/10/2026 (COMPRA_EN_APP_SPEC.md §7.2). El caso que la
motivó es el 2x1: con el cupón encima, una promo de ese tipo se lleva el margen
dos veces.

**Solo cambia el default**, no las filas existentes. Un centro que ya hubiera
decidido lo contrario conserva su valor; hoy no hay ninguna integración viva, así
que en los hechos cambia para todos.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integraciones', '0009_tiendanubeprivacyrequest_tiendanubeinstallintent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tiendanubeintegration',
            name='coupons_combine_with_other_discounts',
            field=models.BooleanField(
                default=False,
                help_text='Si está activo, el descuento de la app se suma a las promos de la tienda (2x1, 3x2). Si no, la clienta se lleva el mejor de los dos',
                verbose_name='Los cupones se combinan con otras promociones',
            ),
        ),
    ]
