# MÓDULO DE ANALYTICS - ESPECIFICACIÓN TÉCNICA

**Plataforma de Gestión para Centros de Estética**
Versión 1.0 - Diciembre 2025

---

## TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Objetivos del Módulo](#2-objetivos-del-módulo)
3. [Analytics Global - Dashboard General](#3-analytics-global---dashboard-general)
4. [Analytics de Cliente Individual](#4-analytics-de-cliente-individual)
5. [Especificación Técnica del Backend](#5-especificación-técnica-del-backend)
6. [Especificación Técnica del Frontend](#6-especificación-técnica-del-frontend)
7. [Plan de Implementación](#7-plan-de-implementación)
8. [Consideraciones de Performance](#8-consideraciones-de-performance)
9. [Wireframes y UX](#9-wireframes-y-ux)

---

## 1. RESUMEN EJECUTIVO

El módulo de Analytics transformará los datos operacionales de la plataforma en **insights accionables** para la toma de decisiones estratégicas. Se compone de dos subsistemas principales:

### **Analytics Global**
Dashboard ejecutivo para Administradores y Managers con métricas agregadas del negocio: ventas, ocupación, performance de empleados, rentabilidad.

### **Analytics de Cliente Individual**
Perfil analítico profundo de cada cliente con patrones de consumo, frecuencia de visitas, tendencias de gasto, y alertas de comportamiento.

### **Valor de Negocio**
- **Optimización de Precios**: Identificar servicios más/menos rentables
- **Retención de Clientes**: Detectar clientes en riesgo de abandono
- **Gestión de Capacidad**: Optimizar horarios según ocupación real
- **Performance de Staff**: Incentivar empleados basado en métricas objetivas
- **Forecasting**: Proyectar ingresos y planificar recursos

---

## 2. OBJETIVOS DEL MÓDULO

### Objetivos Funcionales

1. **Visibilidad Total del Negocio**
   - Métricas clave en tiempo real
   - Visualizaciones interactivas
   - Comparativas temporales

2. **Análisis Profundo de Clientes**
   - Perfil de consumo individual
   - Detección de patrones de comportamiento
   - Sistema de alertas proactivo

3. **Optimización Basada en Datos**
   - Identificar horarios pico y bajos
   - Servicios de mayor/menor demanda
   - Rentabilidad por servicio/producto

4. **Forecasting y Proyecciones**
   - Tendencias estacionales
   - Proyección de ingresos
   - Predicción de capacidad necesaria

### Objetivos Técnicos

- **Performance**: Queries optimizados con agregaciones SQL y cacheo
- **Escalabilidad**: Diseño que soporte crecimiento de datos históricos
- **Usabilidad**: Dashboards intuitivos con visualizaciones claras
- **Exportabilidad**: Reportes descargables en PDF y Excel

---

## 3. ANALYTICS GLOBAL - DASHBOARD GENERAL

Dashboard principal accesible para roles Admin y Manager. Vista consolidada del negocio.

### 3.1 KPIs Principales (Cards de Resumen)

**Métricas Generales**
- **Ingresos Totales**: Total del período seleccionado
  - Comparación con período anterior (% de cambio)
  - Desglose: Servicios vs Productos vs Otros

- **Cantidad de Citas**: Total de turnos completados
  - Comparación con período anterior
  - Tasa de completitud (completados/agendados)

- **Clientes Activos**: Clientes con al menos 1 visita en el período
  - Nuevos clientes vs recurrentes
  - Tasa de retención

- **Ticket Promedio**: Ingreso promedio por transacción
  - Comparación con período anterior
  - Tendencia (creciente/decreciente)

**Filtros Globales**
- Rango de fechas (últimos 7 días, 30 días, 3 meses, 6 meses, 1 año, custom)
- Sucursal (individual o todas)
- Tipo de vista: Diario, Semanal, Mensual, Anual

### 3.2 Gráficos de Ventas e Ingresos

**Evolución de Ingresos**
- **Tipo**: Gráfico de líneas o áreas
- **Datos**: Ingresos totales por período (día/semana/mes)
- **Series múltiples**:
  - Ingresos por servicios
  - Ingresos por productos
  - Total general
- **Interactividad**: Hover para ver detalles, zoom, exportar imagen

**Comparativa de Ingresos**
- **Tipo**: Gráfico de barras
- **Datos**: Comparación período actual vs período anterior
- **Vista**: Mes a mes, trimestre a trimestre, año a año

**Distribución de Ingresos por Método de Pago**
- **Tipo**: Pie chart o donut
- **Datos**: % de ingresos por método (Efectivo, Tarjeta, Transferencia, MercadoPago, etc.)

### 3.3 Análisis de Servicios

**Top 10 Servicios Más Vendidos**
- **Tipo**: Gráfico de barras horizontales
- **Datos**: Cantidad de servicios realizados
- **Métricas adicionales**: Ingresos generados, ticket promedio

**Evolución de Servicios**
- **Tipo**: Gráfico de líneas múltiples
- **Datos**: Cantidad de servicios por tipo a lo largo del tiempo
- **Selección**: Top 5 servicios seleccionables

**Análisis de Rentabilidad de Servicios**
- **Tipo**: Tabla interactiva con ordenamiento
- **Columnas**:
  - Nombre del servicio
  - Cantidad vendida
  - Ingresos totales
  - Costo (máquina alquilada si aplica)
  - Margen bruto
  - Rentabilidad %
- **Ordenamiento**: Por cualquier columna
- **Filtros**: Por categoría de servicio

### 3.4 Análisis de Productos

**Top 10 Productos Más Vendidos**
- **Tipo**: Gráfico de barras
- **Datos**: Cantidad vendida y ingresos generados
- **Vista**: Intercambiable entre cantidad e ingresos

**Rotación de Inventario**
- **Tipo**: Tabla con indicadores visuales
- **Datos**: Productos ordenados por velocidad de rotación
- **Métricas**: Stock actual, ventas último mes, días para agotarse

**Margen de Productos**
- **Tipo**: Scatter plot (dispersión)
- **Ejes**: X = Cantidad vendida, Y = Margen de ganancia %
- **Insight**: Identificar productos de alto volumen/bajo margen vs bajo volumen/alto margen

### 3.5 Performance de Empleados

**Ranking de Empleados**
- **Tipo**: Tabla clasificada
- **Métricas por empleado**:
  - Nombre
  - Servicios realizados
  - Ingresos generados
  - Ticket promedio
  - Comisiones ganadas
  - Rating (si aplica)
- **Filtros**: Por sucursal, por período

**Evolución de Performance Individual**
- **Tipo**: Gráfico de líneas
- **Datos**: Ingresos generados por empleado a lo largo del tiempo
- **Selección**: Comparar hasta 5 empleados simultáneamente

**Distribución de Carga de Trabajo**
- **Tipo**: Gráfico de barras apiladas
- **Datos**: Cantidad de turnos por empleado
- **Vista**: Por día de la semana, por franja horaria

### 3.6 Análisis de Clientes

**Métricas Generales de Clientes**
- Total de clientes registrados
- Clientes nuevos en el período
- Clientes activos vs inactivos
- Tasa de retención

**Segmentación de Clientes**
- **Tipo**: Pie chart
- **Categorías**:
  - Nuevos (primera visita en los últimos 30 días)
  - Activos (visita en últimos 30 días)
  - En Riesgo (última visita hace 30-90 días)
  - Inactivos (sin visita hace +90 días)
  - VIP (top 20% en gasto)

**Top Clientes por Gasto**
- **Tipo**: Tabla
- **Datos**: Top 20 clientes ordenados por lifetime value
- **Columnas**: Nombre, Total gastado, Cantidad de visitas, Última visita

**Distribución de Lifetime Value**
- **Tipo**: Histograma
- **Datos**: Cantidad de clientes por rango de gasto total
- **Rangos**: 0-5k, 5k-10k, 10k-20k, 20k-50k, +50k (ajustables según moneda)

### 3.7 Análisis de Ocupación

**Ocupación por Día de la Semana**
- **Tipo**: Gráfico de barras
- **Datos**: % de ocupación por día (Lunes-Domingo)
- **Cálculo**: Turnos realizados / Capacidad total teórica

**Ocupación por Franja Horaria**
- **Tipo**: Heatmap
- **Ejes**: X = Día de semana, Y = Franja horaria
- **Color**: Intensidad según nivel de ocupación
- **Insight**: Identificar horarios pico y bajos

**Evolución de Ocupación**
- **Tipo**: Gráfico de líneas
- **Datos**: % de ocupación a lo largo del tiempo
- **Objetivo**: Detectar tendencias estacionales

### 3.8 Tasas de No-Show y Cancelaciones

**Métricas Generales**
- Tasa de no-show general (% de turnos marcados como NO_SHOW)
- Tasa de cancelación (% de turnos cancelados)
- Comparación con período anterior

**No-Show por Día de Semana**
- **Tipo**: Gráfico de barras
- **Insight**: ¿Qué días hay más ausencias?

**No-Show por Servicio**
- **Tipo**: Tabla ordenable
- **Datos**: Servicios con mayor tasa de no-show
- **Acción**: Implementar recordatorios más agresivos

**No-Show por Cliente**
- **Tipo**: Tabla
- **Datos**: Clientes con mayor cantidad de no-shows
- **Acción**: Política de depósito obligatorio

### 3.9 Tendencias Estacionales

**Ingresos por Mes (12 meses)**
- **Tipo**: Gráfico de barras
- **Datos**: Ingresos de cada mes del último año
- **Insight**: Identificar meses altos y bajos

**Comparativa Año a Año**
- **Tipo**: Gráfico de líneas superpuestas
- **Datos**: Año actual vs año anterior (mes a mes)
- **Insight**: Crecimiento real del negocio

### 3.10 Exportación de Reportes

**Formatos Disponibles**
- PDF: Reporte ejecutivo con gráficos
- Excel: Datos tabulados para análisis externo
- CSV: Data raw para BI externo

**Contenido del Reporte**
- KPIs principales
- Gráficos clave (imágenes embebidas)
- Tablas de datos
- Fecha de generación y período

---

## 4. ANALYTICS DE CLIENTE INDIVIDUAL

Perfil analítico profundo accesible desde la vista de detalles de cada cliente.

### 4.1 Resumen General del Cliente

**Tarjeta de Resumen** (Header del perfil)
- **Lifetime Value**: Total gastado histórico (grande y destacado)
- **Total de Visitas**: Cantidad total de servicios realizados
- **Cliente Desde**: Fecha de primera visita
- **Última Visita**: Fecha y hace cuánto tiempo
- **Frecuencia Promedio**: "Visita cada X días en promedio"
- **Estado**: Badge visual (VIP / Activo / En Riesgo / Inactivo)

**Cálculo de Estado del Cliente**
- **VIP**: Lifetime value en top 20% de clientes
- **Activo**: Última visita hace menos de 30 días
- **En Riesgo**: Última visita hace 30-90 días (más de su frecuencia promedio)
- **Inactivo**: Última visita hace más de 90 días

### 4.2 Gráficos de Gasto

**Gasto Mensual (Últimos 12 Meses)**
- **Tipo**: Gráfico de barras o líneas
- **Datos**: Total gastado cada mes
- **Línea de tendencia**: Regresión lineal para ver si gasta más/menos
- **Promedio**: Línea horizontal con gasto promedio mensual

**Evolución del Ticket Promedio**
- **Tipo**: Gráfico de líneas
- **Datos**: Ticket promedio por visita a lo largo del tiempo
- **Insight**: ¿El cliente está consumiendo servicios más caros?

**Distribución del Gasto**
- **Tipo**: Pie chart
- **Datos**: % gastado en Servicios vs Productos
- **Desglose secundario**: Por tipo de servicio

**Comparativa Año a Año**
- **Tipo**: Gráfico de barras agrupadas
- **Datos**: Gasto mensual año actual vs año anterior
- **Insight**: ¿El cliente está más o menos activo que antes?

### 4.3 Gráficos de Servicios

**Servicios por Mes (Últimos 12 Meses)**
- **Tipo**: Gráfico de barras
- **Datos**: Cantidad de visitas/servicios por mes
- **Promedio**: Línea con promedio mensual

**Servicios Favoritos**
- **Tipo**: Pie chart o donut
- **Datos**: Distribución de servicios consumidos por tipo
- **Top 5**: Servicios más consumidos por este cliente

**Historial de Servicios (Timeline)**
- **Tipo**: Lista cronológica inversa con cards
- **Datos por servicio**:
  - Fecha
  - Servicio realizado
  - Profesional
  - Monto pagado
  - Método de pago
  - Notas (si hay)
- **Paginación**: 10-20 por página
- **Filtros**: Por tipo de servicio, por fecha

**Evolución de Frecuencia de Visitas**
- **Tipo**: Gráfico de líneas
- **Datos**: Cantidad de visitas por mes a lo largo del tiempo
- **Insight**: ¿El cliente está viniendo más o menos seguido?

### 4.4 Análisis de Patrones Temporales

**Días de la Semana Preferidos**
- **Tipo**: Gráfico de barras
- **Datos**: Cantidad de visitas por día de semana (L-D)
- **Insight**: "Este cliente prefiere venir los Martes y Jueves"

**Horarios Preferidos**
- **Tipo**: Gráfico de barras
- **Franjas**: Mañana (9-13h), Tarde (13-18h), Noche (18-21h)
- **Datos**: Cantidad de visitas por franja
- **Insight**: Para sugerirle horarios al agendar

**Meses de Mayor/Menor Actividad**
- **Tipo**: Gráfico de barras
- **Datos**: Actividad promedio por mes del año (agregado de todos los años)
- **Insight**: "Este cliente suele venir más en verano"

**Heatmap de Actividad**
- **Tipo**: Heatmap calendario (estilo GitHub)
- **Datos**: Cada celda = un día, color según actividad (visitas)
- **Período**: Último año
- **Insight visual**: Patrones de regularidad

### 4.5 Análisis de Comportamiento

**Métricas de Comportamiento**
- **Tasa de No-Show**: % de veces que no asistió
- **Tasa de Cancelación**: % de veces que canceló
- **Puntualidad**: % de veces que llegó a tiempo (si se trackea)
- **Tasa de Reprogramación**: % de veces que movió su cita

**Tiempo Promedio Entre Visitas**
- **Valor**: X días promedio
- **Distribución**: Histograma de intervalos entre visitas
- **Insight**: Regularidad del cliente

**Tendencia de Fidelización**
- **Indicador visual**: Gráfico de gauge o score 0-100
- **Factores**:
  - Frecuencia de visitas (vs promedio general)
  - Recencia (hace cuánto vino)
  - Valor monetario (vs promedio general)
  - Tendencia (mejorando/empeorando)
- **Interpretación**:
  - 80-100: Cliente fiel (verde)
  - 50-79: Cliente estable (amarillo)
  - 0-49: Cliente en riesgo (rojo)

### 4.6 Productos Comprados

**Productos Favoritos**
- **Tipo**: Tabla ordenada
- **Datos**: Productos comprados más frecuentemente
- **Columnas**: Producto, Cantidad total, Última compra

**Gasto en Productos vs Servicios**
- **Tipo**: Gráfico de barras apiladas por mes
- **Datos**: Desglose de gasto mensual entre productos y servicios
- **Insight**: ¿Oportunidad de upselling de productos?

### 4.7 Alertas y Insights Automáticos

**Sistema de Alertas Inteligentes**

Panel de alertas en la parte superior del perfil con badges visuales:

**Alertas de Riesgo** (Rojas)
- 🚨 "Cliente en riesgo - Sin visita hace 45 días (su promedio es 21 días)"
- 🚨 "Tendencia decreciente - Ha reducido su frecuencia en 40% vs año anterior"
- 🚨 "Alto no-show - 3 ausencias en los últimos 5 turnos"

**Alertas de Oportunidad** (Verdes)
- 💚 "Cliente VIP - En top 10% de gasto total"
- 💚 "Oportunidad de upselling - Nunca ha comprado productos"
- 💚 "Cliente leal - 12 meses consecutivos con visitas"
- 💚 "Cumpleaños próximo - En 15 días (ofertas especiales?)"

**Insights Automáticos** (Azules)
- 💡 "Patrón detectado - Siempre viene el último martes del mes"
- 💡 "Prefiere profesional: Ana García (75% de sus visitas)"
- 💡 "Gasto creciente - +35% vs mismo período año anterior"
- 💡 "Cliente estacional - Más activo en Sep-Dic"

**Recomendaciones Accionables**
- ✅ "Enviar recordatorio - Hace 30 días de su última visita"
- ✅ "Ofrecer paquete - Consume siempre el mismo servicio 3x/mes"
- ✅ "Requiere depósito - Alta tasa de no-show (30%)"

### 4.8 Predicciones (Opcional - Fase Avanzada)

**Próxima Visita Estimada**
- **Cálculo**: Basado en frecuencia promedio
- **Visualización**: "Se espera que regrese entre el 15-20 de Enero"
- **Confianza**: Baja/Media/Alta según regularidad del cliente

**Lifetime Value Proyectado**
- **Cálculo**: LTV actual + proyección a 12 meses basado en tendencia
- **Visualización**: Número proyectado con % de confianza

---

## 5. ESPECIFICACIÓN TÉCNICA DEL BACKEND

### 5.1 Estructura de URLs

```python
# apps/analytics/urls.py

urlpatterns = [
    # Analytics Global
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('dashboard/revenue/', RevenueAnalyticsView.as_view(), name='dashboard-revenue'),
    path('dashboard/services/', ServiceAnalyticsView.as_view(), name='dashboard-services'),
    path('dashboard/products/', ProductAnalyticsView.as_view(), name='dashboard-products'),
    path('dashboard/employees/', EmployeePerformanceView.as_view(), name='dashboard-employees'),
    path('dashboard/clients/', ClientAnalyticsView.as_view(), name='dashboard-clients'),
    path('dashboard/ocupacion/', OccupancyAnalyticsView.as_view(), name='dashboard-ocupacion'),
    path('dashboard/no-shows/', NoShowAnalyticsView.as_view(), name='dashboard-no-shows'),

    # Analytics de Cliente Individual
    path('client/<int:cliente_id>/summary/', ClientSummaryView.as_view(), name='client-summary'),
    path('client/<int:cliente_id>/spending/', ClientSpendingView.as_view(), name='client-spending'),
    path('client/<int:cliente_id>/services/', ClientServicesView.as_view(), name='client-services'),
    path('client/<int:cliente_id>/patterns/', ClientPatternsView.as_view(), name='client-patterns'),
    path('client/<int:cliente_id>/behavior/', ClientBehaviorView.as_view(), name='client-behavior'),
    path('client/<int:cliente_id>/alerts/', ClientAlertsView.as_view(), name='client-alerts'),

    # Exportación
    path('export/pdf/', ExportPDFView.as_view(), name='export-pdf'),
    path('export/excel/', ExportExcelView.as_view(), name='export-excel'),
]
```

### 5.2 Views y Endpoints

#### 5.2.1 Dashboard Summary View

**Endpoint**: `GET /api/analytics/dashboard/summary/`

**Query Params**:
- `start_date`: Fecha inicio (YYYY-MM-DD)
- `end_date`: Fecha fin (YYYY-MM-DD)
- `sucursal_id`: ID de sucursal (opcional, null = todas)

**Response**:
```json
{
  "kpis": {
    "total_revenue": 450000.00,
    "revenue_change": 15.5,  // % vs período anterior
    "revenue_breakdown": {
      "services": 350000.00,
      "products": 100000.00
    },
    "total_appointments": 320,
    "appointments_change": 8.2,
    "completion_rate": 85.5,  // % completados
    "active_clients": 156,
    "new_clients": 23,
    "retention_rate": 78.5,
    "average_ticket": 1406.25,
    "ticket_change": 6.8
  },
  "period": {
    "start": "2025-11-01",
    "end": "2025-11-30",
    "previous_start": "2025-10-01",
    "previous_end": "2025-10-31"
  }
}
```

#### 5.2.2 Revenue Analytics View

**Endpoint**: `GET /api/analytics/dashboard/revenue/`

**Query Params**:
- `start_date`, `end_date`, `sucursal_id`
- `granularity`: day | week | month
- `compare`: true | false (incluir período anterior)

**Response**:
```json
{
  "evolution": [
    {
      "date": "2025-11-01",
      "services_revenue": 12500.00,
      "products_revenue": 3200.00,
      "total_revenue": 15700.00
    },
    // ... más datos
  ],
  "comparison": [
    {
      "period": "current",
      "month": "Nov 2025",
      "revenue": 450000.00
    },
    {
      "period": "previous",
      "month": "Oct 2025",
      "revenue": 390000.00
    }
  ],
  "by_payment_method": [
    {
      "method": "CASH",
      "amount": 180000.00,
      "percentage": 40.0
    },
    {
      "method": "CREDIT_CARD",
      "amount": 135000.00,
      "percentage": 30.0
    },
    // ...
  ]
}
```

#### 5.2.3 Service Analytics View

**Endpoint**: `GET /api/analytics/dashboard/services/`

**Response**:
```json
{
  "top_services": [
    {
      "service_id": 5,
      "service_name": "Masaje Descontracturante",
      "quantity_sold": 45,
      "revenue": 67500.00,
      "average_ticket": 1500.00
    },
    // ... top 10
  ],
  "evolution": [
    {
      "date": "2025-11",
      "services": {
        "Masaje Descontracturante": 45,
        "Lifting Facial": 32,
        // ...
      }
    }
  ],
  "profitability": [
    {
      "service_id": 5,
      "service_name": "Masaje Descontracturante",
      "quantity": 45,
      "revenue": 67500.00,
      "cost": 15000.00,  // costos de máquinas si aplica
      "gross_margin": 52500.00,
      "margin_percentage": 77.8
    },
    // ...
  ]
}
```

#### 5.2.4 Client Summary View

**Endpoint**: `GET /api/analytics/client/{cliente_id}/summary/`

**Response**:
```json
{
  "client_info": {
    "id": 123,
    "name": "María González",
    "email": "maria@email.com",
    "phone": "+54911..."
  },
  "summary": {
    "lifetime_value": 125000.00,
    "total_visits": 42,
    "first_visit": "2023-05-15",
    "last_visit": "2025-11-28",
    "days_since_last_visit": 10,
    "average_frequency_days": 18.5,
    "average_ticket": 2976.19,
    "status": "VIP",  // VIP | ACTIVE | AT_RISK | INACTIVE
    "status_color": "green"
  },
  "spending_trend": "increasing",  // increasing | stable | decreasing
  "loyalty_score": 87  // 0-100
}
```

#### 5.2.5 Client Spending View

**Endpoint**: `GET /api/analytics/client/{cliente_id}/spending/`

**Response**:
```json
{
  "monthly_spending_12m": [
    {
      "month": "2024-12",
      "amount": 5600.00,
      "visits": 3
    },
    {
      "month": "2025-01",
      "amount": 8900.00,
      "visits": 5
    },
    // ... 12 meses
  ],
  "average_monthly": 6500.00,
  "trend": {
    "direction": "increasing",
    "percentage": 12.5
  },
  "spending_distribution": {
    "services": {
      "amount": 100000.00,
      "percentage": 80.0
    },
    "products": {
      "amount": 25000.00,
      "percentage": 20.0
    }
  },
  "ticket_evolution": [
    {
      "date": "2024-12",
      "average_ticket": 1866.67
    },
    // ...
  ],
  "year_over_year": [
    {
      "month": "Jan",
      "2024": 5200.00,
      "2025": 8900.00
    },
    // ...
  ]
}
```

#### 5.2.6 Client Patterns View

**Endpoint**: `GET /api/analytics/client/{cliente_id}/patterns/`

**Response**:
```json
{
  "preferred_days": {
    "Monday": 2,
    "Tuesday": 8,
    "Wednesday": 5,
    "Thursday": 12,
    "Friday": 10,
    "Saturday": 5,
    "Sunday": 0
  },
  "preferred_time_slots": {
    "morning": 15,  // 9-13h
    "afternoon": 20,  // 13-18h
    "evening": 7  // 18-21h
  },
  "monthly_activity": {
    "Jan": 4.5,  // promedio de visitas
    "Feb": 3.2,
    // ...
  },
  "activity_heatmap": [
    {
      "date": "2025-01-15",
      "visits": 1
    },
    // ... últimos 365 días
  ]
}
```

#### 5.2.7 Client Alerts View

**Endpoint**: `GET /api/analytics/client/{cliente_id}/alerts/`

**Response**:
```json
{
  "alerts": [
    {
      "type": "risk",  // risk | opportunity | insight
      "severity": "high",  // high | medium | low
      "icon": "🚨",
      "title": "Cliente en riesgo",
      "message": "Sin visita hace 45 días (su promedio es 21 días)",
      "action": "send_reminder"
    },
    {
      "type": "opportunity",
      "severity": "medium",
      "icon": "💚",
      "title": "Oportunidad de upselling",
      "message": "Nunca ha comprado productos, solo servicios",
      "action": "offer_products"
    }
  ],
  "insights": [
    {
      "icon": "💡",
      "message": "Patrón detectado - Siempre viene el último martes del mes"
    },
    {
      "icon": "💡",
      "message": "Prefiere profesional: Ana García (75% de sus visitas)"
    }
  ],
  "recommendations": [
    {
      "icon": "✅",
      "message": "Enviar recordatorio - Hace 30 días de su última visita",
      "action": "send_whatsapp"
    }
  ]
}
```

### 5.3 Lógica de Cálculos y Agregaciones

#### 5.3.1 Agregaciones SQL Optimizadas

```python
# apps/analytics/utils.py

from django.db.models import Sum, Count, Avg, Q, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from apps.turnos.models import Turno
from apps.finanzas.models import Transaction
from datetime import datetime, timedelta

class AnalyticsCalculator:

    @staticmethod
    def get_revenue_summary(sucursal_id=None, start_date=None, end_date=None):
        """
        Calcula resumen de ingresos con agregaciones SQL eficientes
        """
        queryset = Transaction.objects.filter(
            fecha__gte=start_date,
            fecha__lte=end_date,
            type__in=['INCOME_SERVICE', 'INCOME_PRODUCT', 'INCOME_OTHER']
        )

        if sucursal_id:
            queryset = queryset.filter(sucursal_id=sucursal_id)

        summary = queryset.aggregate(
            total_revenue=Sum('amount'),
            services_revenue=Sum('amount', filter=Q(type='INCOME_SERVICE')),
            products_revenue=Sum('amount', filter=Q(type='INCOME_PRODUCT')),
            total_transactions=Count('id')
        )

        return summary

    @staticmethod
    def get_client_lifetime_value(cliente_id):
        """
        Calcula el Lifetime Value de un cliente
        """
        ltv = Transaction.objects.filter(
            cliente_id=cliente_id,
            type__in=['INCOME_SERVICE', 'INCOME_PRODUCT']
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

        return ltv

    @staticmethod
    def get_client_frequency(cliente_id):
        """
        Calcula la frecuencia promedio de visitas (en días)
        """
        visitas = Turno.objects.filter(
            cliente_id=cliente_id,
            estado='COMPLETADO'
        ).order_by('fecha', 'hora').values_list('fecha', flat=True)

        if len(visitas) < 2:
            return None

        # Calcular intervalos entre visitas consecutivas
        intervals = []
        for i in range(1, len(visitas)):
            delta = (visitas[i] - visitas[i-1]).days
            intervals.append(delta)

        average_interval = sum(intervals) / len(intervals) if intervals else None
        return average_interval

    @staticmethod
    def get_client_status(cliente_id):
        """
        Determina el estado del cliente (VIP, ACTIVE, AT_RISK, INACTIVE)
        """
        # Obtener LTV
        ltv = AnalyticsCalculator.get_client_lifetime_value(cliente_id)

        # Obtener LTV del percentil 80 (top 20%)
        ltv_threshold = Transaction.objects.filter(
            type__in=['INCOME_SERVICE', 'INCOME_PRODUCT']
        ).values('cliente_id').annotate(
            client_ltv=Sum('amount')
        ).order_by('-client_ltv').values_list('client_ltv', flat=True)

        # Calcular percentil 80
        if ltv_threshold:
            threshold_index = int(len(ltv_threshold) * 0.2)
            vip_threshold = list(ltv_threshold)[threshold_index] if threshold_index < len(ltv_threshold) else 0
        else:
            vip_threshold = 0

        # VIP check
        if ltv >= vip_threshold and vip_threshold > 0:
            return 'VIP'

        # Última visita
        last_visit = Turno.objects.filter(
            cliente_id=cliente_id,
            estado='COMPLETADO'
        ).order_by('-fecha', '-hora').first()

        if not last_visit:
            return 'INACTIVE'

        days_since_last = (datetime.now().date() - last_visit.fecha).days

        if days_since_last <= 30:
            return 'ACTIVE'
        elif days_since_last <= 90:
            return 'AT_RISK'
        else:
            return 'INACTIVE'

    @staticmethod
    def get_top_services(sucursal_id=None, start_date=None, end_date=None, limit=10):
        """
        Obtiene los servicios más vendidos
        """
        queryset = Turno.objects.filter(
            estado='COMPLETADO',
            fecha__gte=start_date,
            fecha__lte=end_date
        )

        if sucursal_id:
            queryset = queryset.filter(sucursal_id=sucursal_id)

        top_services = queryset.values(
            'servicio__id',
            'servicio__nombre'
        ).annotate(
            quantity=Count('id'),
            revenue=Sum('precio_final')
        ).order_by('-quantity')[:limit]

        return list(top_services)
```

### 5.4 Caché Strategy

```python
# apps/analytics/views.py

from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

class DashboardSummaryView(APIView):
    """
    Cachear por 5 minutos para queries pesadas
    """
    @method_decorator(cache_page(60 * 5))  # 5 minutos
    def get(self, request):
        # ... lógica
        pass

class ClientSummaryView(APIView):
    """
    Cachear por cliente individual
    """
    def get(self, request, cliente_id):
        cache_key = f'client_summary_{cliente_id}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        # Calcular datos
        data = self.calculate_summary(cliente_id)

        # Guardar en caché por 10 minutos
        cache.set(cache_key, data, 60 * 10)

        return Response(data)
```

### 5.5 Permisos y Seguridad

```python
# apps/analytics/permissions.py

from rest_framework import permissions

class IsAdminOrManager(permissions.BasePermission):
    """
    Solo Admin y Manager pueden acceder a analytics global
    """
    def has_permission(self, request, view):
        return request.user.rol in ['ADMIN', 'MANAGER']

class CanViewClientAnalytics(permissions.BasePermission):
    """
    Puede ver analytics de cliente si:
    - Es Admin/Manager de la misma sucursal/centro
    - Es el empleado asignado a ese cliente
    """
    def has_permission(self, request, view):
        cliente_id = view.kwargs.get('cliente_id')
        user = request.user

        # Admin siempre puede
        if user.rol == 'ADMIN':
            return True

        # Manager de la misma sucursal
        if user.rol == 'MANAGER':
            from apps.clientes.models import Cliente
            cliente = Cliente.objects.filter(
                id=cliente_id,
                centro_estetica=user.centro_estetica
            ).exists()
            return cliente

        # Empleado puede ver solo clientes que atendió
        if user.rol == 'EMPLEADO':
            from apps.turnos.models import Turno
            has_attended = Turno.objects.filter(
                cliente_id=cliente_id,
                profesional=user
            ).exists()
            return has_attended

        return False
```

---

## 6. ESPECIFICACIÓN TÉCNICA DEL FRONTEND

### 6.1 Estructura de Componentes

```
frontend/src/
├── components/
│   └── analytics/
│       ├── dashboard/
│       │   ├── KPICard.tsx              # Tarjeta de métrica individual
│       │   ├── RevenueChart.tsx         # Gráfico de ingresos
│       │   ├── ServicesChart.tsx        # Gráfico de servicios
│       │   ├── ProductsChart.tsx        # Gráfico de productos
│       │   ├── EmployeePerformance.tsx  # Performance de empleados
│       │   ├── ClientSegmentation.tsx   # Segmentación de clientes
│       │   ├── OccupancyHeatmap.tsx     # Heatmap de ocupación
│       │   └── DateRangeFilter.tsx      # Filtro de fechas
│       │
│       ├── client/
│       │   ├── ClientSummaryCard.tsx    # Resumen general del cliente
│       │   ├── SpendingChart.tsx        # Gráficos de gasto
│       │   ├── ServicesTimeline.tsx     # Timeline de servicios
│       │   ├── PatternsChart.tsx        # Patrones temporales
│       │   ├── BehaviorMetrics.tsx      # Métricas de comportamiento
│       │   ├── AlertsPanel.tsx          # Panel de alertas
│       │   └── ActivityHeatmap.tsx      # Heatmap de actividad
│       │
│       └── shared/
│           ├── LineChart.tsx            # Componente reutilizable de líneas
│           ├── BarChart.tsx             # Componente reutilizable de barras
│           ├── PieChart.tsx             # Componente reutilizable de pie
│           ├── DataTable.tsx            # Tabla con ordenamiento
│           └── ExportButton.tsx         # Botón de exportación
│
├── pages/
│   ├── AnalyticsPage.tsx                # Dashboard principal
│   └── ClientDetailPage.tsx             # Ya existe, agregar tab Analytics
│
└── hooks/
    ├── useAnalytics.ts                  # Hook para dashboard general
    └── useClientAnalytics.ts            # Hook para analytics de cliente
```

### 6.2 Librerías de Visualización

**Opción Recomendada: Recharts**
- Más sencillo de usar
- Integración nativa con React
- Responsive por defecto
- Personalización sencilla

```bash
npm install recharts
```

**Alternativa: Chart.js con react-chartjs-2**
- Más features avanzadas
- Mejor para gráficos complejos

```bash
npm install chart.js react-chartjs-2
```

### 6.3 Ejemplo de Componente: KPICard

```typescript
// components/analytics/dashboard/KPICard.tsx

import React from 'react';

interface KPICardProps {
  title: string;
  value: string | number;
  change?: number;  // % de cambio vs período anterior
  icon?: React.ReactNode;
  format?: 'currency' | 'number' | 'percentage';
}

export default function KPICard({ title, value, change, icon, format = 'number' }: KPICardProps) {
  const formatValue = (val: string | number) => {
    if (format === 'currency') {
      return `$${Number(val).toLocaleString('es-AR', { minimumFractionDigits: 2 })}`;
    } else if (format === 'percentage') {
      return `${val}%`;
    }
    return val.toLocaleString('es-AR');
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        {icon && <div className="text-gray-400">{icon}</div>}
      </div>

      <div className="flex items-end justify-between">
        <p className="text-3xl font-bold text-gray-900">
          {formatValue(value)}
        </p>

        {change !== undefined && (
          <div className={`flex items-center text-sm font-medium ${getChangeColor(change)}`}>
            {change > 0 ? '↑' : change < 0 ? '↓' : '−'}
            <span className="ml-1">{Math.abs(change)}%</span>
          </div>
        )}
      </div>

      {change !== undefined && (
        <p className="text-xs text-gray-500 mt-2">vs período anterior</p>
      )}
    </div>
  );
}
```

### 6.4 Ejemplo de Componente: RevenueChart

```typescript
// components/analytics/dashboard/RevenueChart.tsx

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface RevenueChartProps {
  data: {
    date: string;
    services_revenue: number;
    products_revenue: number;
    total_revenue: number;
  }[];
}

export default function RevenueChart({ data }: RevenueChartProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Evolución de Ingresos</h3>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip
            formatter={(value: number) => `$${value.toLocaleString('es-AR')}`}
          />
          <Legend />

          <Line
            type="monotone"
            dataKey="services_revenue"
            stroke="#8b5cf6"
            strokeWidth={2}
            name="Servicios"
          />
          <Line
            type="monotone"
            dataKey="products_revenue"
            stroke="#10b981"
            strokeWidth={2}
            name="Productos"
          />
          <Line
            type="monotone"
            dataKey="total_revenue"
            stroke="#3b82f6"
            strokeWidth={3}
            name="Total"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

### 6.5 Custom Hook: useAnalytics

```typescript
// hooks/useAnalytics.ts

import { useState, useEffect } from 'react';
import { api } from '../services/api';

interface AnalyticsFilters {
  startDate: string;
  endDate: string;
  sucursalId?: number;
}

export function useAnalytics(filters: AnalyticsFilters) {
  const [summary, setSummary] = useState<any>(null);
  const [revenue, setRevenue] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalytics();
  }, [filters]);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        start_date: filters.startDate,
        end_date: filters.endDate,
        ...(filters.sucursalId && { sucursal_id: filters.sucursalId.toString() })
      });

      const [summaryRes, revenueRes] = await Promise.all([
        api.get(`/analytics/dashboard/summary/?${params}`),
        api.get(`/analytics/dashboard/revenue/?${params}`)
      ]);

      setSummary(summaryRes.data);
      setRevenue(revenueRes.data);
    } catch (err: any) {
      setError(err.message || 'Error al cargar analytics');
    } finally {
      setLoading(false);
    }
  };

  return { summary, revenue, loading, error, refetch: fetchAnalytics };
}
```

### 6.6 Ejemplo de Página: AnalyticsPage

```typescript
// pages/AnalyticsPage.tsx

import React, { useState } from 'react';
import { useAnalytics } from '../hooks/useAnalytics';
import KPICard from '../components/analytics/dashboard/KPICard';
import RevenueChart from '../components/analytics/dashboard/RevenueChart';
import DateRangeFilter from '../components/analytics/dashboard/DateRangeFilter';

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState({
    startDate: '2025-11-01',
    endDate: '2025-11-30'
  });

  const { summary, revenue, loading } = useAnalytics(dateRange);

  if (loading) {
    return <div>Cargando analytics...</div>;
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
        <DateRangeFilter onChange={setDateRange} />
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <KPICard
          title="Ingresos Totales"
          value={summary?.kpis.total_revenue}
          change={summary?.kpis.revenue_change}
          format="currency"
        />
        <KPICard
          title="Citas Completadas"
          value={summary?.kpis.total_appointments}
          change={summary?.kpis.appointments_change}
          format="number"
        />
        <KPICard
          title="Clientes Activos"
          value={summary?.kpis.active_clients}
          format="number"
        />
        <KPICard
          title="Ticket Promedio"
          value={summary?.kpis.average_ticket}
          change={summary?.kpis.ticket_change}
          format="currency"
        />
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RevenueChart data={revenue?.evolution || []} />
        {/* Más gráficos... */}
      </div>
    </div>
  );
}
```

---

## 7. PLAN DE IMPLEMENTACIÓN

### FASE 1: Backend - Analytics Global API (3-4 días)

**Día 1: Setup inicial y endpoints básicos**
- [ ] Crear estructura de views y URLs
- [ ] Implementar `DashboardSummaryView` con KPIs
- [ ] Implementar `RevenueAnalyticsView` con evolución temporal
- [ ] Tests unitarios para cálculos básicos

**Día 2: Endpoints de servicios y productos**
- [ ] Implementar `ServiceAnalyticsView` (top services, rentabilidad)
- [ ] Implementar `ProductAnalyticsView` (top products, rotación)
- [ ] Implementar agregaciones SQL optimizadas
- [ ] Tests de performance

**Día 3: Endpoints de empleados y clientes**
- [ ] Implementar `EmployeePerformanceView`
- [ ] Implementar `ClientAnalyticsView` (segmentación)
- [ ] Implementar `OccupancyAnalyticsView`
- [ ] Implementar `NoShowAnalyticsView`

**Día 4: Caché y optimización**
- [ ] Configurar Redis para caché de queries pesadas
- [ ] Implementar estrategia de caché por endpoint
- [ ] Testing de carga
- [ ] Documentación de API

---

### FASE 2: Backend - Analytics de Cliente Individual (2-3 días)

**Día 1: Endpoints de perfil de cliente**
- [ ] Implementar `ClientSummaryView`
- [ ] Implementar `ClientSpendingView`
- [ ] Implementar cálculos de LTV, frecuencia, estado
- [ ] Tests unitarios

**Día 2: Endpoints de patrones y comportamiento**
- [ ] Implementar `ClientPatternsView` (días, horarios preferidos)
- [ ] Implementar `ClientBehaviorView` (no-shows, fidelización)
- [ ] Implementar `ClientServicesView` (timeline, favoritos)

**Día 3: Sistema de alertas e insights**
- [ ] Implementar `ClientAlertsView`
- [ ] Lógica de detección de riesgos
- [ ] Lógica de oportunidades
- [ ] Insights automáticos

---

### FASE 3: Frontend - Analytics Global Dashboard (3-4 días)

**Día 1: Setup y componentes base**
- [ ] Instalar Recharts
- [ ] Crear componentes reutilizables (LineChart, BarChart, PieChart)
- [ ] Crear `KPICard` component
- [ ] Crear `DateRangeFilter` component

**Día 2: Dashboard principal - KPIs y Revenue**
- [ ] Implementar `AnalyticsPage` layout
- [ ] Implementar sección de KPIs
- [ ] Implementar `RevenueChart`
- [ ] Implementar hook `useAnalytics`

**Día 3: Gráficos de servicios y productos**
- [ ] Implementar `ServicesChart`
- [ ] Implementar `ProductsChart`
- [ ] Implementar tablas de rentabilidad
- [ ] Filtros y búsqueda

**Día 4: Performance de empleados y ocupación**
- [ ] Implementar `EmployeePerformanceChart`
- [ ] Implementar `OccupancyHeatmap`
- [ ] Implementar gráficos de no-shows
- [ ] Testing de integración

---

### FASE 4: Frontend - Analytics de Cliente Individual (3-4 días)

**Día 1: Componentes de perfil de cliente**
- [ ] Crear tab "Analytics" en `ClientDetailPage`
- [ ] Implementar `ClientSummaryCard`
- [ ] Implementar hook `useClientAnalytics`
- [ ] Estado del cliente (badges visuales)

**Día 2: Gráficos de gasto y servicios**
- [ ] Implementar `SpendingChart` (gasto mensual)
- [ ] Implementar gráfico de ticket promedio
- [ ] Implementar distribución servicios vs productos
- [ ] Implementar año a año

**Día 3: Timeline y patrones**
- [ ] Implementar `ServicesTimeline` (historial)
- [ ] Implementar `PatternsChart` (días preferidos)
- [ ] Implementar gráfico de horarios
- [ ] Implementar `ActivityHeatmap`

**Día 4: Alertas e insights**
- [ ] Implementar `AlertsPanel`
- [ ] Diseño de badges y notificaciones
- [ ] Iconografía y colores
- [ ] Testing de UX

---

### FASE 5: Features Avanzadas (2-3 días)

**Día 1: Exportación de reportes**
- [ ] Backend: Implementar generación de PDF con ReportLab
- [ ] Backend: Implementar generación de Excel con openpyxl
- [ ] Frontend: Botones de exportación
- [ ] Testing de formatos

**Día 2: Comparativas y proyecciones**
- [ ] Comparativas año a año
- [ ] Comparativas entre sucursales
- [ ] Proyecciones básicas (forecasting)
- [ ] Tendencias estacionales

**Día 3: Polish y optimización**
- [ ] Optimización de performance
- [ ] Loading states y skeletons
- [ ] Error handling
- [ ] Responsive design
- [ ] Testing end-to-end

---

### FASE 6: Testing y Documentación (1-2 días)

**Testing**
- [ ] Tests unitarios backend (80%+ coverage)
- [ ] Tests de integración
- [ ] Tests E2E con Playwright/Cypress
- [ ] Testing de performance (queries < 500ms)

**Documentación**
- [ ] Documentar endpoints en Swagger
- [ ] Comentarios en código
- [ ] README de analytics
- [ ] Guía de usuario (screenshots)

---

## 8. CONSIDERACIONES DE PERFORMANCE

### 8.1 Optimizaciones de Base de Datos

**Índices Necesarios**
```sql
-- Índices para queries de analytics
CREATE INDEX idx_turno_fecha_estado ON turnos_turno(fecha, estado);
CREATE INDEX idx_turno_cliente_completado ON turnos_turno(cliente_id, estado) WHERE estado = 'COMPLETADO';
CREATE INDEX idx_transaction_fecha_type ON finanzas_transaction(fecha, type);
CREATE INDEX idx_transaction_cliente ON finanzas_transaction(cliente_id);
CREATE INDEX idx_turno_servicio ON turnos_turno(servicio_id, estado);
CREATE INDEX idx_turno_profesional ON turnos_turno(profesional_id, estado);
```

**Queries Optimizadas**
- Usar `select_related()` y `prefetch_related()` para evitar N+1 queries
- Usar `annotate()` y `aggregate()` en lugar de loops en Python
- Usar `values()` para obtener solo campos necesarios
- Limitar resultados con `[:limit]` cuando sea posible

### 8.2 Estrategia de Caché

**Niveles de Caché**

1. **Caché de vista completa** (5-10 minutos)
   - Dashboard summary
   - Analytics global

2. **Caché de cálculos pesados** (15-30 minutos)
   - Top services/products
   - Ocupación histórica

3. **Caché por cliente** (10 minutos)
   - Client summary
   - Client patterns

**Invalidación de Caché**
```python
# Cuando se crea/actualiza un Turno, invalidar caché relacionado
from django.db.models.signals import post_save
from django.core.cache import cache

