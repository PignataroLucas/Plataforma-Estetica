# App Cliente - Roadmap de Implementación

## Visión General

Desarrollar una aplicación web orientada al cliente final que permita:
- Ver disponibilidad de turnos en tiempo real
- Reservar turnos online
- Comprar productos del catálogo
- Gestionar sus propios turnos (ver, cancelar, reagendar)
- Recibir notificaciones por WhatsApp

## Arquitectura: Monorepo

### Estructura del Proyecto

```
Plataforma-Estetica/  (repositorio actual)
├── backend/           (Django - Backend compartido)
│   ├── apps/
│   │   ├── clientes/       (existente)
│   │   ├── turnos/         (existente)
│   │   ├── inventario/     (existente)
│   │   ├── servicios/      (existente)
│   │   ├── public_api/     (NUEVO - endpoints públicos sin auth)
│   │   └── client_api/     (NUEVO - endpoints para clientes autenticados)
│   └── config/
│
├── frontend/          (Admin App - React existente)
│   └── src/
│
├── client-app/        (NUEVO - App Cliente React)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── ServiciosPage.tsx
│   │   │   ├── ReservarTurnoPage.tsx
│   │   │   ├── MisTurnosPage.tsx
│   │   │   ├── ProductosPage.tsx
│   │   │   └── MiPerfilPage.tsx
│   │   ├── components/
│   │   │   ├── calendario/
│   │   │   ├── productos/
│   │   │   └── ui/
│   │   └── services/
│   │       └── api.ts
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── docker-compose.yml (actualizar - agregar servicio client-app)
└── README.md
```

### Ventajas del Monorepo

✅ **Backend único**: Misma base de datos, misma lógica de negocio
✅ **Single source of truth**: No hay duplicación de código
✅ **Multi-tenancy funciona**: Cada cliente ve solo su centro
✅ **Prevención double-booking**: Reutiliza lógica existente
✅ **Deploy coordinado**: Cambios sincronizados entre admin y cliente
✅ **Mantenimiento simplificado**: Un solo repositorio

## Fase 1: MVP Cliente (2-3 semanas)

### Backend - Nuevos Endpoints

#### 1. Public API (Sin autenticación)

**Archivo**: `backend/apps/public_api/`

```python
# Endpoints públicos
GET  /api/public/centros/<centro_id>/disponibilidad/
     - Parámetros: fecha, servicio_id, profesional_id
     - Respuesta: Lista de slots disponibles
     - Nota: Solo slots futuros, sin datos sensibles

GET  /api/public/centros/<centro_id>/servicios/
     - Respuesta: Catálogo de servicios activos
     - Datos: nombre, descripción, duración, precio

GET  /api/public/centros/<centro_id>/productos/
     - Respuesta: Solo productos REVENTA activos
     - Datos: nombre, descripción, precio_venta, stock_actual

GET  /api/public/centros/<centro_id>/info/
     - Respuesta: Información del centro (nombre, dirección, horarios)
```

#### 2. Client API (Clientes autenticados)

**Archivo**: `backend/apps/client_api/`

```python
# Autenticación de clientes
POST /api/client/auth/register/
     - Body: email, password, nombre, apellido, telefono
     - Respuesta: access_token, refresh_token, cliente_data

POST /api/client/auth/login/
     - Body: email, password
     - Respuesta: access_token, refresh_token, cliente_data

# Gestión de turnos del cliente
GET  /api/client/turnos/
     - Respuesta: Turnos del cliente (próximos y pasados)

POST /api/client/turnos/reservar/
     - Body: servicio_id, fecha_hora_inicio, profesional_id (opcional)
     - Validaciones:
       * Disponibilidad en tiempo real
       * Prevención double-booking (reutiliza lógica existente)
       * Horario dentro del rango permitido
     - Respuesta: turno creado + notificación WhatsApp

POST /api/client/turnos/<id>/cancelar/
     - Validaciones:
       * Solo puede cancelar sus propios turnos
       * Solo turnos futuros
       * Tiempo mínimo de anticipación (configurable)
     - Respuesta: turno actualizado + notificación WhatsApp

GET  /api/client/perfil/
     - Respuesta: Datos del cliente

PUT  /api/client/perfil/
     - Body: Datos actualizables del cliente
```

