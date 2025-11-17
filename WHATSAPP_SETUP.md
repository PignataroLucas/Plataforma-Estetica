# Configuración de Notificaciones WhatsApp con Twilio

## Resumen

El sistema envía notificaciones automáticas por WhatsApp en los siguientes momentos:
- ✅ **Confirmación inmediata** al crear un turno
- ⏰ **Recordatorio 24 horas antes** del turno
- ⏰ **Recordatorio 2 horas antes** del turno
- ❌ **Notificación de cancelación** cuando se cancela un turno

---

## Paso 1: Crear Cuenta Twilio (5 minutos)

### 1.1 Registro

1. Ir a https://www.twilio.com/try-twilio
2. Click en "Sign up"
3. Completar el formulario:
   - Email
   - Contraseña
   - Datos personales
4. Verificar email y teléfono

**Crédito inicial**: $15 USD gratis (suficiente para ~3000 mensajes de prueba)

### 1.2 Obtener Credenciales

Una vez dentro de la consola de Twilio:

1. Ir a **Console Dashboard** (https://console.twilio.com/)
2. Encontrarás:
   ```
   Account SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   Auth Token: [Click en "Show" para ver]
   ```
3. **Copiar y guardar** ambos valores

---

## Paso 2: Activar WhatsApp Sandbox (2 minutos)

### 2.1 Acceder al Sandbox

1. En Twilio Console, ir a:
   - **Messaging** → **Try it out** → **Send a WhatsApp message**
   - O directamente: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn

2. Verás una pantalla con:
   ```
   Twilio Sandbox Number: +1 415 523 8886 (o similar)
   Join code: join <palabra-única>

   Ejemplo: join cotton-moon
   ```

### 2.2 Activar tu Teléfono

1. Desde tu WhatsApp personal, **agregar el número de Twilio** como contacto:
   ```
   +1 415 523 8886
   ```

2. **Enviar mensaje** al contacto con el código:
   ```
   join cotton-moon
   ```
   (Reemplaza "cotton-moon" con tu código único)

3. Recibirás respuesta de confirmación:
   ```
   ✅ Joined cotton-moon. Tap this link to read more: https://...
   ```

**Nota**: Puedes registrar hasta 5 números en el sandbox para testing.

---

## Paso 3: Configurar Variables de Entorno

### 3.1 Crear archivo .env

En la carpeta `backend/`, crear un archivo `.env` (si no existe) con:

```bash
# Copiar de .env.example y completar con tus valores:

# Twilio Credentials
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=tu_auth_token_aqui
TWILIO_WHATSAPP_NUMBER=+14155238886  # Número del sandbox
```

**Importante**:
- ⚠️ El archivo `.env` está en `.gitignore` - NO lo subas a Git
- El `TWILIO_WHATSAPP_NUMBER` debe incluir el `+` y no tener espacios

### 3.2 Verificar Configuración

Ejecutar este comando para verificar que las variables estén cargadas:

```bash
docker-compose exec backend python manage.py shell

>>> from django.conf import settings
>>> print(settings.TWILIO_ACCOUNT_SID)
ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Debe mostrar tu SID

>>> print(settings.TWILIO_AUTH_TOKEN)
tu_auth_token_aqui  # Debe mostrar tu token

>>> print(settings.TWILIO_WHATSAPP_NUMBER)
+14155238886  # Debe mostrar el número
```

Salir con `exit()`.

---

## Paso 4: Reiniciar Servicios

Para que las nuevas variables de entorno se carguen:

```bash
docker-compose restart backend celery celery-beat
```

Verificar que todo esté corriendo:

```bash
docker-compose ps

# Deberías ver:
# - backend: Up
# - celery: Up
# - celery-beat: Up
```

---

## Paso 5: Probar el Sistema

### 5.1 Prueba Manual desde Django Shell

```bash
docker-compose exec backend python manage.py shell
```

```python
from apps.notificaciones.services import whatsapp_service
from apps.clientes.models import Cliente

# Obtener un cliente de prueba
cliente = Cliente.objects.first()

# Verificar que el cliente tenga teléfono válido
print(f"Cliente: {cliente.nombre_completo}")
print(f"Teléfono: {cliente.telefono}")

# Si el teléfono no está en formato internacional, actualizarlo:
# cliente.telefono = "+5491123456789"  # Tu número registrado en sandbox
# cliente.save()

# Enviar mensaje de prueba
notificacion = whatsapp_service.enviar_mensaje(
    telefono=cliente.telefono,
    mensaje="¡Hola! Este es un mensaje de prueba del sistema. ✅",
    tipo_notificacion='OTRO',
    cliente=cliente
)

print(f"Estado: {notificacion.estado}")
print(f"Message SID: {notificacion.mensaje_id_externo}")
```

**Resultado esperado**:
- Deberías recibir el mensaje en tu WhatsApp en 2-5 segundos
- El estado debe ser `ENVIADO`
- Debe aparecer un Message SID (ej: `SMxxxxxxxxxxxxxxxxxx`)

### 5.2 Prueba Creando un Turno

1. Ir a la aplicación admin: http://localhost:5173
2. Login
3. Ir a **Turnos** → **+ Nuevo Turno**
4. Llenar el formulario:
   - Cliente: Seleccionar cliente con teléfono registrado en sandbox
   - Servicio: Cualquiera
   - Profesional: Cualquiera
   - Fecha/Hora: Cualquier fecha futura
5. Click en **Crear Turno**

**Resultado esperado**:
- Turno creado exitosamente
- En 2-5 segundos, recibirás WhatsApp de confirmación
- Mensaje similar a:
  ```
  ¡Hola [Nombre]!

  Tu turno ha sido confirmado ✅

  📅 Fecha: 20/11/2025
  🕐 Hora: 15:00
  💆 Servicio: Limpieza Facial
  👤 Profesional: María García
  📍 Sucursal: Centro

  Te enviaremos recordatorios antes de tu turno.

  ¡Te esperamos!
  ```

### 5.3 Verificar Logs

Revisar logs de Celery para confirmar que la task se ejecutó:

```bash
docker-compose logs celery --tail=50
```

Deberías ver:
```
[INFO] WhatsApp enviado exitosamente a +5491123456789. SID: SMxxxxxxxxx
[INFO] Confirmación enviada para turno 123
```

---

## Paso 6: Configurar Recordatorios Automáticos

### 6.1 Verificar Celery Beat

Celery Beat se ejecuta automáticamente cada hora para procesar recordatorios.

Verificar que esté corriendo:

```bash
docker-compose logs celery-beat --tail=30
```

Deberías ver algo como:
```
[INFO] Scheduler: Sending due task procesar-recordatorios-turnos
[INFO] celery.worker.strategy: Received task: apps.notificaciones.tasks.procesar_recordatorios_pendientes
```

### 6.2 Probar Recordatorios Manualmente

Para no esperar 24 horas, puedes ejecutar la task manualmente:

```bash
docker-compose exec backend python manage.py shell
```

```python
from apps.notificaciones.tasks import procesar_recordatorios_pendientes

# Ejecutar task de forma síncrona
result = procesar_recordatorios_pendientes()
print(result)
# Output:
# {
#   'recordatorios_24h': 0,
#   'recordatorios_2h': 0,
#   'timestamp': '2025-11-17T10:00:00...'
# }
```

### 6.3 Crear Turno para Prueba de Recordatorios

Para probar recordatorios, crear un turno para dentro de 24 horas:

1. Crear turno para mañana a esta hora
2. Ejecutar manualmente la task (paso 6.2)
3. Deberías recibir el recordatorio de 24h

---

## Troubleshooting

### ❌ Error: "Twilio no está configurado"

**Solución**:
- Verificar que las variables de entorno estén en `.env`
- Reiniciar backend: `docker-compose restart backend`

### ❌ Error: "Unable to create record: The 'To' number is not a valid phone number"

**Solución**:
- Verificar que el teléfono del cliente esté en formato internacional: `+5491123456789`
- Asegurarse que el número esté registrado en el sandbox de Twilio

### ❌ Error: "The message From/To pair violates a blacklist rule"

**Solución**:
- El número NO está registrado en el sandbox
- Enviar `join codigo-unico` desde ese número al sandbox de Twilio

### ❌ No recibo mensajes pero el estado es "ENVIADO"

**Solución**:
- Verificar que el sandbox siga activo
- Re-enviar el código de join al número de Twilio
- Esperar 1-2 minutos (a veces hay delay)

### ❌ Mensajes tienen prefijo "Sent from your Twilio Sandbox..."

**Esto es normal en sandbox**. Para quitarlo:
- Migrar a Twilio Production (requiere número dedicado)
- Ver `CLIENTE_APP_ROADMAP.md` sección "Etapa 2: Producción"

---

## Formato de Teléfonos

### Argentina

```
Formato correcto:
+5491123456789

Incorrecto:
1123456789       ❌ (falta código país)
5491123456789    ❌ (falta +)
+54 911 2345 6789  ❌ (no usar espacios)
```

### Otros países

```
México: +52XXXXXXXXXX
España: +34XXXXXXXXX
Colombia: +57XXXXXXXXXX
Chile: +56XXXXXXXXX
```

---

## Costos y Límites

### Sandbox (Testing)
- **Costo**: GRATIS
- **Crédito inicial**: $15 USD
- **Límite**: 5 números registrados
- **Mensajes**: ~3000 con el crédito inicial
- **Prefijo**: "Sent from your Twilio Sandbox..."

### Production (Cuando tengas clientes reales)
- **Número dedicado**: $1.50 USD/mes
- **Costo por mensaje**: $0.005 USD (~$5 ARS)
- **Límite**: Ilimitados números
- **Sin prefijo**: Mensajes sin "Sandbox"

**Ejemplo costo mensual** (100 turnos):
- 100 turnos × 3 mensajes (confirmación + 2 recordatorios) = 300 mensajes
- 300 × $0.005 = $1.50 USD en mensajes
- Número: $1.50 USD
- **Total**: ~$3 USD/mes (~$3000 ARS)

---

## Próximos Pasos

Una vez que tengas esto funcionando:

1. ✅ **Testear con tu equipo** (máximo 5 teléfonos en sandbox)
2. ✅ **Validar templates** de mensajes (editar en `apps/notificaciones/services.py`)
3. ✅ **Ajustar horarios** de recordatorios si es necesario
4. 🔜 **Migrar a Production** cuando estés listo para clientes reales
5. 🔜 **Implementar app cliente** para que clientes reserven online

---

## Soporte

Si tienes problemas:

1. Revisar logs: `docker-compose logs backend celery celery-beat`
2. Verificar notificaciones en Django Admin: http://localhost:8000/admin/notificaciones/notificacion/
3. Consultar documentación Twilio: https://www.twilio.com/docs/whatsapp

---

**¡Listo! Tu sistema de notificaciones WhatsApp está configurado.** 🎉

Cuando crees un turno, el cliente recibirá confirmación inmediata y recordatorios automáticos.