@receiver(post_save, sender=Turno)
def invalidate_analytics_cache(sender, instance, **kwargs):
    # Invalidar caché de dashboard general
    cache.delete('dashboard_summary')

    # Invalidar caché del cliente específico
    cache.delete(f'client_summary_{instance.cliente_id}')
```

### 8.3 Paginación y Lazy Loading

**Backend**
- Usar `PageNumberPagination` para listas largas
- Limitar resultados por defecto (100-200 items)

**Frontend**
- Lazy loading para gráficos (cargar solo cuando están visibles)
- Infinite scroll para timelines largos
- Skeleton loaders para mejor UX

### 8.4 Archivado de Datos Históricos

Para evitar que las queries se vuelvan lentas con años de datos:

```python
# Opcional: Tabla de Analytics Pre-calculados
class AnalyticsSummaryDaily(models.Model):
    """
    Tabla de resumen diario pre-calculado
    Se calcula con un Celery task cada noche
    """
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    fecha = models.DateField()
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2)
    services_revenue = models.DecimalField(max_digits=10, decimal_places=2)
    products_revenue = models.DecimalField(max_digits=10, decimal_places=2)
    total_appointments = models.IntegerField()
    # ... más métricas

    class Meta:
        unique_together = ['sucursal', 'fecha']
        indexes = [
            models.Index(fields=['sucursal', 'fecha']),
        ]