#### 3. Permisos y Seguridad

```python
# Nuevas permission classes
class IsPublic(BasePermission):
    """Permite acceso sin autenticación"""
    def has_permission(self, request, view):
        return True

class IsClient(BasePermission):
    """Solo clientes autenticados"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'cliente')

class IsClientOwner(BasePermission):
    """Cliente solo accede a sus propios recursos"""
    def has_object_permission(self, request, view, obj):
        return obj.cliente == request.user.cliente
```

#### 4. Rate Limiting

```python
# Prevenir abuse de endpoints públicos
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',    # Usuarios anónimos
        'user': '1000/hour',   # Clientes autenticados
    }
}
```

### Frontend Cliente - App Web Responsive

**Tecnologías**: React 18 + TypeScript + Vite + TailwindCSS

#### Páginas Principales

**1. HomePage**
```typescript
// Página de bienvenida
- Información del centro de estética
- Servicios destacados
- Botón CTA: "Reservar Turno"
- Login/Registro
```

**2. ServiciosPage**
```typescript
// Catálogo de servicios
- Grid de servicios con:
  * Nombre y descripción
  * Duración estimada
  * Precio
  * Botón: "Reservar"
- Filtros por categoría
```

**3. ReservarTurnoPage**
```typescript
// Flujo de reserva
Step 1: Seleccionar servicio
Step 2: Seleccionar profesional (opcional o "Sin preferencia")
Step 3: Calendario con slots disponibles
        - Días disponibles marcados
        - Horarios disponibles por día
        - Actualización en tiempo real
Step 4: Confirmar datos
        - Datos del cliente
        - Resumen del turno
        - Opciones de pago (si aplica)
Step 5: Confirmación
        - Turno creado exitosamente
        - Notificación WhatsApp enviada
```

**4. MisTurnosPage** (requiere login)
```typescript
// Gestión de turnos del cliente
- Tabs: "Próximos" / "Pasados"
- Tarjetas de turno mostrando:
  * Fecha y hora
  * Servicio
  * Profesional
  * Estado
  * Acciones: Ver detalle, Cancelar (si es futuro)
```

**5. ProductosPage**
```typescript
// E-commerce de productos (Fase 2)
- Grid de productos
- Carrito de compras
- Checkout con MercadoPago/Stripe
```

#### Componentes Reutilizables

```typescript
// client-app/src/components/

// Calendario
<DisponibilidadCalendar
  servicio={servicio}
  profesional={profesional}
  onSelectSlot={(slot) => ...}
/>

// Tarjeta de servicio
<ServicioCard
  servicio={servicio}
  onReservar={() => ...}
/>

// Tarjeta de turno
<TurnoCard
  turno={turno}
  onCancelar={() => ...}
/>

// UI Components (reutilizar del admin)
<Button />
<Card />
<Modal />
<Input />
```

### Docker Configuration

**Actualizar `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  db:
    # ... existente

  redis:
    # ... existente

  backend:
    # ... existente

  frontend:  # Admin App
    build:
      context: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
    environment:
      - VITE_API_URL=http://localhost:8000

  client-app:  # NUEVO - Cliente App
    build:
      context: ./client-app
      dockerfile: Dockerfile
    ports:
      - "5174:5173"  # Puerto diferente
    volumes:
      - ./client-app:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend

  celery:
    # ... existente

  celery-beat:
    # ... existente
```

### URLs de Acceso

```
Admin App:   http://localhost:5173
Client App:  http://localhost:5174
Backend API: http://localhost:8000
```

## Fase 2: E-commerce (2 semanas)

### Funcionalidades

1. **Catálogo de Productos**
   - Solo productos tipo REVENTA
   - Stock en tiempo real
   - Imágenes de productos

2. **Carrito de Compras**
   - Agregar/quitar productos
   - Actualizar cantidades
   - Calcular total

3. **Checkout**
   - Datos de envío
   - Método de pago
   - Integración MercadoPago/Stripe

4. **Backend - Nuevos Endpoints**

