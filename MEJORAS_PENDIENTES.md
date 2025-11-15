# Mejoras Pendientes - Plataforma de Gestión Estética

## 🔴 PRIORIDAD ALTA: Sistema de Turnos - Gestión y Visualización

### Problemas Actuales Identificados
**Fecha identificación**: 2025-01-14

1. **❌ Turnos pasados no se filtran automáticamente**
   - La lista muestra TODOS los turnos (pasados, presentes y futuros) mezclados
   - Dificulta ver la agenda del día actual
   - No hay distinción visual entre turnos pasados y futuros
   - **Impacto**: Confusión, pérdida de tiempo buscando turnos relevantes

2. **❌ Falta gestión rápida de estados**
   - Para marcar un turno como "Completado" hay que abrir modal de edición
   - No hay botones de acción rápida (Completar, Cancelar, No-Show)
   - Proceso tedioso para cambios de estado frecuentes
   - **Impacto**: Flujo de trabajo lento, frustración del usuario

3. **❌ Vista poco práctica para uso diario**
   - Solo hay una tabla larga sin organización
   - No hay vista de "Agenda del día"
   - Falta contexto visual de la jornada
   - No hay filtros rápidos por fecha (Hoy, Mañana, Esta semana)
   - **Impacto**: Mala experiencia de usuario, sistema poco práctico

4. **❌ No hay gestión de turnos pasados**
   - Los turnos viejos permanecen en la lista principal indefinidamente
   - No hay separación entre turnos activos e históricos
   - **Impacto**: Performance degradada con el tiempo, lista interminable

### Soluciones Propuestas - Orden de Implementación

#### ✅ Fase 1: Vista con Tabs y Filtros (30 min) - PRIORITARIO
**Estado**: ✅ COMPLETADO (2025-01-14)
**Complejidad**: Baja
**Impacto**: Alto

**Descripción**:
- Agregar sistema de **tabs** en TurnosPage:
  - 📅 **"Hoy"** - Turnos del día actual (default)
  - 🔜 **"Próximos"** - Turnos futuros (próximos 7 días)
  - 📊 **"Historial"** - Turnos pasados (últimos 30 días)
- Cambiar comportamiento por defecto: mostrar solo "Hoy" al cargar
- Ordenar turnos por fecha/hora ascendente
- Filtro rápido por profesional en cada tab

**Implementación**:
```typescript
// frontend/src/pages/TurnosPage.tsx
const [activeTab, setActiveTab] = useState<'hoy' | 'proximos' | 'historial'>('hoy')

useEffect(() => {
  const today = new Date().toISOString().split('T')[0]
  const params = {
    fecha_desde: activeTab === 'hoy' ? `${today}T00:00:00` : undefined,
    fecha_hasta: activeTab === 'hoy' ? `${today}T23:59:59` : undefined,
    // ... otros filtros según tab
  }
  fetchTurnos(params)
}, [activeTab])
```

**Archivos a modificar**:
- `frontend/src/pages/TurnosPage.tsx` - Agregar tabs y lógica de filtrado

---

#### ✅ Fase 2: Acciones Rápidas de Estado (20 min) - PRIORITARIO
**Estado**: ✅ COMPLETADO (2025-01-14)
**Complejidad**: Baja
**Impacto**: Muy Alto

**Descripción**:
- Agregar botones de acción rápida en cada fila de la tabla:
  - ✅ **"Completar"** - Cambia a COMPLETADO
  - ❌ **"Cancelar"** - Cambia a CANCELADO
  - 🚫 **"No-Show"** - Cambia a NO_SHOW
- Solo mostrar acciones relevantes según estado actual
- Confirmación simple antes de cambiar estado (sin modal grande)
- Usar el endpoint `cambiar_estado` del backend

**Implementación**:
```typescript
// frontend/src/components/turnos/TurnosList.tsx
const QuickActions = ({ turno }) => {
  if (turno.estado === 'COMPLETADO' || turno.estado === 'CANCELADO') {
    return <Badge>Finalizado</Badge>
  }

  return (
    <div className="flex gap-1">
      <Button size="small" onClick={() => onQuickAction(turno.id, 'COMPLETADO')}>
        ✅ Completar
      </Button>
      <Button size="small" variant="danger" onClick={() => onQuickAction(turno.id, 'CANCELADO')}>
        ❌ Cancelar
      </Button>
      <Button size="small" variant="secondary" onClick={() => onQuickAction(turno.id, 'NO_SHOW')}>
        🚫 No-Show
      </Button>
    </div>
  )
}
```

**Archivos a modificar**:
- `frontend/src/components/turnos/TurnosList.tsx` - Agregar botones de acción rápida
- `frontend/src/pages/TurnosPage.tsx` - Manejar cambios de estado

---

#### ✅ Fase 3: Validación Inteligente de Horarios (40 min)
**Estado**: Pendiente
**Complejidad**: Media
**Impacto**: Alto

