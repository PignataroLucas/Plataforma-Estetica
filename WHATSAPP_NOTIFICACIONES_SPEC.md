# Sistema de Notificaciones WhatsApp - Especificación Completa

Sistema de notificaciones automáticas vía WhatsApp para confirmar turnos, enviar recordatorios y reducir no-shows.

---

## 📊 Resumen Ejecutivo

### Estado Actual: 60% Implementado ✅

**Lo que YA está funcionando:**
- ✅ Modelo de datos completo (`Notificacion`)
- ✅ Servicio de WhatsApp con Twilio (`WhatsAppService`)
- ✅ Templates de mensajes (confirmación, recordatorios, cancelación)
- ✅ Tasks asíncronas con Celery
- ✅ Sistema de recordatorios automáticos programados
- ✅ Manejo de errores y reintentos
- ✅ Soporte para teléfonos argentinos

**Lo que FALTA implementar:**
- ❌ API endpoints (ViewSets, Serializers)
- ❌ Signals para disparar notificaciones automáticamente
- ❌ Configuración de Celery Beat
- ❌ Frontend (historial, configuración)
- ❌ Testing completo
- ❌ Documentación de setup de Twilio

**Tiempo estimado para completar**: 3-4 días

---

## 🎯 Funcionalidades del Sistema

### 1. Notificaciones Automáticas

#### **Confirmación Inmediata** (Al crear turno)
```
¡Hola María!

Tu turno ha sido confirmado ✅

📅 Fecha: 15/01/2026
🕐 Hora: 14:30
💆 Servicio: Masaje Relajante
👤 Profesional: Ana García
📍 Sucursal: Principal

Te enviaremos recordatorios antes de tu turno.

¡Te esperamos!
```

**Cuándo se envía:** Inmediatamente al crear/confirmar un turno
**Trigger:** Signal `post_save` en modelo `Turno`

---

#### **Recordatorio 24 horas antes**
```
Hola María 👋

Te recordamos tu turno para mañana:

🕐 14:30 - Masaje Relajante
👤 Ana García
📍 Sucursal Principal

Si necesitas cancelar o reprogramar, contactanos.

¡Te esperamos!
```

**Cuándo se envía:** 24 horas antes del turno
**Trigger:** Celery Beat task periódica (cada hora)

---

#### **Recordatorio 2 horas antes**
```
¡Tu turno es en 2 horas! ⏰

🕐 14:30 - Masaje Relajante
📍 Av. Santa Fe 1234, Palermo

¡Te esperamos!
```

**Cuándo se envía:** 2 horas antes del turno
**Trigger:** Celery Beat task periódica (cada hora)

---

#### **Notificación de Cancelación**
```
Hola María,

Tu turno del 15/01/2026 a las 14:30 ha sido cancelado.

Si deseas reprogramar, contactanos.

Saludos!
```

**Cuándo se envía:** Al cancelar un turno
**Trigger:** Signal `post_save` en modelo `Turno` cuando `estado` cambia a `CANCELADO`

---

### 2. Tipos de Notificaciones Soportadas

| Tipo | Código | Cuándo se usa |
|------|--------|---------------|
| Confirmación | `CONFIRMACION` | Turno creado/confirmado |
| Recordatorio 24h | `RECORDATORIO_24H` | 24 horas antes |
| Recordatorio 2h | `RECORDATORIO_2H` | 2 horas antes |
| Cancelación | `CANCELACION` | Turno cancelado |
| Modificación | `MODIFICACION` | Turno modificado (fecha/hora) |
| Seguimiento | `SEGUIMIENTO` | Post-tratamiento (manual) |
| Promoción | `PROMOCION` | Campañas (manual) |
| Otro | `OTRO` | Mensajes personalizados |

---

### 3. Estados de Notificación

| Estado | Descripción | Cuándo |
|--------|-------------|--------|
| `PENDIENTE` | Creada pero no enviada | Al crear notificación |
| `ENVIADO` | Enviada a Twilio exitosamente | Después de enviar |
| `ENTREGADO` | WhatsApp confirmó entrega | Webhook de Twilio |
| `LEIDO` | Cliente abrió el mensaje | Webhook de Twilio |
| `FALLIDO` | Error al enviar | Error de Twilio o validación |