```python
# Carrito
POST /api/client/carrito/agregar/
GET  /api/client/carrito/
PUT  /api/client/carrito/<item_id>/
DELETE /api/client/carrito/<item_id>/

# Pedidos
POST /api/client/pedidos/crear/
GET  /api/client/pedidos/
GET  /api/client/pedidos/<id>/

# Pagos
POST /api/client/pagos/mercadopago/crear/
POST /api/client/pagos/mercadopago/webhook/
```

5. **Modelo de Pedido**

```python
class Pedido(models.Model):
    cliente = models.ForeignKey(Cliente)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        choices=[
            ('PENDIENTE', 'Pendiente'),
            ('PAGADO', 'Pagado'),
            ('ENVIADO', 'Enviado'),
            ('ENTREGADO', 'Entregado'),
            ('CANCELADO', 'Cancelado'),
        ]
    )

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido)
    producto = models.ForeignKey(Producto)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
```

## Fase 3: Mejoras y Features Avanzadas (1-2 semanas)

### 1. Historial de Tratamientos
- Cliente ve su historial completo
- Fotos antes/después (si el centro lo permite)
- Observaciones de profesionales

### 2. Sistema de Fidelidad
- Puntos por visitas
- Descuentos acumulables
- Promociones exclusivas

### 3. Reagendar Turnos
- Cliente puede cambiar fecha/hora
- Validación de disponibilidad
- Sin penalización (configurable)

### 4. Notificaciones Push
- Recordatorios de turnos
- Ofertas y promociones
- Novedades del centro

### 5. Valoraciones
- Cliente puede valorar servicios
- Rating de profesionales
- Comentarios

## Flujo de Reserva de Turno (Detallado)

### 1. Cliente selecciona servicio
```
GET /api/public/centros/{centro_id}/servicios/
→ Lista de servicios disponibles
```

### 2. Sistema muestra disponibilidad
```
GET /api/public/centros/{centro_id}/disponibilidad/
    ?servicio_id=1
    &fecha=2025-11-20
    &profesional_id=2 (opcional)

→ Response:
{
  "fecha": "2025-11-20",
  "slots_disponibles": [
    {
      "hora_inicio": "09:00",
      "hora_fin": "10:00",
      "profesional_id": 2,
      "profesional_nombre": "María García",
      "disponible": true
    },
    {
      "hora_inicio": "10:00",
      "hora_fin": "11:00",
      "profesional_id": 2,
      "profesional_nombre": "María García",
      "disponible": false,
      "motivo": "Ya reservado"
    },
    ...
  ]
}
```

### 3. Cliente selecciona slot y confirma

```
POST /api/client/turnos/reservar/

Headers:
  Authorization: Bearer {access_token}

Body:
{
  "servicio_id": 1,
  "profesional_id": 2,
  "fecha_hora_inicio": "2025-11-20T09:00:00",
  "notas": "Primera vez en el centro"
}

→ Validaciones backend:
  1. Cliente autenticado
  2. Servicio existe y está activo
  3. Profesional existe (si se especificó)
  4. Slot todavía disponible (double-check)
  5. No hay conflictos de horario
  6. Horario dentro del rango permitido

→ Si todo OK:
  1. Crear turno con estado PENDIENTE o CON_SENA
  2. Enviar notificación WhatsApp al cliente
  3. Notificar al centro (opcional)

→ Response:
{
  "id": 123,
  "servicio": "Limpieza Facial",
  "profesional": "María García",
  "fecha_hora_inicio": "2025-11-20T09:00:00",
  "fecha_hora_fin": "2025-11-20T10:00:00",
  "estado": "PENDIENTE",
  "monto_total": 5000,
  "mensaje": "Turno reservado exitosamente. Recibirás una confirmación por WhatsApp."
}
```

## Seguridad y Validaciones Críticas

### 1. Prevención Double-Booking
```python
# Reutilizar lógica existente de TurnoViewSet
def validar_disponibilidad(servicio, profesional, fecha_inicio, fecha_fin):
    """
    Verifica que no haya conflictos de horario
    - Mismo profesional
    - Mismo rango de tiempo
    - Turno activo (no cancelado)
    """
    conflictos = Turno.objects.filter(
        profesional=profesional,
        fecha_hora_inicio__lt=fecha_fin,
        fecha_hora_fin__gt=fecha_inicio,
        estado__in=['PENDIENTE', 'CONFIRMADO']
    ).exists()

    if conflictos:
        raise ValidationError("El horario ya no está disponible")
```

