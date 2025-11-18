# Estrategia de Pricing - Plataforma Estética SaaS

## Análisis de Mercado (2025)

### Competencia Directa - Argentina/LATAM

| Software | Precio Mensual | Mercado | Características Principales |
|----------|---------------|---------|----------------------------|
| **AgendaPro** | $30 USD | LATAM | Agenda, CRM básico, notificaciones |
| **Software español** | €29.90 (~$32 USD) | España | Gestión básica de citas |
| **Software local ARG** | ~$25-35 USD | Argentina | Funcionalidades limitadas |

### Competencia Internacional - Salones

| Categoría | Rango de Precio | Ejemplos |
|-----------|----------------|----------|
| **Budget** | $24-30/mes | GlossGenius ($24), Vagaro ($30) |
| **Mid-Range** | $60-165/mes | Timely ($60-240), Mangomint ($165-375) |
| **Premium** | $159-410/mes | Mindbody ($159-699), Boulevard ($176-410) |

### Benchmarks E-commerce SaaS

| Plataforma | Plan Básico | Plan Profesional | Plan Premium |
|------------|-------------|------------------|--------------|
| **Tiendanube** (ARG) | $0 ARS | $21.499 ARS (~$21 USD) | $59.999 ARS (~$60 USD) |
| **Shopify** | $19 USD | $52 USD | $399 USD |

---

## Análisis de Valor de Nuestra Plataforma

### ✅ Características Completas

**Módulo Admin:**
1. ✅ Gestión de turnos con calendario visual
2. ✅ Prevención de double-booking (crítico)
3. ✅ CRM completo de clientes (historial, fotos, notas)
4. ✅ Catálogo de servicios con categorías
5. ✅ Inventario con control de stock y alertas
6. ✅ **Sistema financiero** (ingresos, gastos, flujo de caja)
7. ✅ **WhatsApp automatizado** (confirmación, recordatorios, cancelaciones)
8. ✅ Sistema de comisiones para empleados
9. ✅ Multi-sucursal
10. ✅ Analytics y reportes
11. ✅ 3 roles (Admin, Manager, Empleado)

**Módulo Client App:**
12. ✅ Portal de clientes con reserva online
13. ✅ Disponibilidad en tiempo real
14. ✅ E-commerce de productos
15. ✅ White-label completo (dominio propio, colores, logos)
16. ✅ Gestión de pedidos
17. ✅ Integración de pagos (MercadoPago/MODO)

### 🔥 Diferenciadores Clave vs Competencia

| Feature | Nuestra Plataforma | AgendaPro | Otros |
|---------|-------------------|-----------|-------|
| WhatsApp Automatizado | ✅ Incluido | ❌ Extra | ❌ No |
| Sistema Financiero | ✅ Completo | ⚠️ Básico | ❌ No |
| E-commerce Productos | ✅ Incluido | ❌ No | ❌ No |
| Client App | ✅ White-label | ⚠️ Genérica | ❌ No |
| Inventario | ✅ Completo | ⚠️ Básico | ⚠️ Limitado |
| Multi-sucursal | ✅ Incluido | 💰 Extra | 💰 Extra |
| Comisiones | ✅ Automatizado | ❌ Manual | ❌ No |

**Valor agregado estimado:** 2-3x más completo que AgendaPro básico

---

## Costos de Operación (COGS por Centro)

### Infraestructura

```
Hosting (AWS/DigitalOcean):
- Backend + DB:              $3-5 USD/mes por centro
- Frontend (CDN):            $0.50 USD/mes
- Redis:                     $1 USD/mes
Subtotal infraestructura:    ~$5 USD/mes

Servicios externos:
- WhatsApp (Twilio):         $2-10 USD/mes (según volumen)
  * ~500 mensajes/mes = $2.50
  * 1000 mensajes/mes = $5
- Storage (S3/Cloudinary):   $1-2 USD/mes
- Email (SendGrid):          $0-1 USD/mes (hasta 40k/mes gratis)
Subtotal servicios:          ~$4-13 USD/mes

Soporte y overhead:
- Soporte técnico:           ~$2-3 USD/mes (prorrateado)
- Monitoring (Sentry):       $0.50 USD/mes

COGS Total por centro:       $11-21 USD/mes
Promedio:                    ~$15 USD/mes
```

