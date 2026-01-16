# Generated manually - Data migration for default WhatsApp templates

from django.db import migrations


def crear_templates_default(apps, schema_editor):
    """Crear templates por defecto para todas las sucursales"""
    MensajeTemplate = apps.get_model('notificaciones', 'MensajeTemplate')
    Sucursal = apps.get_model('empleados', 'Sucursal')
    
    defaults = {
        'CONFIRMACION': """¡Hola {nombre_cliente}!

Tu turno ha sido confirmado ✅

📅 Fecha: {fecha}
🕐 Hora: {hora}
💆 Servicio: {servicio}
👤 Profesional: {profesional}
📍 Sucursal: {sucursal_nombre}

Te enviaremos recordatorios antes de tu turno.

¡Te esperamos!""",

        'RECORDATORIO_24H': """Hola {nombre_cliente} 👋

Te recordamos tu turno para mañana:

🕐 {hora} - {servicio}
👤 {profesional}
📍 {sucursal_nombre}

Si necesitas cancelar o reprogramar, contáctanos.

¡Te esperamos!""",

        'RECORDATORIO_2H': """¡Tu turno es en 2 horas! ⏰

🕐 {hora} - {servicio}
📍 {sucursal_direccion}

¡Te esperamos!""",

        'CANCELACION': """Hola {nombre_cliente},

Tu turno del {fecha} a las {hora} ha sido cancelado.

Si deseas reprogramar, contáctanos.

Saludos!""",

        'MODIFICACION': """Hola {nombre_cliente},

Tu turno ha sido modificado ✏️

Nueva fecha y hora:
📅 {fecha}
🕐 {hora}
💆 Servicio: {servicio}
👤 Profesional: {profesional}

¡Nos vemos pronto!""",

        'PROMOCION': """¡Hola {nombre_cliente}! 🎁

Tenemos una promoción especial para ti.

Contáctanos para más información.

📍 {sucursal_nombre}
📞 {sucursal_telefono}"""
    }
    
    # Crear templates para todas las sucursales existentes
    for sucursal in Sucursal.objects.all():
        for tipo, mensaje in defaults.items():
            MensajeTemplate.objects.get_or_create(
                sucursal=sucursal,
                tipo=tipo,
                defaults={'mensaje': mensaje, 'activo': True}
            )


def eliminar_templates_default(apps, schema_editor):
    """Rollback - eliminar templates creados por esta migración"""
    # No hacer nada en el rollback para no borrar templates personalizados
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('notificaciones', '0002_mensajetemplate'),
    ]

    operations = [
        migrations.RunPython(crear_templates_default, eliminar_templates_default),
    ]