---

## 🏗️ Arquitectura del Sistema

### Flujo de Notificaciones

```
┌─────────────────┐
│  Crear Turno    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Signal Django  │ ← post_save de Turno
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Celery Task    │ ← Ejecuta asíncronamente
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ WhatsAppService │ ← Envía via Twilio
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Twilio API     │ ← Envía WhatsApp
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Cliente WA    │ ← Recibe mensaje
└─────────────────┘
```

### Recordatorios Programados

```
┌─────────────────┐
│  Celery Beat    │ ← Cron cada hora
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│ procesar_recordatorios_task     │
└────────┬────────────────────────┘
         │
         ├──► Busca turnos en 24h ──► Envía recordatorio 24h
         │
         └──► Busca turnos en 2h  ──► Envía recordatorio 2h
```

---

## 💻 Implementación Actual (Backend)

### Modelo de Datos ✅ COMPLETO

**Ubicación**: `backend/apps/notificaciones/models.py`

```python
class Notificacion(models.Model):
    # Relaciones
    sucursal = ForeignKey(Sucursal)
    cliente = ForeignKey(Cliente)
    turno = ForeignKey(Turno, null=True, blank=True)

    # Info de notificación
    tipo = CharField(choices=TipoNotificacion.choices)
    mensaje = TextField()
    telefono_destino = CharField(max_length=20)

    # Estado
    estado = CharField(choices=Estado.choices, default=PENDIENTE)

    # Respuesta de Twilio
    mensaje_id_externo = CharField(max_length=100, blank=True)
    error_mensaje = TextField(blank=True)

    # Timestamps
    creado_en = DateTimeField(auto_now_add=True)
    enviado_en = DateTimeField(null=True)
    entregado_en = DateTimeField(null=True)
    leido_en = DateTimeField(null=True)
```

**Campos importantes:**
- `mensaje_id_externo`: SID de Twilio para tracking
- `error_mensaje`: Almacena errores si falla
- Timestamps separados para cada estado

---

### Servicio WhatsApp ✅ COMPLETO

**Ubicación**: `backend/apps/notificaciones/services.py`

**Clase principal**: `WhatsAppService`

**Métodos públicos:**
```python
# Envío genérico
enviar_mensaje(telefono, mensaje, tipo, cliente, turno, sucursal)

# Métodos específicos
enviar_confirmacion_turno(turno)
enviar_recordatorio_24h(turno)
enviar_recordatorio_2h(turno)
enviar_cancelacion_turno(turno)
```

**Características:**
- ✅ Validación de configuración de Twilio
- ✅ Formateo automático de teléfonos argentinos (`+54`)
- ✅ Manejo de errores con TwilioRestException
- ✅ Registro automático en BD (estado PENDIENTE → ENVIADO/FALLIDO)
- ✅ Templates de mensajes customizables
- ✅ Conversión a hora local Argentina

**Ejemplo de uso:**
```python
from apps.notificaciones.services import whatsapp_service

# Enviar confirmación
notificacion = whatsapp_service.enviar_confirmacion_turno(turno)

# Verificar resultado
if notificacion.estado == 'ENVIADO':
    print(f"Enviado! SID: {notificacion.mensaje_id_externo}")
else:
    print(f"Error: {notificacion.error_mensaje}")
```

---

### Tasks Asíncronas ✅ COMPLETO

**Ubicación**: `backend/apps/notificaciones/tasks.py`

**Tasks disponibles:**

#### 1. Confirmación de Turno
```python
@shared_task(bind=True, max_retries=3)
def enviar_confirmacion_turno_task(turno_id):
    """Envía confirmación de turno asíncronamente"""
    # Implementación completa
```

**Uso:**
```python
from apps.notificaciones.tasks import enviar_confirmacion_turno_task

# Llamada asíncrona
enviar_confirmacion_turno_task.delay(turno.id)
```