### Economía Unitaria

**Escenario Conservador:**
- Precio: $40 USD/mes
- COGS: $15 USD/mes
- **Margen bruto: $25 USD (62.5%)**
- Target de margen SaaS: 70-80% ✅

**Escenario Optimista (volumen):**
- Precio: $50 USD/mes
- COGS: $12 USD/mes (economías de escala)
- **Margen bruto: $38 USD (76%)**

---

## Estrategia de Pricing Recomendada

### Modelo: Pricing por Tiers (3 planes)

#### 🥉 **Plan BÁSICO** - $29 USD/mes

**Target:** Centros pequeños (1 sucursal, 1-3 empleados)

**Incluye:**
- ✅ 1 sucursal
- ✅ Hasta 3 usuarios
- ✅ Gestión de turnos ilimitados
- ✅ CRM de clientes
- ✅ Servicios e inventario básico
- ✅ WhatsApp: 300 mensajes/mes
- ✅ Reportes básicos
- ❌ No incluye: Client App, e-commerce, multi-sucursal

**Margen:** 48% (COGS $15)

---

#### ⭐ **Plan PROFESIONAL** - $49 USD/mes (RECOMENDADO)

**Target:** Centros medianos (1-3 sucursales, 4-10 empleados)

**Incluye TODO del Básico +**
- ✅ Hasta 3 sucursales
- ✅ Usuarios ilimitados
- ✅ Sistema financiero completo
- ✅ Comisiones automatizadas
- ✅ Analytics avanzado
- ✅ **Client App white-label**
- ✅ **E-commerce de productos**
- ✅ WhatsApp: 1000 mensajes/mes
- ✅ Subdominio personalizado (centro.plataforma.com)
- ✅ Integración pagos (MercadoPago/MODO)
- ✅ Soporte prioritario

**Margen:** 69% (COGS $15)

**🎯 Este es el plan con mejor relación precio/valor**

---

#### 💎 **Plan ENTERPRISE** - $99 USD/mes

**Target:** Centros grandes o cadenas (4+ sucursales, 10+ empleados)

**Incluye TODO del Profesional +**
- ✅ Sucursales ilimitadas
- ✅ WhatsApp: mensajes ilimitados
- ✅ Dominio personalizado propio (www.micentro.com)
- ✅ CSS/Scripts custom
- ✅ API access para integraciones
- ✅ Reportes personalizados
- ✅ Soporte dedicado (WhatsApp directo)
- ✅ Onboarding personalizado
- ✅ Training para empleados
- ✅ SLA 99.9% uptime

**Margen:** 85% (COGS $15)

---

### Tabla Comparativa Completa

| Feature | Básico<br>$29/mes | Profesional<br>$49/mes | Enterprise<br>$99/mes |
|---------|----------|--------------|-----------|
| **Sucursales** | 1 | 3 | Ilimitadas |
| **Usuarios** | 3 | Ilimitados | Ilimitados |
| **Turnos** | ✅ | ✅ | ✅ |
| **CRM Clientes** | ✅ | ✅ | ✅ |
| **Inventario** | ✅ | ✅ | ✅ |
| **Sistema Financiero** | ❌ | ✅ | ✅ |
| **Comisiones** | ❌ | ✅ | ✅ |
| **Analytics** | Básico | Avanzado | Personalizado |
| **Client App** | ❌ | ✅ White-label | ✅ White-label |
| **E-commerce** | ❌ | ✅ | ✅ |
| **WhatsApp** | 300 msg/mes | 1000 msg/mes | Ilimitado |
| **Dominio** | Subdominio | Subdominio | Propio |
| **API Access** | ❌ | ❌ | ✅ |
| **Soporte** | Email | Prioritario | Dedicado |
| **Custom Code** | ❌ | ❌ | ✅ CSS/JS |

---

## Estrategias de Adopción

### 1. Trial Gratuito

```
Trial de 30 días del Plan Profesional
- Acceso completo a todas las funciones
- No requiere tarjeta de crédito
- Onboarding guiado
- 3 llamadas de soporte incluidas

Conversión esperada: 15-25%
```

