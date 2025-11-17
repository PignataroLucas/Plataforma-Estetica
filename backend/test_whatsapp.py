#!/usr/bin/env python
"""Script para probar envío de WhatsApp"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.notificaciones.services import whatsapp_service
from apps.clientes.models import Cliente

# Obtener cliente Lucas
cliente = Cliente.objects.get(id=8)
print(f'Cliente: {cliente.nombre_completo}')
print(f'Teléfono: {cliente.telefono}')
print('---')

# Obtener una sucursal del centro
sucursal = cliente.centro_estetica.sucursales.first()

# Enviar mensaje de prueba
notificacion = whatsapp_service.enviar_mensaje(
    telefono=cliente.telefono,
    mensaje='🧪 PRUEBA MANUAL: Este es un mensaje de prueba del sistema. Si lo recibes, responde con OK!',
    tipo_notificacion='OTRO',
    cliente=cliente,
    sucursal=sucursal
)

print(f'Estado: {notificacion.estado}')
print(f'Message SID: {notificacion.mensaje_id_externo}')
if notificacion.error_mensaje:
    print(f'Error: {notificacion.error_mensaje}')
else:
    print('✅ Sin errores - Mensaje enviado correctamente')