#### 2. Recordatorio 24 horas
```python
@shared_task(bind=True, max_retries=3)
def enviar_recordatorio_24h_task(turno_id):
    """Envía recordatorio 24h antes"""
    # Verifica que turno siga activo
    # Envía mensaje
```

#### 3. Recordatorio 2 horas
```python
@shared_task(bind=True, max_retries=3)
def enviar_recordatorio_2h_task(turno_id):
    """Envía recordatorio 2h antes"""
```

#### 4. Cancelación
```python
@shared_task(bind=True, max_retries=3)
def enviar_cancelacion_turno_task(turno_id):
    """Envía notificación de cancelación"""
```

#### 5. **Task Periódica (CRÍTICA)**
```python
@shared_task
def procesar_recordatorios_pendientes():
    """
    Ejecuta cada hora vía Celery Beat
    Busca turnos próximos y envía recordatorios
    """
    # Busca turnos en ventana 23-25h → Recordatorio 24h
    # Busca turnos en ventana 1.5-2.5h → Recordatorio 2h
```

**Características:**
- ✅ Reintentos automáticos (max 3)
- ✅ Backoff de 60 segundos entre reintentos
- ✅ Logging completo
- ✅ Verifica estado del turno antes de enviar
- ✅ Marca recordatorios como enviados para evitar duplicados

---

## ❌ Lo que FALTA Implementar

### 1. API Endpoints (ViewSets y Serializers)

**Archivo a crear**: `backend/apps/notificaciones/views.py` (actualmente vacío)

**Endpoints necesarios:**

```python
# GET /api/notificaciones/
# Listar notificaciones (filtrable por cliente, turno, estado, tipo)
class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer
    filterset_fields = ['cliente', 'turno', 'estado', 'tipo', 'sucursal']

    def get_queryset(self):
        # Filtrar por sucursal del usuario
        return Notificacion.objects.filter(
            sucursal=self.request.user.sucursal
        ).select_related('cliente', 'turno')

# POST /api/notificaciones/enviar-manual/
@action(detail=False, methods=['post'])
def enviar_manual(self, request):
    """
    Enviar mensaje manual de WhatsApp
    Body: {
        "cliente_id": 123,
        "tipo": "OTRO",
        "mensaje": "Hola! Tenemos una promo..."
    }
    """
    pass

# GET /api/notificaciones/historial-cliente/{cliente_id}/
@action(detail=False, methods=['get'])
def historial_cliente(self, request, cliente_id):
    """Historial de notificaciones de un cliente"""
    pass

# POST /api/notificaciones/reenviar/{id}/
@action(detail=True, methods=['post'])
def reenviar(self, request, pk):
    """Reenviar notificación fallida"""
    pass
```

**Serializer a crear**:
```python
# backend/apps/notificaciones/serializers.py
class NotificacionSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True)
    turno_info = TurnoBasicoSerializer(source='turno', read_only=True)

    class Meta:
        model = Notificacion
        fields = [
            'id', 'tipo', 'mensaje', 'telefono_destino',
            'estado', 'mensaje_id_externo', 'error_mensaje',
            'cliente', 'cliente_nombre', 'turno', 'turno_info',
            'creado_en', 'enviado_en', 'entregado_en', 'leido_en'
        ]
        read_only_fields = ['mensaje_id_externo', 'estado', 'enviado_en']
```

---

### 2. Signals para Disparar Notificaciones Automáticas

**Archivo a crear**: `backend/apps/turnos/signals.py` (agregar signals)