### 2. Descuentos por Pago Anual

```
Plan Profesional:
- Mensual: $49 USD
- Anual: $470 USD ($39.16/mes) → 20% descuento ✅

Plan Enterprise:
- Mensual: $99 USD
- Anual: $950 USD ($79.16/mes) → 20% descuento ✅

Ventajas:
- Mejor cash flow
- Menor churn
- Commitment del cliente
```

### 3. Programa de Referidos

```
Centro refiere → Nuevo centro se suscribe
- Referidor recibe: 1 mes gratis
- Nuevo cliente recibe: 10% descuento primer año

Costo de adquisición reducido
Crecimiento orgánico
```

### 4. Pricing Regional (Argentina)

**Opción A: Facturación en Pesos (Recomendado)**
```
Plan Profesional: $49 USD
Conversión a pesos al tipo de cambio + 5%

Ejemplo (TC = 1000):
$49 USD × 1000 × 1.05 = $51.450 ARS/mes

Ventajas:
- Menor fricción (pago en moneda local)
- Competitivo vs AgendaPro
- Ajustes mensuales por inflación
```

**Opción B: Facturación en USD con pago en pesos**
```
Precio fijo en USD, conversión al momento del pago
Más predecible para el negocio
```

---

## Proyección de Revenue

### Escenario Conservador (12 meses)

| Mes | Clientes | MRR | ARR |
|-----|----------|-----|-----|
| 3 | 5 | $245 | $2,940 |
| 6 | 15 | $735 | $8,820 |
| 9 | 30 | $1,470 | $17,640 |
| 12 | 50 | $2,450 | $29,400 |

**Asumiendo:**
- 60% Plan Profesional ($49)
- 30% Plan Básico ($29)
- 10% Plan Enterprise ($99)
- MRR promedio: ~$49

### Escenario Optimista (12 meses)

| Mes | Clientes | MRR | ARR |
|-----|----------|-----|-----|
| 6 | 30 | $1,470 | $17,640 |
| 12 | 100 | $4,900 | $58,800 |
| 18 | 250 | $12,250 | $147,000 |
| 24 | 500 | $24,500 | $294,000 |

**Con 500 clientes:**
- Revenue mensual: $24,500 USD
- COGS: $7,500 USD (500 × $15)
- **Profit bruto: $17,000 USD/mes** (69% margen)

---

## Análisis Competitivo de Precio

### Posicionamiento en el Mercado

```
Budget Tier ($20-30):
- Funcionalidades limitadas
- Solo agenda básica
- Sin client app
[Nuestra opción: Plan Básico $29]

Value Tier ($40-60):  ← AQUÍ NOS POSICIONAMOS
- Funcionalidades completas
- Client app incluida
- E-commerce
- WhatsApp automatizado
[Nuestra opción: Plan Profesional $49]

Premium Tier ($100-400):
- Enterprise features
- Soporte dedicado
- Customización
[Nuestra opción: Plan Enterprise $99]
```

**Nuestra ventaja:** Ofrecemos features de $100+ en el plan de $49

### Value Proposition por Dólar

**AgendaPro ($30/mes):**
- Agenda ✅
- CRM básico ✅
- WhatsApp ❌ (extra)
- Finanzas ⚠️ (limitado)
- Client App ❌
- E-commerce ❌

**Nuestra Plataforma ($49/mes):**
- Agenda ✅
- CRM completo ✅
- WhatsApp ✅ (incluido)
- Finanzas ✅ (completo)
- Client App ✅ (white-label)
- E-commerce ✅ (incluido)
- Inventario ✅
- Comisiones ✅

**ROI para el cliente:**
```
Sin plataforma (manual):
- Pérdida por no-shows: ~$500/mes
- Tiempo admin manual: 40hs/mes × $10/h = $400/mes
- Pérdida de ventas online: $200/mes
Total pérdida: ~$1,100/mes

Con nuestra plataforma ($49/mes):
- Reducción no-shows 40%: ahorro $200/mes
- Automatización: ahorro $300/mes
- Ventas online: +$300/mes
**ROI: 16x** ($800 beneficio vs $49 costo)
```

---