```

---

## 9. WIREFRAMES Y UX

### 9.1 Dashboard Global - Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Analytics Dashboard                    [Filtro: Últimos 30 días] [Sucursal: Todas] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Ingresos     │  │ Citas        │  │ Clientes     │  │ Ticket       │ │
│  │ $450,000     │  │ 320          │  │ 156          │  │ $1,406       │ │
│  │ ↑ 15.5%      │  │ ↑ 8.2%       │  │ +23 nuevos   │  │ ↑ 6.8%       │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Evolución de Ingresos                                      │ │
│  │  [Gráfico de líneas: Servicios, Productos, Total]          │ │
│  │                                                             │ │
│  │  50K ┤         ╭─╮                                          │ │
│  │  40K ┤      ╭──╯ ╰─╮                                        │ │
│  │  30K ┤   ╭──╯      ╰──╮                                     │ │
│  │  20K ┤╭──╯            ╰─                                    │ │
│  │      └┴────────────────────────────────────────             │ │
│  │       Nov 1    Nov 10    Nov 20    Nov 30                  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────┐  ┌────────────────────────┐        │
│  │ Top 10 Servicios       │  │ Top 10 Productos       │        │
│  │ [Gráfico de barras]    │  │ [Gráfico de barras]    │        │
│  │                        │  │                        │        │
│  └────────────────────────┘  └────────────────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Perfil de Cliente - Analytics Tab

```
┌─────────────────────────────────────────────────────────────────┐
│  María González                           [Tabs: Info | Historial | Analytics] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  💰 Lifetime Value: $125,000    📅 Cliente desde: 15/05/2023 │ │
│  │  🎯 42 visitas totales          📆 Última visita: hace 10 días │ │
│  │  ⭐ Estado: VIP                 📊 Cada 18.5 días en promedio │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  🚨 ALERTAS                                                  │ │
│  │  💚 Cliente VIP - En top 10% de gasto total                 │ │
│  │  💡 Patrón detectado - Siempre viene los jueves             │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Gasto Mensual (Últimos 12 meses)                           │ │
│  │  [Gráfico de barras con línea de tendencia]                 │ │
│  │                                                             │ │
│  │  10K ┤         ┃                                            │ │
│  │   8K ┤      ┃  ┃           ┃                                │ │
│  │   6K ┤   ┃  ┃  ┃     ┃     ┃                                │ │
│  │   4K ┤┃  ┃  ┃  ┃  ┃  ┃  ┃  ┃                                │ │
│  │      └┴──┴──┴──┴──┴──┴──┴──┴──                              │ │
│  │       Ene Feb Mar Abr May Jun Jul Ago                       │ │
│  │       Promedio mensual: $6,500                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌────────────────────────┐  ┌────────────────────────┐        │
│  │ Servicios Favoritos    │  │ Días Preferidos        │        │
│  │ [Pie chart]            │  │ [Gráfico de barras]    │        │
│  │ • Masaje: 40%          │  │ Martes: ████████       │        │
│  │ • Facial: 35%          │  │ Jueves: ████████████   │        │
│  │ • Corporal: 25%        │  │ Viernes: ████          │        │
│  └────────────────────────┘  └────────────────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 9.3 Paleta de Colores

