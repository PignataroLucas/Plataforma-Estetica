# Features Pendientes y Roadmap

Este documento lista funcionalidades que están parcialmente implementadas o planificadas para futuras versiones de la plataforma.

---

## 🚧 Features Parcialmente Implementadas

### 1. Sistema Multi-Sucursal (UI Pendiente)

**Estado**: Backend 100% implementado | Frontend 0% implementado

**Descripción**:
El backend ya soporta completamente múltiples sucursales por centro estético. Todos los modelos principales (Servicios, Productos, Turnos, Transacciones, Máquinas Alquiladas, Empleados) están vinculados a una sucursal específica.

**Qué ya existe (Backend)**:
- ✅ Modelo `Sucursal` con FK a `CentroEstetica`
- ✅ Todos los modelos principales filtran por sucursal
- ✅ Usuarios asignados a sucursal específica
- ✅ API endpoints aceptan parámetro `sucursal_id` para filtrado
- ✅ Queries automáticos filtrados por `user.sucursal`
- ✅ Soporte para sucursal principal (`es_principal=True`)
- ✅ Analytics con filtrado por sucursal

**Qué falta implementar (Frontend)**:
- ❌ **Selector de Sucursales**: Dropdown en navbar/header para cambiar entre sucursales
- ❌ **Vista Consolidada**: Dashboard que muestre datos de todas las sucursales (solo para Admin/Owner)
- ❌ **Gestión de Sucursales**: CRUD completo para crear/editar/desactivar sucursales
- ❌ **Comparación entre Sucursales**: Analytics comparativas de rendimiento
- ❌ **Transferencias inter-sucursales**: Movimiento de inventario entre sucursales
- ❌ **Asignación de Empleados**: Cambiar empleados de sucursal desde la UI

**Prioridad**: Media-Alta (importante para centros con múltiples locaciones)

**Estimación de desarrollo**:
- Selector de sucursales: 2-3 días
- Vista consolidada: 3-4 días
- CRUD de sucursales: 2-3 días
- Analytics comparativas: 4-5 días
- **Total**: 11-15 días

**Casos de uso**:
- Centro con múltiples locaciones (Ej: Belgrano, Palermo, Recoleta)
- Admin/Owner que quiere ver rendimiento de cada sucursal
- Manager que solo debe ver datos de su sucursal
- Transferencia de stock entre sucursales

**Componentes a crear**:
```
frontend/src/components/sucursales/
├── SucursalSelector.tsx       # Dropdown para cambiar sucursal activa
├── SucursalForm.tsx            # Formulario crear/editar sucursal
├── SucursalesList.tsx          # Lista de sucursales del centro
├── SucursalCard.tsx            # Card con info y métricas de sucursal
└── SucursalComparison.tsx      # Comparación de rendimiento

frontend/src/pages/
└── SucursalesPage.tsx          # Página de gestión de sucursales

frontend/src/stores/
└── useSucursalStore.ts         # Zustand store para sucursal activa
```

**Flujo de usuario propuesto**:
1. Admin/Owner ve selector de sucursales en navbar (al lado del nombre de usuario)
2. Puede seleccionar:
   - Una sucursal específica (filtra todo el dashboard a esa sucursal)
   - "Todas las sucursales" (vista consolidada con totales agregados)
3. Managers/Empleados solo ven su sucursal asignada (sin selector)
4. Al cambiar de sucursal, todo el dashboard se actualiza automáticamente

**Endpoints ya disponibles (solo falta UI)**:
- `GET /api/sucursales/` - Listar sucursales del centro
- `GET /api/sucursales/{id}/` - Detalle de sucursal
- `GET /api/analytics/dashboard/summary/?sucursal_id=1` - Analytics filtrados
- `GET /api/turnos/?sucursal=1` - Turnos de sucursal específica

---

## 📋 Features Completamente Nuevas (No implementadas)

### 2. Verificación de Email y Teléfono

**Estado**: No implementado

**Descripción**:
Sistema de verificación de email y teléfono para nuevos registros y seguridad adicional.

**Funcionalidades**:
- Envío de email de confirmación con link de activación
- Código de verificación por SMS
- Cuenta en estado "pendiente" hasta verificar
- Reenvío de códigos de verificación
- Recuperación de contraseña por email/SMS

**Prioridad**: Media

**Estimación**: 5-7 días

**Dependencias**:
- Servicio de email (SendGrid, AWS SES, Mailgun)
- Servicio de SMS (Twilio, WhatsApp Business API ya integrado)