```python
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from apps.turnos.models import Turno
from apps.notificaciones.tasks import (
    enviar_confirmacion_turno_task,
    enviar_cancelacion_turno_task
)

@receiver(post_save, sender=Turno)
def turno_creado_o_modificado(sender, instance, created, **kwargs):
    """
    Signal que se dispara cuando se crea o modifica un turno
    """
    if created and instance.estado in ['CONFIRMADO', 'PENDIENTE']:
        # Turno nuevo → Enviar confirmación
        enviar_confirmacion_turno_task.delay(instance.id)

    elif not created:
        # Turno modificado → Verificar si fue cancelado
        # Necesitamos comparar estado anterior con estado actual
        pass

# Para detectar cambios de estado, necesitamos pre_save
@receiver(pre_save, sender=Turno)
def turno_pre_save(sender, instance, **kwargs):
    """Guardar estado anterior del turno"""
    if instance.pk:
        try:
            instance._estado_anterior = Turno.objects.get(pk=instance.pk).estado
        except Turno.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None

@receiver(post_save, sender=Turno)
def turno_post_save(sender, instance, created, **kwargs):
    """Detectar cancelación y enviar notificación"""
    if not created and hasattr(instance, '_estado_anterior'):
        if instance._estado_anterior != 'CANCELADO' and instance.estado == 'CANCELADO':
            # Turno cancelado → Enviar notificación
            enviar_cancelacion_turno_task.delay(instance.id)
```

**Registrar signals en apps.py**:
```python
# backend/apps/turnos/apps.py
class TurnosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.turnos'

    def ready(self):
        import apps.turnos.signals  # Importar signals
```

---

### 3. Configuración de Celery Beat

**Archivo a modificar**: `backend/config/celery.py` (o crear si no existe)

```python
# backend/config/celery.py
from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('plataforma_estetica')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# ⭐ CONFIGURACIÓN DE TAREAS PERIÓDICAS
app.conf.beat_schedule = {
    'procesar-recordatorios-cada-hora': {
        'task': 'apps.notificaciones.tasks.procesar_recordatorios_pendientes',
        'schedule': crontab(minute=0),  # Cada hora en punto (00:00, 01:00, etc.)
    },
}

app.conf.timezone = 'America/Argentina/Buenos_Aires'
```

**Variables en settings.py**:
```python
# backend/config/settings.py

# Celery Configuration
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Argentina/Buenos_Aires'

# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_WHATSAPP_NUMBER = config('TWILIO_WHATSAPP_NUMBER', default='+14155238886')
```

---

### 4. Campos Faltantes en Modelo Turno

**Archivo a modificar**: `backend/apps/turnos/models.py`

Agregar estos campos al modelo `Turno`:

```python
class Turno(models.Model):
    # ... campos existentes ...

    # ⭐ AGREGAR ESTOS CAMPOS
    recordatorio_24h_enviado = models.BooleanField(
        default=False,
        help_text="Indica si ya se envió el recordatorio de 24h"
    )
    recordatorio_2h_enviado = models.BooleanField(
        default=False,
        help_text="Indica si ya se envió el recordatorio de 2h"
    )
```

**Crear migración**:
```bash
python manage.py makemigrations turnos
python manage.py migrate
```

---

### 5. Frontend (React)

**Componentes a crear**:

#### Historial de Notificaciones
```typescript
// frontend/src/components/notificaciones/NotificacionesHistorial.tsx
interface Notificacion {
  id: number;
  tipo: string;
  mensaje: string;
  telefono_destino: string;
  estado: 'PENDIENTE' | 'ENVIADO' | 'ENTREGADO' | 'LEIDO' | 'FALLIDO';
  cliente_nombre: string;
  creado_en: string;
  enviado_en: string | null;
}

export default function NotificacionesHistorial() {
  const [notificaciones, setNotificaciones] = useState<Notificacion[]>([]);

  // Fetch notificaciones
  // Mostrar tabla con filtros
  // Badges de color por estado

  return (
    <div>
      <h2>Historial de Notificaciones WhatsApp</h2>
      {/* Tabla con notificaciones */}
    </div>
  );
}
```