### 2. Rate Limiting por Cliente
```python
# Prevenir spam de reservas
- Máximo 5 reservas por hora por cliente
- Máximo 10 cancelaciones por mes
```

### 3. Validación de Datos del Cliente
```python
# En registro
- Email único
- Teléfono válido (formato argentino)
- Password seguro (min 8 caracteres)

# En reserva
- Solo turnos futuros
- Mínimo 1 hora de anticipación (configurable)
- Máximo 60 días en el futuro (configurable)
```

### 4. CORS Configuration
```python
# backend/config/settings.py
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',  # Admin
    'http://localhost:5174',  # Cliente
    'https://admin.tudominio.com',
    'https://reservas.tudominio.com',
]
```

## Integración WhatsApp

### Flujos de Notificación

**1. Confirmación de Reserva**
```
Trigger: Cliente crea turno
Template:
  "¡Hola {nombre}!
   Tu turno para {servicio} ha sido confirmado.
   📅 Fecha: {fecha}
   🕐 Hora: {hora}
   👤 Profesional: {profesional}
   📍 {direccion_centro}

   Te enviaremos recordatorios antes del turno."
```

**2. Recordatorio 24h antes**
```
Template:
  "Hola {nombre}, te recordamos tu turno mañana:
   🕐 {hora} - {servicio}
   👤 {profesional}

   Si necesitas cancelar, ingresa a: {link_cancelar}"
```

**3. Recordatorio 2h antes**
```
Template:
  "¡Tu turno es en 2 horas!
   🕐 {hora} - {servicio}
   📍 {direccion_centro}

   ¡Te esperamos!"
```

**4. Cancelación de Turno**
```
Template:
  "Tu turno del {fecha} a las {hora} ha sido cancelado.

   Puedes reservar uno nuevo en: {link_reservar}"
```

## Testing

### Backend Tests
```python
# backend/apps/client_api/tests.py

def test_disponibilidad_sin_conflictos():
    """Slots disponibles se muestran correctamente"""

def test_disponibilidad_con_conflictos():
    """Slots ocupados no se muestran como disponibles"""

def test_reservar_turno_exito():
    """Cliente puede reservar turno disponible"""

def test_reservar_turno_conflicto():
    """Sistema rechaza turno con conflicto"""

def test_cancelar_turno_propio():
    """Cliente puede cancelar su propio turno"""

def test_cancelar_turno_ajeno():
    """Cliente NO puede cancelar turno de otro"""
```

### Frontend Tests
```typescript
// client-app/src/__tests__/

describe('ReservarTurno', () => {
  it('muestra slots disponibles', async () => {})
  it('previene selección de slots ocupados', () => {})
  it('valida datos antes de enviar', () => {})
  it('muestra confirmación después de reservar', () => {})
})
```

## Deployment

### Desarrollo
```bash
docker-compose up -d
# Admin:  http://localhost:5173
# Client: http://localhost:5174
```

### Producción (Ejemplo con Render)

**Admin App**: `https://admin.tucentro.com`
**Client App**: `https://reservas.tucentro.com` o `https://tucentro.com`
**Backend**: `https://api.tucentro.com`

```yaml
# render.yaml
services:
  - type: web
    name: backend
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "gunicorn config.wsgi:application"

  - type: web
    name: admin-frontend
    env: static
    buildCommand: "cd frontend && npm install && npm run build"
    staticPublishPath: frontend/dist

  - type: web
    name: client-frontend
    env: static
    buildCommand: "cd client-app && npm install && npm run build"
    staticPublishPath: client-app/dist
```

## Métricas de Éxito

### KPIs a Monitorear

1. **Adopción**
   - % de turnos reservados online vs teléfono
   - Nuevos clientes registrados por semana

2. **Engagement**
   - Tasa de cancelación
   - Tiempo promedio para reservar
   - Turnos por cliente

