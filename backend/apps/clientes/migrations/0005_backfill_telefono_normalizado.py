from django.db import migrations


def backfill_telefono_normalizado(apps, schema_editor):
    """Rellena telefono_normalizado (E.164) para todos los clientes existentes."""
    from apps.clientes.utils import normalizar_telefono

    Cliente = apps.get_model('clientes', 'Cliente')
    for cliente in Cliente.objects.all().iterator():
        normalizado = normalizar_telefono(cliente.telefono)
        if normalizado != cliente.telefono_normalizado:
            cliente.telefono_normalizado = normalizado
            cliente.save(update_fields=['telefono_normalizado'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0004_usuariocliente_cliente_telefono_normalizado_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_telefono_normalizado, noop_reverse),
    ]
