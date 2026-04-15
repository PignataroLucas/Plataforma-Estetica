# WhatsApp Templates Configuration - Implementation Summary

## Overview
Sistema de configuración de plantillas de mensajes WhatsApp para el administrador. Permite personalizar los mensajes de confirmación, recordatorios y cancelaciones que se envían automáticamente a los clientes.

## Status: BACKEND COMPLETADO ✅ | FRONTEND PENDIENTE ⏳

---

## Backend Implementation (COMPLETADO)

### 1. Modelo de Datos
**File**: `backend/apps/notificaciones/models.py`

```python
class MensajeTemplate(models.Model):
    """Plantillas configurables de mensajes WhatsApp"""

    class TipoMensaje(models.TextChoices):
        CONFIRMACION_TURNO = 'CONFIRMACION', 'Confirmación de Turno'
        RECORDATORIO_24H = 'RECORDATORIO_24H', 'Recordatorio 24 horas'
        RECORDATORIO_2H = 'RECORDATORIO_2H', 'Recordatorio 2 horas'
        CANCELACION = 'CANCELACION', 'Cancelación de Turno'
        MODIFICACION = 'MODIFICACION', 'Modificación de Turno'
        PROMOCION = 'PROMOCION', 'Mensaje Promocional'

    sucursal = ForeignKey(Sucursal)  # Multi-tenancy
    tipo = CharField(max_length=30, choices=TipoMensaje.choices)
    mensaje = TextField()  # Contenido con variables {nombre_cliente}, {fecha}, etc.
    activo = BooleanField(default=True)
    actualizado_por = ForeignKey(Usuario)

    unique_together = ['sucursal', 'tipo']  # Una plantilla por tipo por sucursal
```

**Migration**: ✅ `0002_mensajetemplate.py` creada y aplicada

### 2. Serializers
**File**: `backend/apps/notificaciones/serializers.py`

- ✅ `MensajeTemplateSerializer`: Serializer completo para CRUD
- ✅ `MensajeTemplateListSerializer`: Serializer simplificado para listados con preview
- ✅ Validación: Mínimo 10 caracteres en el mensaje

### 3. API Endpoints
**File**: `backend/apps/notificaciones/views.py`

#### MensajeTemplateViewSet (ADMIN only)

| Método | Endpoint | Descripción | Permiso |
|--------|----------|-------------|---------|
| GET | `/api/mensajes-templates/` | Listar templates de la sucursal | ADMIN |
| GET | `/api/mensajes-templates/{id}/` | Obtener un template | ADMIN |
| POST | `/api/mensajes-templates/` | Crear template | ADMIN |
| PUT | `/api/mensajes-templates/{id}/` | Actualizar template | ADMIN |
| DELETE | `/api/mensajes-templates/{id}/` | Eliminar template | ADMIN |
| POST | `/api/mensajes-templates/reset_defaults/` | Restaurar defaults | ADMIN |
| GET | `/api/mensajes-templates/variables_disponibles/` | Listar variables | ADMIN |

**Permisos**: Solo usuarios con `role == 'ADMIN'` pueden crear/editar/eliminar templates.

---

**Última actualización**: 2026-01-14
**Status**: Backend 100% | Frontend 0%