3. **Negocio**
   - Reducción de no-shows
   - Incremento en ventas de productos
   - Satisfacción del cliente (ratings)

## Próximos Pasos

1. ✅ Documentar feature (este archivo)
2. ⏳ Implementar notificaciones WhatsApp en admin (prioridad)
3. ⏳ Crear estructura base de `client-app/`
4. ⏳ Desarrollar endpoints de `public_api`
5. ⏳ Desarrollar endpoints de `client_api`
6. ⏳ Frontend cliente - Páginas principales
7. ⏳ Integración WhatsApp en flujo de reserva
8. ⏳ Testing y QA
9. ⏳ Deploy a producción

---

## Apéndice: Comparación de Gateways de Pago (MODO vs MercadoPago)

### Contexto
Este análisis surge del debate sobre reducción de comisiones para el modelo SaaS. La conclusión es usar el **modelo Tienda Nube**: cada centro conecta su propia cuenta de pago (OAuth), los pagos van directo a ellos, y la plataforma solo cobra suscripción mensual.

### Comisiones Comparadas

| Gateway | Débito | Crédito | QR/Transferencia |
|---------|--------|---------|------------------|
| **MercadoPago** | 3.19% - 3.39% | 1.49% - 6.49% | 0.8% |
| **MODO (Payway)** | 0.8% ⭐ | 1.8% ⭐ | 0.8% |

**Ahorro con MODO**: 60-75% menos en comisiones de débito/crédito

**Ejemplo:** Centro vende $500,000/mes
- MP: $17,500 comisiones
- MODO: $7,500 comisiones
- **Ahorro: $10,000/mes** ($120,000/año)

### Facilidad de Integración

| Aspecto | MercadoPago | MODO (Payway) |
|---------|-------------|---------------|
| SDK Python oficial | ✅ Sí | ❌ No (requiere wrapper custom) |
| Documentación | ⭐⭐⭐⭐⭐ Excelente | ⭐⭐⭐ Menos pública |
| OAuth para SaaS | ✅ Bien documentado | ⚠️ Requiere contacto directo |
| Sandbox | ✅ Completo | ⚠️ Limitado |
| Comunidad/Soporte | ✅ Grande | ⚠️ Más pequeña |
| Tiempo desarrollo | 2-3 días | 5-7 días |

### Estrategia Recomendada (Cuando se implemente e-commerce)

**Fase 1: MercadoPago primero**
- Implementación rápida (2-3 días)
- SDK confiable y bien mantenido
- OAuth para modelo SaaS ya probado
- Validación rápida del producto

**Fase 2: Agregar MODO como opción**
- Desarrollo de wrapper custom (1 semana)
- Dar alternativa de menor comisión
- Ideal para centros con alto volumen

**Fase 3: Métodos sin comisión**
- Transferencia bancaria manual (0%)
- Efectivo al retirar (0%)
- CBU/Alias directo del centro

### Arquitectura Multi-Gateway

```python
class CentroEstetica(models.Model):
    # MercadoPago
    mercadopago_conectado = models.BooleanField(default=False)
    mercadopago_access_token = models.CharField(...)

    # Modo/Payway
    modo_conectado = models.BooleanField(default=False)
    modo_api_key = models.CharField(...)

    # Preferencia
    gateway_preferido = models.CharField(
        choices=[
            ('MERCADOPAGO', 'MercadoPago'),
            ('MODO', 'Modo'),
            ('TRANSFERENCIA', 'Transferencia'),
            ('EFECTIVO', 'Efectivo')
        ]
    )
```

### Conclusión
El modelo ideal es ofrecer **múltiples opciones de pago** para que cada centro elija según sus necesidades:
- **MercadoPago**: Facilidad y rapidez
- **MODO**: Ahorro en comisiones (volumen alto)
- **Transferencia/Efectivo**: Sin comisiones

**Importante**: En el modelo SaaS, la plataforma NO maneja el dinero. Cada centro conecta su propia cuenta y recibe los pagos directamente. La plataforma solo cobra suscripción mensual fija ($30-50 USD/mes).

---

**Fecha de creación**: 16 de Noviembre 2025
**Última actualización**: 17 de Noviembre 2025
**Estado**: Planificación