#### Enviar Mensaje Manual
```typescript
// frontend/src/components/notificaciones/EnviarMensajeManual.tsx
export default function EnviarMensajeManual() {
  const [clienteId, setClienteId] = useState('');
  const [mensaje, setMensaje] = useState('');

  const handleEnviar = async () => {
    await api.post('/notificaciones/enviar-manual/', {
      cliente_id: clienteId,
      tipo: 'OTRO',
      mensaje: mensaje
    });
  };

  return (
    <form onSubmit={handleEnviar}>
      {/* Selector de cliente */}
      {/* Textarea para mensaje */}
      {/* Botón enviar */}
    </form>
  );
}
```

#### Widget en Detalle de Cliente
```typescript
// frontend/src/components/clientes/ClienteNotificaciones.tsx
export default function ClienteNotificaciones({ clienteId }) {
  const [notificaciones, setNotificaciones] = useState([]);

  useEffect(() => {
    // Fetch /api/notificaciones/?cliente={clienteId}
  }, [clienteId]);

  return (
    <div>
      <h3>Mensajes WhatsApp Enviados</h3>
      {/* Lista de notificaciones */}
    </div>
  );
}
```

---

## 🔧 Configuración de Twilio

### Paso 1: Crear Cuenta en Twilio

1. **Ir a**: https://www.twilio.com/try-twilio
2. **Sign Up** (gratis)
3. **Verificar email** y **número de teléfono**
4. **Recibir USD $15** en créditos gratis

### Paso 2: Configurar WhatsApp Sandbox

**⚠️ IMPORTANTE**: Para usar WhatsApp en producción, necesitás aprobación de Facebook. Para desarrollo, usá el **Sandbox**.

1. En el Dashboard de Twilio, ir a: **Messaging** → **Try it out** → **Send a WhatsApp message**
2. Vas a ver un número de prueba (ej: `+1 415 523 8886`)
3. Enviar un mensaje desde tu WhatsApp personal a ese número con el código que te dan (ej: `join happy-tiger`)
4. Ahora podés enviar mensajes a tu número personal

**Limitaciones del Sandbox:**
- Solo funciona con números que se "unieron" enviando el código
- Expira después de 24 horas sin actividad (hay que re-unirse)
- Los mensajes tienen prefijo "[Sandbox]"

### Paso 3: Obtener Credenciales

En el Dashboard de Twilio:

1. **Account SID**: Encontrar en "Account Info"
2. **Auth Token**: Click en "Show" para revelar
3. **WhatsApp Number**: El número del sandbox (ej: `whatsapp:+14155238886`)

### Paso 4: Configurar en el Proyecto

**Agregar a `.env` (backend)**:
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=tu_auth_token_secreto
TWILIO_WHATSAPP_NUMBER=+14155238886
```

**Verificar configuración**:
```python
# En Django shell
python manage.py shell

from apps.notificaciones.services import whatsapp_service

# Testear envío
mensaje_test = "Hola! Este es un mensaje de prueba desde la plataforma."
telefono_test = "+5491123456789"  # TU número que se unió al sandbox

from apps.clientes.models import Cliente
cliente = Cliente.objects.first()

notificacion = whatsapp_service.enviar_mensaje(
    telefono=telefono_test,
    mensaje=mensaje_test,
    tipo_notificacion='OTRO',
    cliente=cliente,
    sucursal=cliente.sucursal
)