**Descripción**:
- Mejorar `isTimeSlotOccupied()` para considerar duración del servicio
- Calcular automáticamente qué slots ocupará el servicio seleccionado
- Deshabilitar todos los slots que interfieran con turnos existentes
- Mostrar mensaje claro si no hay disponibilidad ese día

**Implementación**:
```typescript
const isTimeSlotAvailable = (time: string, serviceDuration: number) => {
  const slotsNeeded = Math.ceil(serviceDuration / 30)

  for (let i = 0; i < slotsNeeded; i++) {
    const slotTime = addMinutes(time, i * 30)
    if (isSlotOccupied(slotTime)) return false
  }

  return true
}
```

**Archivos a modificar**:
- `frontend/src/components/turnos/TurnoForm.tsx` - Mejorar lógica de validación

---

#### 🔄 Fase 4: Vista de Agenda del Día (Opcional - 1-2 horas)
**Estado**: Pendiente
**Complejidad**: Media-Alta
**Impacto**: Muy Alto

**Descripción**:
- Vista alternativa tipo "agenda" con bloques de tiempo
- Timeline visual de 8am a 7pm
- Turnos mostrados como bloques en su horario
- Espacios en blanco = horarios disponibles
- Código de colores por profesional o tipo de servicio

**Librerías recomendadas**:
- [react-big-calendar](https://github.com/jquense/react-big-calendar)
- [FullCalendar](https://fullcalendar.io/)
- Custom con CSS Grid

---

### Recomendación de Implementación
1. **Fase 1** (30 min) ← EMPEZAR AQUÍ
2. **Fase 2** (20 min) ← SEGUIR ACÁ
3. **Fase 3** (40 min)
4. **Fase 4** (Opcional, más adelante)

**Total tiempo Fases 1-3**: ~90 minutos
**Impacto**: Sistema de turnos profesional y funcional

---

## Sistema de Turnos - Disponibilidad de Horarios

### Problema Actual
1. **Slots de tiempo no inteligentes**: El sistema solo verifica si el horario exacto está ocupado, pero no considera que un servicio de 60 minutos ocupa múltiples slots de 30 minutos.
   - Ejemplo: Si hay un turno a las 10:00 para un servicio de 60 min, actualmente el sistema permite agendar otro turno a las 10:30, causando superposición.

2. **Profesional sin asignar**: Si no se selecciona un profesional, el sistema permite agendar infinitos turnos en el mismo horario (aunque el backend previene esto con validación).

3. **UX mejorable**: No es visualmente claro qué horarios están disponibles considerando la duración del servicio seleccionado.

### Soluciones Propuestas

#### Opción A: Mejorar el Selector de Horarios (Visual Grid)
**Complejidad**: Media
**Impacto UX**: Alto
**Descripción**:
- Crear una grilla visual de horarios estilo calendario
- Cada slot de 30 minutos se muestra como un bloque con estado:
  - 🟢 Verde: Disponible
  - 🔴 Rojo: Ocupado
  - 🟡 Amarillo: Parcialmente ocupado
- Al seleccionar un servicio, resaltar automáticamente los slots que ocuparía
- Ejemplo: Servicio de 90 min a las 10:00 → resalta 10:00, 10:30 y 11:00

**Implementación**:
```
frontend/src/components/turnos/TimeSlotGrid.tsx
- Grid con slots de 30 min
- Cálculo inteligente de disponibilidad
- Indicadores visuales de estado
```

#### Opción B: Validación Inteligente en Tiempo Real
**Complejidad**: Baja
**Impacto UX**: Medio
**Descripción**:
- Mejorar `isTimeSlotOccupied()` para considerar duración del servicio
- Calcular automáticamente qué slots ocupará el servicio seleccionado
- Deshabilitar todos los slots que interfieran con turnos existentes
- Mostrar mensaje claro si no hay disponibilidad ese día

**Implementación**:
```typescript
const isTimeSlotAvailable = (time: string, serviceDuration: number) => {
  // Calcular todos los slots que ocuparía el servicio
  const slotsNeeded = Math.ceil(serviceDuration / 30)

  // Verificar que todos los slots estén libres
  for (let i = 0; i < slotsNeeded; i++) {
    const slotTime = addMinutes(time, i * 30)
    if (isSlotOccupied(slotTime)) return false
  }

  return true
}
```

**Archivos a modificar**:
- `frontend/src/components/turnos/TurnoForm.tsx`
- Mejorar lógica de `isTimeSlotOccupied()`

#### Opción C: Vista de Calendario Semanal (Más Avanzado)
**Complejidad**: Alta
**Impacto UX**: Muy Alto
**Descripción**:
- Implementar vista de calendario estilo Google Calendar
- Columnas por profesional (o por día)
- Drag & drop para crear/mover turnos
- Vista clara de todos los turnos del día/semana
- Zoom in/out de horarios

**Librerías recomendadas**:
- [FullCalendar](https://fullcalendar.io/) - Calendario completo con drag & drop
- [React Big Calendar](https://github.com/jquense/react-big-calendar) - Más liviano, inspirado en Google Calendar
- [DayPilot Lite](https://javascript.daypilot.org/lite/) - Gratis para uso comercial

**Implementación**:
```
frontend/src/components/turnos/CalendarView.tsx
frontend/src/pages/CalendarioPage.tsx (nueva página)
```

### Recomendación
**Para MVP**: Implementar **Opción B** (Validación Inteligente) por ser rápida y efectiva.
**Para producción**: Migrar a **Opción C** (Vista de Calendario) para una experiencia profesional completa.

---

## Otras Mejoras Identificadas

### Funcionalidades Futuras

#### 1. Notificaciones WhatsApp
- **Estado**: Por implementar (Fase 2)
- **Descripción**: Integración con WhatsApp Business API o Twilio
- **Casos de uso**:
  - Confirmación inmediata al crear turno
  - Recordatorio 24h antes
  - Recordatorio 2h antes
  - Notificación de cancelación/modificación

#### 2. Dashboard de Analytics
- **Estado**: Por implementar (Fase 2)
- **Métricas clave**:
  - Tasa de no-shows por servicio/profesional
  - Servicios más populares
  - Ingresos por período
  - Ocupación por día/hora
  - Clientes recurrentes vs nuevos

#### 3. Sistema de Inventario
- **Estado**: Modelo creado, falta implementar UI
- **Funcionalidades**:
  - Alertas de stock bajo
  - Gestión de proveedores
  - Movimientos de inventario
  - Costo por servicio (productos utilizados)

#### 4. Sistema Financiero Completo
- **Estado**: Modelo creado, falta implementar UI
- **Acceso**: Solo Admin/Dueño
- **Funcionalidades**:
  - Registro de ingresos/egresos
  - Categorización de gastos
  - Reportes de flujo de caja
  - Proyecciones financieras
  - Exportación a PDF/Excel

#### 5. Gestión de Empleados y Comisiones
- **Estado**: Modelo creado, falta implementar UI
- **Funcionalidades**:
  - Perfiles de empleados
  - Asignación de horarios
  - Cálculo automático de comisiones
  - Metas y objetivos
  - Reportes de desempeño

#### 6. Multi-sucursal Avanzado
- **Estado**: Base implementada
- **Mejoras pendientes**:
  - Transferencias de stock entre sucursales
  - Reportes consolidados
  - Gestión de permisos por sucursal
  - Dashboard comparativo entre sucursales

---

## Mejoras de UX/UI Generales

### Prioridad Alta
- [ ] Confirmaciones antes de eliminar (modal de confirmación más claro)
- [ ] Feedback visual al guardar/actualizar (toast notifications)
- [ ] Loading states más consistentes en toda la app
- [ ] Validación de formularios en tiempo real (no solo al submit)
- [ ] Mensajes de error más claros y accionables

### Prioridad Media
- [ ] Tema oscuro (Dark mode)
- [ ] Animaciones de transición entre páginas
- [ ] Skeleton loaders en lugar de spinners
- [ ] Búsqueda con debounce para mejor performance
- [ ] Paginación en tablas grandes
- [ ] Exportación de datos (CSV, Excel)

### Prioridad Baja
- [ ] Atajos de teclado
- [ ] Modo offline (PWA)
- [ ] Personalización de colores por centro
- [ ] Widgets arrastrables en dashboard
- [ ] Impresión de reportes optimizada

---

## Optimizaciones Técnicas

### Performance
- [ ] Implementar lazy loading de componentes
- [ ] Optimizar queries con select_related/prefetch_related
- [ ] Implementar caché de Redis para queries frecuentes
- [ ] Comprimir imágenes automáticamente
- [ ] Implementar CDN para assets estáticos

### Seguridad
- [ ] Implementar rate limiting por usuario
- [ ] Agregar 2FA opcional
- [ ] Logs de auditoría para acciones críticas
- [ ] Encriptación de campos sensibles
- [ ] Revisión de permisos por endpoint

### Testing
- [ ] Tests unitarios backend (pytest)
- [ ] Tests de integración API
- [ ] Tests frontend (Jest + React Testing Library)
- [ ] Tests E2E (Playwright o Cypress)
- [ ] Coverage mínimo 80%

---

## Notas de Implementación

### Orden Sugerido de Desarrollo (Post-MVP)

1. **Fase 2 - Funcionalidades Core** (4-6 semanas)
   - Mejora de selector de horarios (Opción B)
   - Inventario básico
   - Empleados y comisiones
   - Finanzas básicas

2. **Fase 3 - Integraciones** (2-4 semanas)
   - WhatsApp notifications
   - Calendario visual (Opción C)
   - Exportación de reportes

3. **Fase 4 - Analytics y Optimización** (2-3 semanas)
   - Dashboard completo
   - Reportes avanzados
   - Optimizaciones de performance

4. **Fase 5 - Polish** (2-3 semanas)
   - Mejoras de UX/UI
   - Testing completo
   - Documentación

---

**Última actualización**: 2025-01-14
**Versión actual**: 1.0 MVP
**Próxima versión planificada**: 1.1 (Fase 2)
