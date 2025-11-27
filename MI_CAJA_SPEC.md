# Especificación Técnica: Sistema "Mi Caja" para Empleados

**Fecha:** 26 de Noviembre, 2025
**Versión:** 1.0
**Autor:** Claude Code

---

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Contexto y Problema](#contexto-y-problema)
3. [Objetivos](#objetivos)
4. [Alcance](#alcance)
5. [Arquitectura de la Solución](#arquitectura-de-la-solución)
6. [Especificación Backend](#especificación-backend)
7. [Especificación Frontend](#especificación-frontend)
8. [Flujos de Usuario](#flujos-de-usuario)
9. [Seguridad y Permisos](#seguridad-y-permisos)
10. [Plan de Implementación](#plan-de-implementación)
11. [Testing](#testing)

---

## 1. Resumen Ejecutivo

### ¿Qué es "Mi Caja"?

Sistema de punto de venta simplificado que permite a **empleados básicos** registrar transacciones de ingreso (cobros de servicios y ventas de productos) sin acceder al módulo completo de Finanzas que permanece restringido solo a Admin/Manager.

### Problema que Resuelve

**Actual:**
- Empleados no pueden registrar cobros → anotan en papel
- Admin debe cargar manualmente todo al final del día
- Inconsistencias entre turnos completados y dinero cobrado
- Sin trazabilidad de quién cobró qué

**Con Mi Caja:**
- Empleados registran cobros en tiempo real
- Trazabilidad completa (quién, cuándo, cuánto)
- Cierre de caja automático
- Admin supervisa desde Finanzas

---

## 2. Contexto y Problema

### Situación Actual

```
Empleado atiende cliente → Cobra servicio → ¿Dónde registra el pago?

Opciones actuales (todas malas):
❌ 1. Anotar en papel → Admin carga después
❌ 2. Darle permisos de MANAGER → Riesgo de seguridad
❌ 3. Llamar al Admin cada vez → Ineficiente
```

### Flujo Problemático

```
09:00 - Empleado completa turno de Masaje ($5000)
      - Cliente paga en efectivo
      - ¿Dónde se registra?

17:00 - Admin revisa sistema
      - Ve turno "Completado" pero no ve el pago
      - Tiene que preguntar a empleado
      - Carga manualmente la transacción
```

---

## 3. Objetivos

### Objetivos Principales

1. **Autonomía:** Empleados registran sus propios cobros sin depender del admin
2. **Trazabilidad:** Cada transacción registra quién la creó
3. **Seguridad:** Empleados NO acceden a información financiera sensible
4. **Simplicidad:** Interfaz simple tipo punto de venta
5. **Auditoría:** Admin ve TODO desde Finanzas

### Objetivos Secundarios

1. Reducir carga de trabajo del admin
2. Mejorar precisión de datos financieros
3. Detectar discrepancias temprano
4. Facilitar cierre de caja diario

---

## 4. Alcance

### ✅ Incluye (Scope IN)

**Para Empleados Básicos:**
- Registrar cobros de servicios completados
- Registrar ventas de productos
- Ver transacciones propias del día
- Cierre de caja diario (contar efectivo)
- Notificación de turnos pendientes de cobro

**Para Admin/Manager:**
- TODO lo anterior +
- Ver transacciones de todos los empleados
- Acceso completo a módulo Finanzas
- Editar/eliminar transacciones
- Reportes consolidados

### ❌ No Incluye (Scope OUT)

- Sistema de comisiones (futuro)
- Gestión de gastos para empleados
- Emisión de facturas electrónicas
- Integración con POS físico
- Gestión de propinas
- Múltiples cajas por empleado

---

## 5. Arquitectura de la Solución

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND                          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐         ┌──────────────┐        │
│  │  Mi Caja     │         │  Finanzas    │        │
│  │  (Todos)     │         │  (Admin)     │        │
│  ├──────────────┤         ├──────────────┤        │
│  │• Cobrar      │         │• Dashboard   │        │
│  │• Vender      │         │• Todas Trans │        │
│  │• Mis Trans   │         │• Categorías  │        │
│  │• Cierre Caja │         │• Salarios    │        │
│  └──────────────┘         └──────────────┘        │
│         │                        │                 │
└─────────┼────────────────────────┼─────────────────┘
          │                        │
          ▼                        ▼
┌─────────────────────────────────────────────────────┐
│                   BACKEND API                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  /api/mi-caja/                /api/finanzas/       │
│  ├─ cobrar-turno/             ├─ transactions/     │
│  ├─ vender-producto/          ├─ categories/       │
│  ├─ mis-transacciones/        ├─ salarios/         │
│  └─ cierre-caja/              └─ dashboard/        │
│                                                     │
└─────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────┐
│               BASE DE DATOS                         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Transaction (modelo actualizado)                   │
│  ├─ created_by (FK → Usuario) ← NUEVO              │
│  ├─ turno (FK → Turno)                             │
│  ├─ producto (FK → Producto)                       │
│  ├─ amount                                         │
│  ├─ payment_method                                 │
│  └─ ...                                            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Separación de Responsabilidades

| Módulo | Acceso | Responsabilidad |
|--------|--------|-----------------|
| **Mi Caja** | Todos | Registrar ingresos propios |
| **Finanzas** | Admin/Manager | Gestión financiera completa |

---

## 6. Especificación Backend

### 6.1. Actualización del Modelo Transaction

**Archivo:** `backend/apps/finanzas/models.py`

```python
class Transaction(models.Model):
    # ... campos existentes ...

    # NUEVO CAMPO
    created_by = models.ForeignKey(
        'empleados.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones_creadas',
        help_text="Usuario que creó esta transacción"
    )

    # Campos para trazabilidad mejorada
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP desde donde se creó la transacción"
    )

    user_agent = models.TextField(
        blank=True,
        help_text="Navegador/dispositivo usado"
    )
```

### 6.2. Nueva App: mi_caja

**Estructura:**
```
backend/apps/mi_caja/
├── __init__.py
├── models.py          # CierreCaja model
├── views.py           # MiCajaViewSet
├── serializers.py     # Serializers específicos
├── urls.py            # Rutas de la app
└── permissions.py     # IsAuthenticated (todos)
```

### 6.3. Modelo CierreCaja

```python
class CierreCaja(models.Model):
    """
    Registro de cierre de caja diario por empleado
    """
    empleado = models.ForeignKey(
        'empleados.Usuario',
        on_delete=models.CASCADE,
        related_name='cierres_caja'
    )
    sucursal = models.ForeignKey(
        'empleados.Sucursal',
        on_delete=models.CASCADE
    )
    fecha = models.DateField()

    # Conteo del sistema
    total_sistema = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total según transacciones registradas"
    )

    # Conteo físico
    efectivo_contado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Efectivo físico contado"
    )

    # Diferencia
    diferencia = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Diferencia entre sistema y físico"
    )

    # Desglose de métodos de pago (según sistema)
    desglose_metodos = models.JSONField(
        default=dict,
        help_text="{'CASH': 5000, 'DEBIT_CARD': 3000, ...}"
    )

    notas = models.TextField(blank=True)
    cerrado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['empleado', 'fecha']]
        ordering = ['-fecha']
```

### 6.4. Endpoints de Mi Caja

#### POST `/api/mi-caja/cobrar-turno/`

**Request:**
```json
{
  "turno_id": 123,
  "amount": 5000,
  "payment_method": "CASH",
  "notas": "Cliente pagó completo"
}
```

**Validaciones:**
- Turno existe y está COMPLETADO
- Turno no tiene transacción de pago asociada
- Amount coincide con precio del servicio
- Turno pertenece al empleado o empleado es admin

**Response:**
```json
{
  "success": true,
  "transaction": {
    "id": 456,
    "amount": 5000,
    "payment_method": "CASH",
    "created_by": {
      "id": 2,
      "name": "Juan Pérez"
    },
    "turno": {
      "id": 123,
      "cliente": "María González",
      "servicio": "Masaje Relajante"
    },
    "created_at": "2025-11-27T10:30:00Z"
  }
}
```

#### POST `/api/mi-caja/vender-producto/`

**Request:**
```json
{
  "producto_id": 10,
  "cantidad": 2,
  "cliente_id": 5,
  "payment_method": "DEBIT_CARD",
  "descuento_porcentaje": 10
}
```

**Validaciones:**
- Producto existe y está activo
- Hay stock suficiente
- Cliente existe
- Descuento <= 100%

**Lógica:**
1. Calcular monto total (precio × cantidad - descuento)
2. Reducir stock del producto
3. Crear transacción de tipo INCOME_PRODUCT
4. Registrar created_by = usuario actual
5. Crear MovimientoInventario

#### GET `/api/mi-caja/mis-transacciones/`

**Query Params:**
- `fecha`: Filtrar por fecha (default: hoy)
- `payment_method`: Filtrar por método de pago

**Response:**
```json
{
  "fecha": "2025-11-27",
  "empleado": {
    "id": 2,
    "nombre": "Juan Pérez"
  },
  "resumen": {
    "total": 15000,
    "cantidad_transacciones": 5,
    "por_metodo": {
      "CASH": 8000,
      "DEBIT_CARD": 5000,
      "CREDIT_CARD": 2000
    }
  },
  "transacciones": [
    {
      "id": 456,
      "tipo": "INCOME_SERVICE",
      "amount": 5000,
      "payment_method": "CASH",
      "cliente": "María González",
      "concepto": "Masaje Relajante",
      "hora": "10:30"
    },
    // ...
  ]
}
```

#### POST `/api/mi-caja/cierre-caja/`

**Request:**
```json
{
  "fecha": "2025-11-27",
  "efectivo_contado": 7800,
  "notas": "Faltaron $200 en efectivo"
}
```

**Lógica:**
1. Calcular total_sistema (sumar transacciones del día del empleado)
2. Calcular desglose_metodos
3. Calcular diferencia (efectivo_contado - efectivo_sistema)
4. Crear registro CierreCaja
5. Notificar a admin si |diferencia| > $500

#### GET `/api/mi-caja/turnos-pendientes-cobro/`

**Response:**
```json
{
  "count": 3,
  "turnos": [
    {
      "id": 124,
      "cliente": "Pedro López",
      "servicio": "Limpieza Facial",
      "monto": 3000,
      "hora": "14:00",
      "estado_pago": "PENDIENTE"
    },
    // ...
  ]
}
```

### 6.5. Permisos

**Nuevo archivo:** `backend/apps/mi_caja/permissions.py`

```python
from rest_framework.permissions import BasePermission

class CanAccessMiCaja(BasePermission):
    """
    Todos los usuarios autenticados pueden acceder a Mi Caja
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

class CanViewTransaction(BasePermission):
    """
    Empleado solo ve sus propias transacciones
    Admin/Manager ve todas
    """
    def has_object_permission(self, request, view, obj):
        user = request.user

        # Admin/Manager ven todo
        if user.rol in ['ADMIN', 'MANAGER']:
            return True

        # Empleado solo ve las suyas
        return obj.created_by == user
```

---

## 7. Especificación Frontend

### 7.1. Nueva Ruta y Navegación

**Archivo:** `frontend/src/App.tsx`

```typescript
// Agregar ruta
<Route path="/mi-caja" element={<MiCajaPage />} />
```

**Archivo:** `frontend/src/components/layout/Sidebar.tsx`

```typescript
// Agregar item de menú (visible para TODOS)
{
  icon: CashIcon,
  label: 'Mi Caja',
  path: '/mi-caja',
  roles: ['ADMIN', 'MANAGER', 'EMPLEADO']  // Todos
}
```

### 7.2. Estructura de Componentes

```
frontend/src/
├── pages/
│   └── MiCajaPage.tsx                    # Página principal
├── components/
│   └── mi-caja/
│       ├── CobrarTurnoModal.tsx          # Modal para cobrar servicio
│       ├── VenderProductoModal.tsx       # Modal para vender producto
│       ├── MisTransaccionesTable.tsx     # Tabla de transacciones
│       ├── ResumenDiario.tsx             # Resumen del día
│       ├── CierreCajaModal.tsx           # Modal cierre de caja
│       └── TurnosPendientesAlert.tsx     # Alerta de pendientes
├── services/
│   └── miCajaService.ts                  # API calls
└── types/
    └── miCaja.ts                         # Tipos TypeScript
```

### 7.3. Interfaz Principal: MiCajaPage

**Layout:**

```
┌────────────────────────────────────────────────────┐
│  Mi Caja                            [Cerrar Caja]  │
├────────────────────────────────────────────────────┤
│                                                    │
│  ⚠️ Tienes 3 turnos completados sin cobrar        │
│     [Ver Turnos Pendientes]                        │
│                                                    │
├────────────────────────────────────────────────────┤
│  Resumen del Día - 27/Nov/2025                    │
│  ┌──────────────┐  ┌──────────────┐               │
│  │ Total        │  │ Transacciones│               │
│  │ $15,000      │  │ 8            │               │
│  └──────────────┘  └──────────────┘               │
│                                                    │
│  Por Método de Pago:                              │
│  🟢 Efectivo       $8,000  (53%)                  │
│  🔵 Tarjeta Débito $5,000  (33%)                  │
│  🟣 Tarjeta Créd.  $2,000  (14%)                  │
│                                                    │
├────────────────────────────────────────────────────┤
│  Acciones Rápidas                                 │
│  [💰 Cobrar Servicio]  [🛍️ Vender Producto]      │
│                                                    │
├────────────────────────────────────────────────────┤
│  Mis Transacciones de Hoy                         │
│  ┌────────────────────────────────────────────┐   │
│  │ Hora  Cliente      Concepto    Monto  Pago│   │
│  ├────────────────────────────────────────────┤   │
│  │ 10:30 María G.    Masaje      $5000  EFE │   │
│  │ 11:15 Pedro L.    Facial      $3000  T.D │   │
│  │ 14:00 Ana M.      Crema Vit.  $2500  EFE │   │
│  └────────────────────────────────────────────┘   │
│                                                    │
└────────────────────────────────────────────────────┘
```

### 7.4. Modal: Cobrar Servicio

**CobrarTurnoModal.tsx:**

```
┌────────────────────────────────────────┐
│  Cobrar Servicio                   [X] │
├────────────────────────────────────────┤
│                                        │
│  Turno #124                           │
│  Cliente: Pedro López                 │
│  Servicio: Limpieza Facial            │
│  Fecha: 27/11/2025 14:00             │
│                                        │
│  ┌────────────────────────────────┐   │
│  │ Monto a Cobrar                 │   │
│  │ $3,000.00                      │   │
│  └────────────────────────────────┘   │
│                                        │
│  ┌────────────────────────────────┐   │
│  │ Método de Pago                 │   │
│  │ [v] Efectivo                   │   │
│  │     Tarjeta de Débito          │   │
│  │     Tarjeta de Crédito         │   │
│  │     MercadoPago                │   │
│  └────────────────────────────────┘   │
│                                        │
│  Notas (opcional):                    │
│  ┌────────────────────────────────┐   │
│  │                                │   │
│  └────────────────────────────────┘   │
│                                        │
│       [Cancelar]  [Cobrar] ✓          │
└────────────────────────────────────────┘
```

### 7.5. Modal: Vender Producto

**VenderProductoModal.tsx:**

```
┌────────────────────────────────────────┐
│  Vender Producto                   [X] │
├────────────────────────────────────────┤
│                                        │
│  Producto:                            │
│  [Buscar producto...        ] 🔍      │
│  ┌────────────────────────────────┐   │
│  │ ✓ Crema Vitamina C             │   │
│  │   Stock: 25 unidades           │   │
│  │   Precio: $2,500               │   │
│  └────────────────────────────────┘   │
│                                        │
│  Cliente:                             │
│  [Buscar cliente...         ] 🔍      │
│                                        │
│  Cantidad:                            │
│  [-]  [  2  ]  [+]                    │
│                                        │
│  Descuento (%):                       │
│  [  0  ]                              │
│                                        │
│  ────────────────────────────────     │
│  Subtotal:        $5,000              │
│  Descuento:       $0                  │
│  Total a Cobrar:  $5,000              │
│  ────────────────────────────────     │
│                                        │
│  Método de Pago:                      │
│  (•) Efectivo  ( ) Débito  ( ) Créd.  │
│                                        │
│       [Cancelar]  [Vender] ✓          │
└────────────────────────────────────────┘
```

### 7.6. Modal: Cierre de Caja

**CierreCajaModal.tsx:**

```
┌────────────────────────────────────────┐
│  Cierre de Caja - 27/11/2025       [X] │
├────────────────────────────────────────┤
│                                        │
│  Según el Sistema:                    │
│  ┌────────────────────────────────┐   │
│  │ Total en Efectivo:   $8,000    │   │
│  │ Tarjeta Débito:      $5,000    │   │
│  │ Tarjeta Crédito:     $2,000    │   │
│  │ ──────────────────────────     │   │
│  │ TOTAL SISTEMA:      $15,000    │   │
│  └────────────────────────────────┘   │
│                                        │
│  Conteo Físico:                       │
│  ┌────────────────────────────────┐   │
│  │ Efectivo Contado                │   │
│  │ $[  7,800  ]                   │   │
│  └────────────────────────────────┘   │
│                                        │
│  ⚠️ Diferencia: -$200                 │
│     (Falta efectivo)                  │
│                                        │
│  Notas:                               │
│  ┌────────────────────────────────┐   │
│  │ Cliente devolvió $200 porque   │   │
│  │ no tenía cambio                │   │
│  └────────────────────────────────┘   │
│                                        │
│    [Cancelar]  [Registrar Cierre]     │
└────────────────────────────────────────┘
```

### 7.7. TypeScript Types

**Archivo:** `frontend/src/types/miCaja.ts`

```typescript
export interface TransaccionMiCaja {
  id: number
  tipo: 'INCOME_SERVICE' | 'INCOME_PRODUCT'
  amount: number
  payment_method: PaymentMethod
  created_by: {
    id: number
    nombre: string
  }
  cliente: {
    id: number
    nombre: string
  }
  concepto: string
  turno?: number
  producto?: number
  created_at: string
}

export interface ResumenDiario {
  fecha: string
  total: number
  cantidad_transacciones: number
  por_metodo: {
    [key in PaymentMethod]: number
  }
}

export interface CierreCaja {
  fecha: string
  total_sistema: number
  efectivo_contado: number
  diferencia: number
  desglose_metodos: {
    [key in PaymentMethod]: number
  }
  notas: string
}

export interface TurnoPendienteCobro {
  id: number
  cliente: string
  servicio: string
  monto: number
  hora: string
  estado_pago: 'PENDIENTE' | 'CON_SENA'
}
```

---

## 8. Flujos de Usuario

### 8.1. Flujo: Empleado Cobra un Servicio

```
1. Empleado completa un turno (marca como COMPLETADO)

2. Sistema muestra notificación:
   "Turno completado. ¿Deseas registrar el cobro?"
   [Ahora]  [Más Tarde]

3. Si elige "Ahora":
   → Se abre CobrarTurnoModal pre-cargado

4. Empleado selecciona método de pago

5. Empleado hace clic en "Cobrar"

6. Sistema:
   - Crea transacción con created_by = empleado
   - Marca turno como PAGADO
   - Actualiza balance del día

7. Muestra confirmación:
   "✓ Cobro registrado: $5,000 en Efectivo"
```

### 8.2. Flujo: Empleado Vende un Producto

```
1. Empleado va a Mi Caja

2. Clic en "Vender Producto"

3. Busca producto (autocomplete)

4. Selecciona cliente (autocomplete)

5. Indica cantidad y descuento (opcional)

6. Sistema calcula total automáticamente

7. Selecciona método de pago

8. Clic en "Vender"

9. Sistema:
   - Reduce stock del producto
   - Crea MovimientoInventario (SALE)
   - Crea transacción INCOME_PRODUCT
   - Registra created_by = empleado

10. Muestra confirmación:
    "✓ Venta registrada: 2x Crema Vitamina C - $5,000"
```

### 8.3. Flujo: Cierre de Caja

```
1. Al final del día, empleado va a Mi Caja

2. Clic en "Cerrar Caja"

3. Sistema muestra:
   - Total según sistema (automático)
   - Desglose por método de pago

4. Empleado cuenta efectivo físico

5. Ingresa monto contado

6. Sistema calcula diferencia automáticamente

7. Si diferencia != 0:
   → Muestra alerta
   → Pide notas explicativas

8. Empleado ingresa notas y confirma

9. Sistema:
   - Crea registro CierreCaja
   - Si |diferencia| > $500 → Notifica a admin

10. Muestra resumen imprimible
```

### 8.4. Flujo: Admin Supervisa Todo

```
1. Admin va a Finanzas (módulo completo)

2. Ve dashboard con:
   - Total del día (todos los empleados)
   - Transacciones por empleado
   - Cierres de caja pendientes de revisión

3. Puede filtrar transacciones:
   - Por empleado que las creó
   - Por método de pago
   - Por rango de fechas

4. Puede editar/eliminar cualquier transacción

5. Puede exportar reportes
```

---

## 9. Seguridad y Permisos

### 9.1. Matriz de Permisos

| Acción | Empleado | Manager | Admin |
|--------|----------|---------|-------|
| **Mi Caja** |
| Acceder a Mi Caja | ✅ | ✅ | ✅ |
| Cobrar turno propio | ✅ | ✅ | ✅ |
| Cobrar turno de otro | ❌ | ✅ | ✅ |
| Vender producto | ✅ | ✅ | ✅ |
| Ver transacciones propias | ✅ | ✅ | ✅ |
| Ver transacciones de otros | ❌ | ✅ | ✅ |
| Hacer cierre de caja | ✅ | ✅ | ✅ |
| **Finanzas** |
| Acceder a Finanzas | ❌ | ✅ | ✅ |
| Ver dashboard completo | ❌ | ✅ | ✅ |
| Crear gastos | ❌ | ✅ | ✅ |
| Editar transacciones | ❌ | ✅ | ✅ |
| Eliminar transacciones | ❌ | ❌ | ✅ |
| Ver salarios | ❌ | ✅ | ✅ |

### 9.2. Validaciones de Seguridad

**Backend:**
```python
# Ejemplo: Validar que empleado solo cobra sus turnos
def cobrar_turno(self, request):
    turno = Turno.objects.get(id=turno_id)

    # Validar que el turno pertenece al empleado
    if request.user.rol == 'EMPLEADO':
        if turno.profesional != request.user:
            raise PermissionDenied(
                "Solo puedes cobrar tus propios turnos"
            )

    # Admin/Manager pueden cobrar cualquier turno
    # ...
```

### 9.3. Auditoría

**Cada transacción registra:**
- `created_by`: Quién la creó
- `created_at`: Cuándo se creó
- `ip_address`: Desde dónde
- `user_agent`: Qué dispositivo

**Log de auditoría:**
```
[2025-11-27 10:30:15] Juan Pérez (ID: 2) creó transacción #456
  Tipo: INCOME_SERVICE
  Monto: $5000
  Método: CASH
  IP: 192.168.1.10
  Dispositivo: Chrome/Windows
```

---

## 10. Plan de Implementación

### Fase 1: Backend (1.5-2 horas)

1. **Actualizar modelo Transaction** (15 min)
   - Agregar campo `created_by`
   - Agregar campos de auditoría
   - Crear migración

2. **Crear app mi_caja** (30 min)
   - Crear modelo CierreCaja
   - Crear serializers
   - Crear permissions

3. **Implementar endpoints** (45 min)
   - `cobrar-turno/`
   - `vender-producto/`
   - `mis-transacciones/`
   - `cierre-caja/`
   - `turnos-pendientes-cobro/`

4. **Testing backend** (30 min)
   - Unit tests de permisos
   - Integration tests de endpoints

### Fase 2: Frontend (2-2.5 horas)

1. **Crear servicios API** (20 min)
   - `miCajaService.ts`
   - Tipos TypeScript

2. **Crear componentes base** (40 min)
   - ResumenDiario
   - MisTransaccionesTable
   - TurnosPendientesAlert

3. **Crear modales** (60 min)
   - CobrarTurnoModal
   - VenderProductoModal
   - CierreCajaModal

4. **Crear página principal** (30 min)
   - MiCajaPage
   - Integrar componentes
   - Agregar navegación

### Fase 3: Integración y Testing (1 hora)

1. **Pruebas de integración** (30 min)
   - Flujo completo empleado
   - Flujo completo admin
   - Casos edge

2. **Ajustes y pulido** (30 min)
   - UX/UI final
   - Mensajes de error
   - Loading states

### Timeline Total: **3.5-4 horas**

---

## 11. Testing

### 11.1. Test Cases Backend

**test_cobrar_turno.py:**
```python
def test_empleado_puede_cobrar_su_turno():
    """Empleado puede cobrar turno que atendió"""

def test_empleado_no_puede_cobrar_turno_de_otro():
    """Empleado NO puede cobrar turno de otro empleado"""

def test_admin_puede_cobrar_cualquier_turno():
    """Admin puede cobrar cualquier turno"""

def test_no_se_puede_cobrar_turno_dos_veces():
    """No se puede registrar pago duplicado"""

def test_created_by_se_registra_correctamente():
    """Campo created_by se llena automáticamente"""
```

**test_vender_producto.py:**
```python
def test_venta_reduce_stock():
    """Venta de producto reduce stock correctamente"""

def test_venta_sin_stock_falla():
    """No se puede vender producto sin stock"""

def test_venta_crea_transaccion():
    """Venta crea transacción INCOME_PRODUCT"""
```

**test_cierre_caja.py:**
```python
def test_cierre_caja_calcula_diferencia():
    """Cierre de caja calcula diferencia correctamente"""

def test_no_se_puede_cerrar_caja_dos_veces():
    """No se puede cerrar caja dos veces en mismo día"""
```

### 11.2. Test Cases Frontend

**MiCajaPage.test.tsx:**
```typescript
test('Muestra resumen del día correctamente', () => {})

test('Muestra alerta de turnos pendientes', () => {})

test('Botón Cerrar Caja deshabilitado si ya cerró', () => {})
```

**CobrarTurnoModal.test.tsx:**
```typescript
test('Pre-carga datos del turno', () => {})

test('Valida método de pago requerido', () => {})

test('Muestra confirmación después de cobrar', () => {})
```

### 11.3. Escenarios de Prueba Manual

1. **Empleado Básico - Día Completo:**
   - Login como empleado
   - Completar 3 turnos
   - Cobrar cada uno con diferentes métodos
   - Vender 2 productos
   - Hacer cierre de caja
   - Verificar que solo ve sus transacciones

2. **Admin - Supervisión:**
   - Login como admin
   - Ir a Finanzas
   - Ver transacciones de todos los empleados
   - Filtrar por empleado específico
   - Editar una transacción
   - Exportar reporte

3. **Casos Edge:**
   - Intentar cobrar turno ya cobrado
   - Intentar vender producto sin stock
   - Hacer cierre con diferencia grande
   - Verificar notificación a admin

---

## 12. Migraciones Necesarias

### Migración 1: Actualizar Transaction

**Archivo:** `backend/apps/finanzas/migrations/000X_add_created_by.py`

```python
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('finanzas', '000X_previous_migration'),
        ('empleados', '0003_usuario_horario_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='transacciones_creadas',
                to='empleados.usuario'
            ),
        ),
        migrations.AddField(
            model_name='transaction',
            name='ip_address',
            field=models.GenericIPAddressField(
                blank=True,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='transaction',
            name='user_agent',
            field=models.TextField(blank=True),
        ),
    ]
```

### Migración 2: Crear CierreCaja

**Archivo:** `backend/apps/mi_caja/migrations/0001_initial.py`

```python
# Migración auto-generada al crear el modelo
```

---

## 13. Consideraciones Futuras

### Features Potenciales (No en Scope Actual)

1. **Sistema de Comisiones:**
   - Empleados ven sus comisiones en Mi Caja
   - Cálculo automático por transacción

2. **Propinas:**
   - Campo adicional para registrar propinas
   - Reporte de propinas por empleado

3. **Múltiples Cajas:**
   - Un empleado puede manejar múltiples cajas
   - Útil para sucursales grandes

4. **Integración POS Físico:**
   - Conectar con terminal física
   - Sincronización automática

5. **Facturas Electrónicas:**
   - Generar factura AFIP directamente
   - Adjuntar PDF a transacción

6. **App Móvil:**
   - Version mobile-first de Mi Caja
   - Cobrar desde tablet/celular

---

## 14. Resumen de Archivos a Crear/Modificar

### Backend - Nuevos Archivos

```
backend/apps/mi_caja/
├── __init__.py
├── admin.py
├── apps.py
├── models.py              # CierreCaja
├── serializers.py         # CierreCajaSerializer, TransaccionMiCajaSerializer
├── views.py               # MiCajaViewSet
├── urls.py
├── permissions.py
├── migrations/
│   └── 0001_initial.py
└── tests/
    ├── test_cobrar_turno.py
    ├── test_vender_producto.py
    └── test_cierre_caja.py
```

### Backend - Archivos Modificados

```
backend/apps/finanzas/models.py           # Agregar created_by a Transaction
backend/apps/finanzas/serializers.py      # Incluir created_by en serializers
backend/apps/finanzas/migrations/         # Nueva migración
backend/config/urls.py                    # Agregar ruta /api/mi-caja/
```

### Frontend - Nuevos Archivos

```
frontend/src/
├── pages/
│   └── MiCajaPage.tsx
├── components/mi-caja/
│   ├── CobrarTurnoModal.tsx
│   ├── VenderProductoModal.tsx
│   ├── MisTransaccionesTable.tsx
│   ├── ResumenDiario.tsx
│   ├── CierreCajaModal.tsx
│   └── TurnosPendientesAlert.tsx
├── services/
│   └── miCajaService.ts
└── types/
    └── miCaja.ts
```

### Frontend - Archivos Modificados

```
frontend/src/App.tsx                     # Agregar ruta
frontend/src/components/layout/Sidebar.tsx  # Agregar item menú
frontend/src/types/models.ts             # Actualizar Transaction type
```

---

## 15. Checklist de Implementación

### Backend
- [ ] Actualizar modelo Transaction con created_by
- [ ] Crear migración para Transaction
- [ ] Crear app mi_caja
- [ ] Crear modelo CierreCaja
- [ ] Crear serializers
- [ ] Crear permissions
- [ ] Implementar endpoint cobrar-turno
- [ ] Implementar endpoint vender-producto
- [ ] Implementar endpoint mis-transacciones
- [ ] Implementar endpoint cierre-caja
- [ ] Implementar endpoint turnos-pendientes
- [ ] Crear URLs de mi_caja
- [ ] Agregar ruta en config/urls.py
- [ ] Escribir tests unitarios
- [ ] Escribir tests de integración
- [ ] Correr migrations

### Frontend
- [ ] Crear tipos TypeScript
- [ ] Crear miCajaService.ts
- [ ] Crear ResumenDiario component
- [ ] Crear MisTransaccionesTable component
- [ ] Crear TurnosPendientesAlert component
- [ ] Crear CobrarTurnoModal component
- [ ] Crear VenderProductoModal component
- [ ] Crear CierreCajaModal component
- [ ] Crear MiCajaPage
- [ ] Agregar ruta en App.tsx
- [ ] Agregar item en Sidebar
- [ ] Actualizar Transaction type
- [ ] Escribir tests de componentes
- [ ] Testing E2E

### Testing & Deployment
- [ ] Probar flujo empleado completo
- [ ] Probar flujo admin completo
- [ ] Probar casos edge
- [ ] Revisar permisos
- [ ] Revisar auditoría
- [ ] Performance testing
- [ ] Deploy a staging
- [ ] User acceptance testing
- [ ] Deploy a producción

---

## 16. Preguntas Frecuentes

**Q: ¿Qué pasa con las transacciones existentes que no tienen created_by?**
A: Se quedan con `created_by = null`. Son transacciones históricas antes del sistema.

**Q: ¿Puede un empleado eliminar sus propias transacciones?**
A: NO. Solo Admin puede eliminar transacciones.

**Q: ¿Se pueden editar transacciones en Mi Caja?**
A: NO. Empleados solo pueden crear. Admin edita desde Finanzas.

**Q: ¿Qué pasa si un empleado cierra caja con diferencia?**
A: Se registra la diferencia y se notifica al admin si es > $500.

**Q: ¿Se puede re-abrir un cierre de caja?**
A: Solo Admin puede invalidar un cierre de caja desde Finanzas.

---

## 17. Métricas de Éxito

Después de implementar, medir:

1. **Tiempo de registro:**
   - ¿Cuánto tarda un empleado en registrar un cobro?
   - Meta: < 30 segundos

2. **Precisión:**
   - ¿Cuántas diferencias en cierre de caja?
   - Meta: < 5% de diferencia promedio

3. **Adopción:**
   - ¿Qué % de turnos se cobran en tiempo real?
   - Meta: > 90%

4. **Satisfacción:**
   - Encuesta a empleados sobre facilidad de uso
   - Meta: > 4/5 estrellas

---

**Fin del Documento**