print(f"Estado: {notificacion.estado}")
print(f"Error: {notificacion.error_mensaje}")
```

---

### Paso 5: Aprobar Templates (Para Producción)

**⚠️ Solo necesario para PRODUCCIÓN** (no para Sandbox)

1. En Twilio: **Messaging** → **WhatsApp** → **Senders** → **Request to enable your Twilio number**
2. Completar información del negocio
3. **Crear templates** de mensajes y enviar para aprobación
4. Esperar 1-2 días para aprobación de Facebook
5. Una vez aprobado, cambiar `TWILIO_WHATSAPP_NUMBER` al número real

**Templates a aprobar**:
- Confirmación de turno
- Recordatorio 24h
- Recordatorio 2h
- Cancelación

---

## 💰 Costos de Twilio WhatsApp

### Pricing (Argentina - 2026)

| Concepto | Costo |
|----------|-------|
| **Mensajes salientes** (de tu negocio al cliente) | USD $0.0085/msg |
| **Mensajes entrantes** (del cliente a tu negocio) | USD $0.005/msg |
| **Session fee** (cada 24h) | USD $0.0085 |

### Estimación de Costos

**Escenario 1: Centro pequeño (50 turnos/mes)**
```
Confirmaciones: 50 turnos × $0.0085 = $0.425
Recordatorios 24h: 50 × $0.0085 = $0.425
Recordatorios 2h: 50 × $0.0085 = $0.425
-----------------
Total: $1.28/mes
```

**Escenario 2: Centro mediano (200 turnos/mes)**
```
Confirmaciones: 200 × $0.0085 = $1.70
Recordatorios 24h: 200 × $0.0085 = $1.70
Recordatorios 2h: 200 × $0.0085 = $1.70
-----------------
Total: $5.10/mes
```

**Escenario 3: Centro grande (500 turnos/mes)**
```
Confirmaciones: 500 × $0.0085 = $4.25
Recordatorios 24h: 500 × $0.0085 = $4.25
Recordatorios 2h: 500 × $0.0085 = $4.25
-----------------
Total: $12.75/mes
```

**Créditos gratis**: USD $15 al crear cuenta = ~1700 mensajes gratis

---

## 📋 Plan de Implementación

### Fase 1: Configuración Básica (Día 1)

**Tareas:**
- [ ] Crear cuenta en Twilio
- [ ] Configurar WhatsApp Sandbox
- [ ] Agregar credenciales a `.env`
- [ ] Testear envío manual desde Django shell
- [ ] Verificar que `WhatsAppService` funciona

**Resultado**: Poder enviar mensajes de WhatsApp manualmente

---

### Fase 2: API y Signals (Día 2)

**Tareas:**
- [ ] Crear `NotificacionSerializer` en `serializers.py`
- [ ] Crear `NotificacionViewSet` en `views.py`
- [ ] Registrar endpoints en `urls.py`
- [ ] Crear signals en `apps/turnos/signals.py`
- [ ] Agregar campos `recordatorio_24h_enviado` y `recordatorio_2h_enviado` al modelo `Turno`
- [ ] Crear y ejecutar migraciones

**Resultado**: Confirmaciones automáticas al crear turnos

---

### Fase 3: Celery Beat y Recordatorios (Día 3)

**Tareas:**
- [ ] Configurar Celery Beat en `config/celery.py`
- [ ] Testear task periódica `procesar_recordatorios_pendientes`
- [ ] Correr Celery worker: `celery -A config worker -l info`
- [ ] Correr Celery beat: `celery -A config beat -l info`
- [ ] Crear turnos de prueba para verificar recordatorios

**Resultado**: Recordatorios automáticos funcionando

---

### Fase 4: Frontend (Día 4)

**Tareas:**
- [ ] Crear `NotificacionesHistorial.tsx`
- [ ] Crear `EnviarMensajeManual.tsx`
- [ ] Agregar widget en `ClienteDetailPage.tsx`
- [ ] Crear hook `useNotificaciones.ts`
- [ ] Agregar ruta `/notificaciones` en React Router
- [ ] Agregar link en navbar (solo para Admin)

**Resultado**: UI completa para ver y gestionar notificaciones

---

### Fase 5: Testing y Ajustes (Opcional)

**Tareas:**
- [ ] Tests unitarios para `WhatsAppService`
- [ ] Tests de integración para tasks
- [ ] Tests de signals
- [ ] Tests de API endpoints
- [ ] Ajustar templates de mensajes según feedback
- [ ] Documentar en README

---

## 🧪 Testing Manual

### Test 1: Confirmación Automática

```bash
# 1. Crear turno desde UI o API
POST /api/turnos/
{
  "cliente": 1,
  "servicio": 1,
  "profesional": 1,
  "fecha_hora_inicio": "2026-01-20T14:30:00",
  "estado": "CONFIRMADO"
}

# 2. Verificar que se creó la notificación
GET /api/notificaciones/?turno={turno_id}

