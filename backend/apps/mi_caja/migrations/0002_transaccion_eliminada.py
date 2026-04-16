from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mi_caja', '0001_initial'),
        ('empleados', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransaccionEliminada',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('eliminada_en', models.DateTimeField(auto_now_add=True)),
                ('motivo', models.TextField(help_text='Motivo obligatorio de la eliminación')),
                ('transaccion_id_original', models.IntegerField(help_text='ID original de la transacción eliminada')),
                ('tipo', models.CharField(max_length=20)),
                ('monto', models.DecimalField(decimal_places=2, max_digits=10)),
                ('metodo_pago', models.CharField(max_length=20)),
                ('fecha', models.DateField()),
                ('descripcion', models.CharField(max_length=300)),
                ('notas_originales', models.TextField(blank=True)),
                ('cliente_nombre', models.CharField(blank=True, max_length=200)),
                ('registrada_por_nombre', models.CharField(blank=True, max_length=200)),
                ('eliminada_por', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='transacciones_eliminadas',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('sucursal', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='transacciones_eliminadas',
                    to='empleados.sucursal',
                )),
            ],
            options={
                'verbose_name': 'Transacción Eliminada',
                'verbose_name_plural': 'Transacciones Eliminadas',
                'ordering': ['-eliminada_en'],
            },
        ),
    ]