---

### 3. Onboarding Guiado

**Estado**: No implementado

**Descripción**:
Tour interactivo para nuevos usuarios que los guía a través de las funcionalidades principales.

**Funcionalidades**:
- Tutorial paso a paso al primer login
- Tooltips contextuales en features clave
- Checklist de primeros pasos:
  - [ ] Agregar primer servicio
  - [ ] Crear primer empleado
  - [ ] Registrar primer cliente
  - [ ] Agendar primer turno
  - [ ] Configurar notificaciones WhatsApp
- Videos tutoriales embebidos
- Documentación in-app

**Prioridad**: Media

**Estimación**: 4-6 días

**Tecnologías sugeridas**:
- React Joyride para tours guiados
- Intro.js para tooltips
- Video.js para tutoriales embebidos

---

### 4. Importación Masiva de Datos

**Estado**: No implementado

**Descripción**:
Permitir a nuevos usuarios importar datos existentes desde Excel/CSV o migrar desde otras plataformas.

**Funcionalidades**:
- Importar clientes desde Excel/CSV
- Importar servicios y precios
- Importar productos e inventario inicial
- Validación de datos antes de importar
- Vista previa de datos a importar
- Manejo de errores y duplicados
- Exportar template Excel con formato correcto

**Prioridad**: Alta (facilita onboarding de nuevos clientes)

**Estimación**: 6-8 días

**Formatos soportados**:
- Excel (.xlsx)
- CSV (.csv)
- Google Sheets (API)

---

### 5. Integración con AFIP (Argentina)

**Estado**: No implementado

**Descripción**:
Integración con AFIP para facturación electrónica (obligatorio para negocios en Argentina).

**Funcionalidades**:
- Generación de facturas electrónicas A, B, C
- Consulta de situación fiscal de clientes (CUIT)
- Envío automático de comprobantes a AFIP
- Almacenamiento de CAE (Código de Autorización Electrónico)
- Reportes de facturación para DDJJ
- Libro IVA digital

**Prioridad**: Alta (requerimiento legal en Argentina)

**Estimación**: 15-20 días

**Dependencias**:
- SDKs de AFIP (pyafipws)
- Certificado digital
- Homologación en ambiente de testing AFIP

---

### 6. Sistema de Pagos Online

**Estado**: No implementado

**Descripción**:
Permitir a clientes pagar servicios/productos online con tarjeta de crédito/débito.

**Funcionalidades**:
- Integración con MercadoPago (Argentina/LATAM)
- Integración con Stripe (internacional)
- Pago de servicios al agendar turno
- Link de pago enviado por WhatsApp
- Cobro de señas/depósitos online
- Facturación automática al recibir pago
- Webhooks para actualizar estado de pago

**Prioridad**: Media-Alta

**Estimación**: 8-10 días

**Pasarelas sugeridas**:
- MercadoPago (preferido para Argentina)
- Stripe (internacional)
- Todo Pago (alternativa Argentina)

---

### 7. App Móvil para Empleados

**Estado**: No implementado

**Descripción**:
Aplicación móvil nativa para que empleados/profesionales puedan gestionar su agenda desde el celular.

**Funcionalidades**:
- Ver agenda del día
- Marcar turnos como completados
- Registrar ventas en Mi Caja
- Notificaciones push de nuevos turnos
- Acceso a datos de clientes
- Ver comisiones ganadas
- Bloquear/desbloquear horarios

**Prioridad**: Media

**Estimación**: 30-40 días

**Tecnologías**:
- React Native (iOS + Android)
- Expo para deployment rápido
- Push notifications (Firebase)

---

### 8. Portal de Clientes

**Estado**: No implementado

**Descripción**:
Portal web donde clientes finales pueden auto-gestionar sus turnos y ver su historial.

**Funcionalidades**:
- Login de cliente con email/teléfono
- Ver próximos turnos
- Agendar nuevo turno (disponibilidad en tiempo real)
- Cancelar/reprogramar turnos
- Ver historial de servicios
- Descargar comprobantes de pago
- Ver fotos antes/después
- Perfil con datos personales

**Prioridad**: Alta (reduce carga de trabajo de recepción)

**Estimación**: 15-20 días

**Beneficios**:
- Reduce llamadas telefónicas para agendar
- Clientes pueden agendar 24/7
- Menos no-shows (clientes gestionan su agenda)

---

### 9. Sistema de Fidelización/Lealtad

**Estado**: No implementado

**Descripción**:
Programa de puntos y recompensas para incentivar la lealtad de clientes.