# 3. Verificar que el mensaje llegó a WhatsApp
# (Revisar tu teléfono)
```

### Test 2: Recordatorio 24h

```bash
# 1. Crear turno para mañana a la misma hora
turno_mañana = crear turno para (ahora + 24 horas)

# 2. Ejecutar task manualmente (sin esperar)
python manage.py shell
>>> from apps.notificaciones.tasks import procesar_recordatorios_pendientes
>>> procesar_recordatorios_pendientes()

# 3. Verificar que se envió
GET /api/notificaciones/?tipo=RECORDATORIO_24H
```

### Test 3: Cancelación

```bash
# 1. Cancelar turno existente
PATCH /api/turnos/{id}/
{
  "estado": "CANCELADO"
}

# 2. Verificar notificación de cancelación
GET /api/notificaciones/?turno={turno_id}&tipo=CANCELACION
```

---

## 🚨 Troubleshooting Común

### Error: "Unable to create record: Permission to send an SMS"
**Solución**: Tu número no está verificado en el Sandbox. Enviar el código de unión nuevamente.

### Error: "Twilio no está configurado"
**Solución**: Verificar que `TWILIO_ACCOUNT_SID` y `TWILIO_AUTH_TOKEN` están en `.env` y `settings.py` los lee correctamente.

### Los recordatorios no se envían automáticamente
**Solución**:
1. Verificar que Celery Beat está corriendo
2. Verificar que Redis está corriendo
3. Revisar logs de Celery Beat
4. Verificar que los campos `recordatorio_24h_enviado` existen en modelo Turno

### Mensaje se envía pero estado queda en PENDIENTE
**Solución**: Twilio puede tardar unos segundos. El estado se actualiza vía webhooks (requiere configuración adicional en producción).

### Formato de teléfono incorrecto
**Solución**: Asegurar que el teléfono del cliente tiene formato `+5491123456789` o `1123456789` (se formatea automáticamente).

---

## 📚 Recursos y Referencias

**Twilio Docs:**
- WhatsApp API: https://www.twilio.com/docs/whatsapp
- Python SDK: https://www.twilio.com/docs/libraries/python
- Sandbox: https://www.twilio.com/docs/whatsapp/sandbox

**Django/Celery:**
- Celery Beat: https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html
- Django Signals: https://docs.djangoproject.com/en/4.2/topics/signals/

---

## 🎯 Próximos Pasos Sugeridos

1. **Ahora**: Configurar Twilio y testear envío manual
2. **Después**: Implementar API endpoints y signals (Fase 2)
3. **Luego**: Configurar Celery Beat (Fase 3)
4. **Finalmente**: Crear UI (Fase 4)

**Tiempo total estimado**: 3-4 días de desarrollo

---

## ✅ Checklist de Implementación

### Backend
- [ ] Cuenta Twilio creada
- [ ] Sandbox configurado
- [ ] Variables en `.env`
- [ ] Test manual exitoso
- [ ] `NotificacionSerializer` creado
- [ ] `NotificacionViewSet` creado
- [ ] Endpoints registrados
- [ ] Signals creados en `turnos`
- [ ] Campos agregados a modelo `Turno`
- [ ] Migraciones ejecutadas
- [ ] Celery configurado
- [ ] Celery Beat configurado
- [ ] Workers corriendo
- [ ] Tests de confirmación ✓
- [ ] Tests de recordatorios ✓

### Frontend
- [ ] Hook `useNotificaciones`
- [ ] Componente `NotificacionesHistorial`
- [ ] Componente `EnviarMensajeManual`
- [ ] Widget en detalle de cliente
- [ ] Ruta `/notificaciones`
- [ ] Link en navbar

### Producción
- [ ] Solicitar aprobación de templates en Twilio
- [ ] Configurar webhooks de Twilio (status callbacks)
- [ ] Monitoreo de costos en Twilio
- [ ] Logs de errores en Sentry

---

**Última actualización**: Enero 2026
**Estado**: 60% completo - Listo para implementar faltantes