**KPIs y Métricas**
- Verde (#10b981): Métricas positivas, crecimiento
- Rojo (#ef4444): Métricas negativas, decrecimiento
- Azul (#3b82f6): Métricas neutras, valores actuales
- Morado (#8b5cf6): Servicios
- Amarillo/Naranja (#f59e0b): Alertas, advertencias

**Estados de Cliente**
- Verde (#10b981): VIP, Activo
- Amarillo (#f59e0b): En Riesgo
- Gris (#6b7280): Inactivo
- Azul (#3b82f6): Nuevo

**Gráficos**
- Usar paleta consistente entre todos los gráficos
- Máximo 5-6 colores simultáneos para claridad
- Alto contraste para accesibilidad

---

## RESUMEN DE ENTREGABLES

### Backend
- ✅ 15+ endpoints de analytics
- ✅ Agregaciones SQL optimizadas
- ✅ Sistema de caché con Redis
- ✅ Permisos y seguridad
- ✅ Tests con 80%+ coverage

### Frontend
- ✅ Dashboard principal completo
- ✅ 20+ componentes de visualización
- ✅ Perfil analítico de cliente
- ✅ Sistema de alertas e insights
- ✅ Responsive design

### Documentación
- ✅ Especificación técnica (este documento)
- ✅ Documentación de API (Swagger)
- ✅ Guía de usuario

### Performance
- ✅ Queries < 500ms
- ✅ Caché estratégico
- ✅ Índices de BD optimizados

---

## PRÓXIMOS PASOS

1. **Revisar y aprobar** esta especificación
2. **Comenzar con Fase 1**: Backend Analytics Global API
3. **Iteraciones semanales** con demos
4. **Feedback continuo** del usuario/cliente piloto
5. **Deploy gradual** por fases

---

**Documento creado**: Diciembre 2025
**Última actualización**: Diciembre 8, 2025
**Versión**: 1.0