**Funcionalidades**:
- Acumulación de puntos por servicios/productos
- Diferentes niveles de membresía (Bronce, Plata, Oro, Platino)
- Descuentos automáticos por nivel
- Recompensas canjeables (servicios gratis, descuentos)
- Cumpleaños con bonus especial
- Referidos con puntos
- Dashboard de puntos para clientes

**Prioridad**: Media

**Estimación**: 8-10 días

---

### 10. Reportes Avanzados en PDF/Excel

**Estado**: Parcialmente implementado (solo exportación básica)

**Descripción**:
Generación de reportes profesionales personalizables en PDF y Excel.

**Funcionalidades actuales**:
- ✅ Exportación básica de analytics a Excel

**Funcionalidades pendientes**:
- ❌ PDFs con logo del centro y branding
- ❌ Reportes programados (envío automático semanal/mensual por email)
- ❌ Templates personalizables de reportes
- ❌ Gráficos incluidos en PDFs
- ❌ Reporte de comisiones para empleados
- ❌ Reporte fiscal mensual/anual
- ❌ Reporte de inventario con stock crítico

**Prioridad**: Media

**Estimación**: 5-7 días

**Tecnologías**:
- PDFKit o ReportLab (backend Python)
- ExcelJS (frontend para Excel avanzado)

---

### 11. Integración con Google Calendar

**Estado**: No implementado

**Descripción**:
Sincronización bidireccional de turnos con Google Calendar de empleados.

**Funcionalidades**:
- Exportar turnos a Google Calendar de profesional
- Importar eventos de Google Calendar como bloqueos
- Actualización en tiempo real (webhooks)
- Evitar doble-booking con agenda personal

**Prioridad**: Baja

**Estimación**: 4-5 días

---

### 12. Sistema de Comisiones Avanzado

**Estado**: Modelo definido pero comentado (pendiente de activación)

**Descripción**:
Sistema completo de cálculo y seguimiento de comisiones para empleados.

**Funcionalidades pendientes**:
- Activar modelo `Comision` (actualmente comentado)
- Diferentes esquemas de comisión:
  - Porcentaje por servicio
  - Monto fijo por servicio
  - Comisiones escalonadas (tiers)
  - Comisión por venta de productos
- Cálculo automático al completar turno
- Reporte de comisiones por empleado
- Liquidación mensual de comisiones
- Estado de pago (pendiente/pagada)
- Exportación para nómina

**Prioridad**: Media-Alta

**Estimación**: 5-7 días

**Nota**: El modelo ya existe en `apps/empleados/models.py` líneas 183-232, solo está comentado.

---

### 13. Chat Interno entre Empleados

**Estado**: No implementado

**Descripción**:
Sistema de mensajería interna para comunicación entre empleados del centro.

**Funcionalidades**:
- Chat 1-a-1 entre empleados
- Grupos por sucursal
- Notificaciones en tiempo real
- Compartir información de clientes
- Historial de mensajes

**Prioridad**: Baja

**Estimación**: 10-12 días

**Tecnologías**:
- WebSockets (Django Channels)
- Redis para pub/sub

---

### 14. Gestión de Inventario Avanzada

**Estado**: Básico implementado, faltan features avanzadas

**Funcionalidades actuales**:
- ✅ CRUD de productos
- ✅ Movimientos de inventario
- ✅ Alertas de stock bajo

**Funcionalidades pendientes**:
- ❌ Órdenes de compra a proveedores
- ❌ Recepción de mercadería con validación
- ❌ Inventario físico vs. sistema (ajustes)
- ❌ Códigos de barras / QR para productos
- ❌ Lotes y fechas de vencimiento
- ❌ Transferencias entre sucursales
- ❌ Predicción de stock (ML)
- ❌ Integración con proveedores (catálogos)

**Prioridad**: Media

**Estimación**: 12-15 días

---

### 15. Análisis Predictivo con IA/ML

**Estado**: No implementado

**Descripción**:
Uso de machine learning para predicciones y recomendaciones inteligentes.

**Funcionalidades**:
- Predicción de no-shows (clasificación)
- Recomendación de servicios a clientes (collaborative filtering)
- Predicción de demanda de productos
- Detección de clientes en riesgo de churn
- Optimización de precios dinámicos
- Detección de anomalías en ventas

**Prioridad**: Baja (nice-to-have)

**Estimación**: 20-30 días

**Tecnologías**:
- scikit-learn o TensorFlow
- pandas para análisis de datos
- Celery para entrenamiento asíncrono