## Estrategia de Lanzamiento

### Fase 1: Early Adopters (Primeros 20 clientes)

**Pricing Especial:**
- Plan Profesional: $29 USD/mes (precio Beta)
- Locked-in por 12 meses
- Acceso de por vida a ese precio (grandfathered)

**A cambio:**
- Feedback activo
- Testimonios
- Casos de estudio
- Tolerancia a bugs iniciales

**Beneficio:**
- Validación rápida
- Referencias tempranas
- Revenue inmediato

### Fase 2: Launch Público (Mes 4-12)

**Pricing Normal:**
- Básico: $29
- Profesional: $49
- Enterprise: $99

**Promoción de lanzamiento:**
- 2 meses gratis en plan anual
- 50% descuento primer mes

### Fase 3: Optimización (Mes 12+)

**Ajustes basados en:**
- Churn rate por plan
- Features más usadas
- Feedback de clientes
- Análisis de competencia

**Posible ajuste:**
- Profesional: $49 → $59
- Enterprise: $99 → $129
- (Clientes existentes mantienen precio)

---

## Métricas Clave a Monitorear

### Unit Economics
- **CAC** (Customer Acquisition Cost): Target < $150
- **LTV** (Lifetime Value): Target > $1,200 (24+ meses)
- **LTV/CAC Ratio**: Target > 3:1
- **Payback Period**: Target < 6 meses

### SaaS Metrics
- **MRR** (Monthly Recurring Revenue)
- **Churn Rate**: Target < 5%/mes
- **Expansion Revenue**: Upsells Basic → Pro
- **Net Revenue Retention**: Target > 100%

### Pricing Optimization
- % de clientes por plan
- Features más/menos usadas
- Razones de cancelación
- Willingness to pay surveys

---

## Recomendación Final

### 🎯 Precio Óptimo de Lanzamiento

**Plan PROFESIONAL: $49 USD/mes**

**Por qué:**
1. ✅ **Competitivo:** AgendaPro $30 tiene 40% menos features
2. ✅ **Margen saludable:** 69% permite inversión en crecimiento
3. ✅ **Value proposition claro:** Client app + e-commerce + WhatsApp incluido
4. ✅ **Psicología:** Precio "medio" atrae más que extremos
5. ✅ **Escalabilidad:** Permite upsell a Enterprise ($99)
6. ✅ **ROI evidente:** Cliente ahorra/gana 10x más que el costo

### Pricing Completo

```
✨ TRIAL: 30 días gratis (Plan Profesional completo)

📦 BÁSICO: $29/mes
   Para centros pequeños (1 sucursal)

⭐ PROFESIONAL: $49/mes ← RECOMENDADO
   Para centros medianos (hasta 3 sucursales)
   Incluye: Client App + E-commerce + WhatsApp

💎 ENTERPRISE: $99/mes
   Para cadenas y centros grandes
   Incluye: Todo + Soporte dedicado

💰 DESCUENTO ANUAL: 20% off
   Profesional: $470/año ($39/mes efectivo)
```

### Facturación para Argentina

**Opción recomendada:**
- Precio en USD (estabilidad)
- Pago en ARS (conveniencia)
- Actualización mensual del tipo de cambio
- Opción de pago anual en USD (descuento)

---

## Comparación con Alternativas del Cliente

### Opción 1: Desarrollo a Medida
**Costo:** $10,000 - $30,000 USD iniciales + $500/mes mantenimiento
**Tiempo:** 6-12 meses
**Riesgo:** Alto

### Opción 2: Software Genérico (Excel + WhatsApp manual)
**Costo:** "Gratis" pero ineficiente
**Pérdidas:** ~$1,000/mes en tiempo y oportunidades perdidas

### Opción 3: Nuestra Plataforma SaaS
**Costo:** $49/mes = $588/año
**Tiempo:** Implementación en 1 día
**ROI:** 16x en el primer año
**Riesgo:** Bajo (trial de 30 días)

---

**Conclusión:** Un centro mediano que paga $49/mes obtiene un sistema que costaría $15,000+ desarrollar y $500/mes mantener, con ROI comprobado de 16x.

**Última actualización:** 17 de Noviembre 2025
