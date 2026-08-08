"""
El push token deja de ser un campo de la cuenta y pasa a ser una tabla.

Un campo único por cuenta significaba un solo teléfono: instalar la app en uno
nuevo apagaba el anterior sin avisar. Antes de borrar la columna se pasa lo que
haya a ``DispositivoPush``, así una cuenta que ya tenía token no se queda muda.
"""
from django.db import migrations


def token_a_dispositivo(apps, schema_editor):
    UsuarioCliente = apps.get_model('clientes', 'UsuarioCliente')
    DispositivoPush = apps.get_model('notificaciones', 'DispositivoPush')

    DispositivoPush.objects.bulk_create(
        [
            DispositivoPush(
                usuario_cliente_id=usuario_id,
                token=token,
                plataforma='DESCONOCIDA',
                activo=True,
            )
            for usuario_id, token in UsuarioCliente.objects
            .exclude(push_token__isnull=True)
            .exclude(push_token='')
            .values_list('id', 'push_token')
        ],
        # El token es único: si la app ya registró el dispositivo por la vía
        # nueva, esta migración no lo pisa.
        ignore_conflicts=True,
    )


def dispositivo_a_token(apps, schema_editor):
    """Vuelta atrás: se recupera un token por cuenta, el más reciente."""
    UsuarioCliente = apps.get_model('clientes', 'UsuarioCliente')
    DispositivoPush = apps.get_model('notificaciones', 'DispositivoPush')

    for dispositivo in DispositivoPush.objects.filter(activo=True).order_by('actualizado_en'):
        UsuarioCliente.objects.filter(id=dispositivo.usuario_cliente_id).update(
            push_token=dispositivo.token
        )


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0007_alter_vinculacioncliente_metodo_vinculacion"),
        # La tabla destino tiene que existir antes de copiar.
        ("notificaciones", "0004_aviso_dispositivopush_preferencianotificacion_and_more"),
    ]

    operations = [
        migrations.RunPython(token_a_dispositivo, dispositivo_a_token),
        migrations.RemoveField(
            model_name="usuariocliente",
            name="push_token",
        ),
    ]