---

### 16. Multi-idioma (i18n)

**Estado**: No implementado

**Descripción**:
Soporte para múltiples idiomas en la plataforma.

**Idiomas sugeridos**:
- Español (actual, default)
- Inglés
- Portugués (Brasil)

**Prioridad**: Baja

**Estimación**: 8-10 días

**Tecnologías**:
- Django i18n (backend)
- react-i18next (frontend)

---

### 17. Modo Oscuro (Dark Mode)

**Estado**: No implementado

**Descripción**:
Tema oscuro para la interfaz de usuario.

**Prioridad**: Baja

**Estimación**: 3-4 días

**Tecnologías**:
- Tailwind CSS dark mode
- Persistencia en localStorage

---

### 18. Backup y Recuperación de Datos

**Estado**: No implementado (solo backups automáticos de servidor)

**Descripción**:
Permitir a usuarios exportar y restaurar sus datos.

**Funcionalidades**:
- Exportación completa de todos los datos (JSON/SQL)
- Restauración desde backup
- Backups programados
- Retención de backups (30 días)
- Descarga de backups cifrados

**Prioridad**: Alta (seguridad de datos)

**Estimación**: 5-6 días

---

### 19. Auditoría y Logs de Acciones

**Estado**: Parcial (logs en servidor, no en UI)

**Descripción**:
Sistema completo de auditoría de acciones críticas.

**Funcionalidades**:
- Log de todas las acciones críticas:
  - Cambios en finanzas
  - Modificación de permisos
  - Eliminación de datos
  - Cambios de configuración
- Consulta de logs desde UI
- Filtrado por usuario, fecha, tipo de acción
- Exportación de logs

**Prioridad**: Media-Alta (seguridad y compliance)

**Estimación**: 4-5 días

---

### 20. Notificaciones In-App

**Estado**: No implementado (solo WhatsApp)

**Descripción**:
Sistema de notificaciones dentro de la aplicación.

**Funcionalidades**:
- Notificaciones en tiempo real (WebSockets)
- Badge con contador de notificaciones no leídas
- Panel de notificaciones
- Diferentes tipos:
  - Nuevos turnos
  - Cancelaciones
  - Stock bajo
  - Pagos recibidos
  - Alertas del sistema
- Marcar como leída
- Configuración de preferencias

**Prioridad**: Media

**Estimación**: 6-8 días

---

## 📊 Priorización Sugerida

### Corto Plazo (1-3 meses)
1. **Sistema Multi-Sucursal UI** ⭐⭐⭐⭐⭐
2. **Importación Masiva de Datos** ⭐⭐⭐⭐⭐
3. **Portal de Clientes** ⭐⭐⭐⭐⭐
4. **Sistema de Comisiones** ⭐⭐⭐⭐
5. **Integración AFIP** ⭐⭐⭐⭐ (si se opera en Argentina)

### Mediano Plazo (3-6 meses)
6. **Sistema de Pagos Online** ⭐⭐⭐⭐
7. **Onboarding Guiado** ⭐⭐⭐
8. **Verificación Email/Teléfono** ⭐⭐⭐
9. **Sistema de Fidelización** ⭐⭐⭐
10. **Reportes Avanzados PDF** ⭐⭐⭐

### Largo Plazo (6-12 meses)
11. **App Móvil** ⭐⭐⭐
12. **Gestión Inventario Avanzada** ⭐⭐⭐
13. **Análisis Predictivo IA** ⭐⭐
14. **Notificaciones In-App** ⭐⭐
15. **Multi-idioma** ⭐⭐

### Opcional / Nice-to-Have
16. Chat Interno
17. Integración Google Calendar
18. Modo Oscuro
19. Backup UI
20. Auditoría UI

---

## 🎯 Criterios de Priorización

- **Impacto en negocio**: ¿Genera más ventas o retiene clientes?
- **Demanda de usuarios**: ¿Lo piden los clientes actuales?
- **Complejidad técnica**: ¿Cuánto esfuerzo requiere?
- **Dependencias**: ¿Bloquea otras features?
- **Compliance**: ¿Es legalmente requerido?

---

## 📝 Notas

- Este documento debe actualizarse regularmente a medida que se implementan features
- Algunas features pueden cambiar de prioridad según feedback de usuarios
- Estimaciones son aproximadas y pueden variar según complejidad encontrada
- Features marcadas como "Parcialmente implementadas" tienen backend listo pero requieren UI

**Última actualización**: 1 de Enero 2026
