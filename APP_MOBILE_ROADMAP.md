# App Mobile Cliente - Roadmap de Implementación

**Fecha de creación**: Abril 2026
**Estado**: Planificación
**Supersedes parcialmente**: `CLIENTE_APP_ROADMAP.md` (web app, estrategia diferente)

---

## 1. Contexto estratégico

### El problema de negocio real

El centro de estética AME (cliente piloto) tiene dos problemas:

1. **Dificultad de adquisición** — pocos clientes nuevos entran al funnel
2. **Baja conversión a servicios** — poca gente contrata los servicios ofrecidos
3. **Fuente principal de ingresos**: venta de productos (no servicios)

### Qué resuelve la app (y qué no)

| Problema | ¿Lo resuelve la app? |
|----------|----------------------|
| Adquirir clientes nuevos | ❌ No — eso lo resuelven Instagram/TikTok, ads, referidos |
| Retener clientes existentes | ✅ Sí — via fidelidad y recompra predictiva |
| Cross-sell producto → servicio | ✅ Sí — via push segmentado contextual |
| Aumentar ticket promedio y frecuencia | ✅ Sí — via rutinas y recompra |

**Decisión de producto**: la app NO es una "app de reservas con productos al lado". Es una **app de fidelidad y e-commerce con servicios como extensión**. Reservas es secundaria.

### Features core (en orden de prioridad)

1. **Motor de recompra predictiva** — push cuando el producto se está por terminar
2. **E-commerce** — catálogo, carrito, checkout con productos de REVENTA
3. **Programa de puntos y fidelidad** — acumulación en cada compra/servicio, canjeables
4. **Rutina de cuidado personalizada** — editable por la esteticista, visible al cliente
5. **Referidos** — código único, beneficio para ambas partes
6. **Push segmentados** — cross-sell producto → servicio
7. **Feed de contenido** — antes/después, tips, ofertas rotativas
8. **Reserva de turnos** — flujo básico, no el foco principal

---

## 2. Stack técnico

### Mobile (Expo + React Native)

| Capa | Librería | Rol |
|------|----------|-----|
| Framework | **Expo SDK 52+** | Builds, OTA, EAS |
| Lenguaje | TypeScript | Tipos compartidos con admin |
| Routing | Expo Router v4 | File-based, deep linking |
| Estilos | NativeWind v4 | Tailwind en RN |
| Animaciones | Reanimated 3 + Moti | 60fps en UI thread |
| Gestos | React Native Gesture Handler | Nativo, sin bridge |
| Efectos visuales | React Native Skia | Blurs, gradientes premium |
| Estado servidor | TanStack Query | Cache + refetch |
| Estado global | Zustand | Auth, carrito |
| Forms | React Hook Form + Zod | Validación tipada |
| Imágenes | Expo Image | Cache + blur hash |
| Fuentes | expo-font (Inter + Fraunces display) | Look premium |
| Bottom sheets | @gorhom/bottom-sheet | UX moderna |
| Haptics | expo-haptics | Feedback táctil en acciones clave |
| Push | expo-notifications | APNs + FCM unificado |
| Pagos | MercadoPago Checkout Pro (WebView) | MVP — evita KYC nativo |
| Errores | Sentry | Crash reporting |
| Analytics | PostHog | Embudos, retention, feature flags |

### Backend (extensiones sobre Django existente)

| Qué agregar | Ubicación | Rol |
|-------------|-----------|-----|
| App `public_api` | `backend/apps/public_api/` | Endpoints sin auth (info centro, catálogo público) |
| App `client_api` | `backend/apps/client_api/` | Endpoints para clientes autenticados |
| App `fidelidad` | `backend/apps/fidelidad/` | Puntos, canjes, referidos |
| App `rutinas` | `backend/apps/rutinas/` | Rutinas de cuidado personalizadas |
| Extensiones a `Producto` | Modelo existente | `duracion_estimada_dias`, `pao_meses`, `contenido_ml`, `frecuencia_uso` |
| Modelo `UsuarioCliente` | `backend/apps/clientes/` | Auth separada del `Usuario` (staff) |
| Modelo `VinculacionCliente` | `backend/apps/clientes/` | M2M entre `UsuarioCliente` y `Cliente` |
| Modelo `CodigoInvitacion` | `backend/apps/clientes/` | Códigos únicos para vinculación privada |
| Job Celery `predecir_recompras` | `backend/apps/fidelidad/tasks.py` | Cálculo diario + disparo de push |
| Expo Push integration | `backend/apps/notificaciones/push.py` | Envío multi-plataforma |

### Infraestructura

| Qué | Servicio |
|-----|----------|
| Builds mobile | EAS Build |
| Distribución beta | EAS Submit → TestFlight + Google Internal Testing |
| APK preview para testers | EAS Build profile `preview` |
| OTA Updates | `expo-updates` + `eas update` |
| Backend hosting | Render/Railway (MVP) → AWS/DigitalOcean (escala) |
| CDN imágenes | Cloudinary o S3 + CloudFront |
| Push tokens | Expo Push Service |
| CI/CD | GitHub Actions |

---

## 3. Sistema de vinculación de cuentas (crítico)

El desafío: María Rivaldo ya existe como `Cliente` en la DB (creada por staff). Cuando baja la app, ¿cómo sabemos que ella es esa María? **Sin pedir teléfono** (decisión de privacidad) y **sin exponer datos a impostores**.

### Solución: sistema de códigos de invitación

**Flujo principal (iniciado por staff)**:

1. Cliente visita el centro (ej: María viene a AME Banfield)
2. Staff abre la ficha de María en el admin → botón **"Invitar a la app"**
3. Sistema genera un **código único** (ej: `AME-7H3K-9M2X`) válido 72hs
4. Staff se lo entrega: WhatsApp, email, ticket impreso, o decírselo verbalmente
5. María baja la app → escanea QR del mostrador (identifica centro) → ingresa código
6. Sistema valida código → linkea `UsuarioCliente` nueva a `Cliente` existente
7. María crea password → acceso completo a su historial, rutina, puntos

**Flujo alternativo (auto-registro)**:

Para clientes nuevos que bajan la app sin haber sido invitados:

1. Escanean QR o buscan centro
2. Registro con email + password (sin vinculación a Cliente existente)
3. Sistema crea `Cliente` nuevo + `UsuarioCliente`
4. Si en una visita futura se descubre que ya tenían registro previo, staff usa UI de consolidación

**Ventajas del sistema de códigos**:

- ✅ Totalmente privado: no se piden teléfonos
- ✅ Seguro: el código es un secreto que solo el cliente recibe
- ✅ Controlado: staff decide quién recibe invitación
- ✅ Auditable: cada código tiene origen y fecha

### Modelos a agregar

```python
# apps/clientes/models.py

class UsuarioCliente(AbstractBaseUser):
    email = models.EmailField(unique=True)
    password = models.CharField(...)
    email_verificado = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    ultimo_login = models.DateTimeField(null=True)
    push_token = models.CharField(max_length=255, null=True, blank=True)

class VinculacionCliente(models.Model):
    usuario_cliente = models.ForeignKey(UsuarioCliente, on_delete=CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=CASCADE)
    metodo_vinculacion = models.CharField(choices=[
        ('CODIGO_INVITACION', 'Código de invitación'),
        ('INVITACION_STAFF', 'Invitación manual por staff'),
        ('REGISTRO_NUEVO', 'Registro como cliente nuevo'),
        ('MERGE_MANUAL', 'Consolidación manual'),
    ])
    vinculado_en = models.DateTimeField(auto_now_add=True)
    vinculado_por = models.ForeignKey('Usuario', null=True, blank=True)

    class Meta:
        unique_together = [('usuario_cliente', 'cliente')]

class CodigoInvitacion(models.Model):
    codigo = models.CharField(max_length=16, unique=True, db_index=True)
    cliente = models.ForeignKey(Cliente, on_delete=CASCADE)
    generado_por = models.ForeignKey('Usuario', on_delete=SET_NULL, null=True)
    generado_en = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField()
    usado_en = models.DateTimeField(null=True, blank=True)
    usado_por = models.ForeignKey(UsuarioCliente, null=True, blank=True)
```

### Cambios en UI del admin

- En `ClientesPage.tsx`: badge de estado ("App activa" / "Sin app" / "Invitación pendiente")
- Botón "Invitar a la app" en ficha del cliente
- Lista de invitaciones generadas con estado
- UI de consolidación de duplicados (detección + merge)

---

## 4. Roadmap por fases

### ⚠️ Fase 0 — Validación sin app (2-3 semanas) — NO SALTEAR

Implementar sobre el admin existente las palancas baratas para medir si hay señal real antes de invertir en la app.

**Objetivos**:
- Confirmar que hay retención real posible
- Limpiar datos de clientes (dedup, normalización)
- Validar hipótesis de cross-sell

**Entregables**:

- [ ] Campañas WhatsApp segmentadas en admin
  - Segmentos: "compró producto X hace 60+ días", "no vino en 90 días", "alto LTV"
  - Trigger manual desde admin
- [ ] Programa de referidos básico
  - Código único por cliente
  - Descuento automático al nuevo cliente + beneficio al referidor
  - Dashboard de referidos activos
- [ ] Trigger post-compra de producto
  - WhatsApp automático día 7 post-compra con tip + invitación a consulta
  - Celery task + template
- [ ] Pedido automático de reseña Google post-servicio
  - WhatsApp 24hs post-servicio con link a Google Business
- [ ] Limpieza de base de datos de clientes
  - Normalizar teléfonos con librería `phonenumbers`
  - Detector de duplicados (mismo tel + nombre similar)
  - UI de merge en admin

**Criterio de éxito**:
- Recompra de productos +20% en 60 días
- Tasa de referidos > 5% de clientes activos
- Reseñas Google +50%

**Si no hay señal en Fase 0, la app no va a resolver el problema — hay que trabajar adquisición primero.**

---

### Fase 1 — Fundaciones de backend (2 semanas)

**Objetivo**: preparar la infraestructura para que la app pueda existir.

- [ ] Crear app `public_api`
  - `GET /api/public/centros/<id>/info/`
  - `GET /api/public/centros/<id>/servicios/`
  - `GET /api/public/centros/<id>/productos/` (solo REVENTA activos)
  - Rate limiting (100/hour anon)
- [ ] Crear app `client_api`
  - Autenticación JWT separada (no mezclar con Usuario staff)
  - `POST /api/client/auth/registro/`
  - `POST /api/client/auth/login/`
  - `POST /api/client/auth/refresh/`
  - `GET /api/client/perfil/`
- [ ] Modelos de vinculación
  - `UsuarioCliente`, `VinculacionCliente`, `CodigoInvitacion`
  - Migraciones
  - Tests de vinculación
- [ ] Extensiones a `Producto`
  - `duracion_estimada_dias` (int, null)
  - `pao_meses` (int, null, "Period After Opening")
  - `contenido_ml` (decimal, null)
  - `frecuencia_uso` (choices: DIARIO, SEMANAL, OCASIONAL)
- [ ] Integración Expo Push
  - Wrapper en `apps/notificaciones/push.py`
  - Endpoint `POST /api/client/push/register/` para guardar token
  - Test de envío
- [ ] UI admin: "Invitar a la app"
  - Botón en ficha de cliente
  - Generación de código
  - Listado de invitaciones

**Tests**:
- pytest para endpoints nuevos
- Tests de vinculación (código válido, expirado, ya usado)
- Tests de multi-tenancy (no leak entre centros)

---

### Fase 2 — Mobile MVP (4 semanas)

**Objetivo**: primera versión funcional de la app con e-commerce y auth.

**Semana 1 — Setup y sistema de diseño**
- [ ] Crear proyecto Expo (`client-app/`)
- [ ] Configurar Expo Router, NativeWind, Reanimated, Sentry
- [ ] Figma: sistema de diseño (colores, tipografía, espaciado, componentes base)
- [ ] Componentes UI base: Button, Input, Card, Modal, BottomSheet
- [ ] Estructura de navegación (tabs + stacks)

**Semana 2 — Auth y onboarding**
- [ ] Pantalla de bienvenida con QR scanner
- [ ] Flujo de registro con código de invitación
- [ ] Flujo de registro como cliente nuevo
- [ ] Login / recuperar password
- [ ] Context/store de auth (Zustand)
- [ ] Integración con API

**Semana 3 — Home y e-commerce**
- [ ] Home: productos destacados + accesos rápidos
- [ ] Catálogo con filtros
- [ ] Detalle de producto con imágenes
- [ ] Carrito (persistente con AsyncStorage)
- [ ] Checkout con MercadoPago WebView
- [ ] Confirmación de orden

**Semana 4 — Perfil y reservas básicas**
- [ ] Mi perfil + editar datos
- [ ] Historial de compras
- [ ] Mis turnos (listado básico)
- [ ] Reservar turno (flujo simple, sin foco)
- [ ] Configuración (notificaciones on/off, logout)

**Entregable**: APK preview distribuible a 5-10 beta testers del centro AME Banfield.

---

### Fase 3 — Motor de recompra y fidelidad (3 semanas)

**Objetivo**: el diferencial real que justifica la app.

**Semana 1 — Motor de recompra**
- [ ] Algoritmo de predicción en backend
  - Fórmula: `fecha_push = fecha_compra + duracion_estimada - 7 dias`
  - Ajuste por histórico real del cliente (promedio móvil)
- [ ] Celery beat diario que calcula próximas recompras
- [ ] Push automatizado con deep link al producto
- [ ] Screen "Mi próxima recompra" en la app

**Semana 2 — Fidelidad**
- [ ] Modelo `Puntos` con historial de acumulación y canjes
- [ ] Reglas configurables en admin (ej: 1 punto por cada $100)
- [ ] Pantalla de puntos en la app con progreso visual
- [ ] Canje al checkout (aplicar puntos como descuento)
- [ ] Notificaciones de acumulación ("ganaste 50 puntos")

**Semana 3 — Referidos**
- [ ] Integración con sistema de referidos de Fase 0
- [ ] Pantalla "Invitar amigas" con código único
- [ ] Share vía WhatsApp/Instagram stories
- [ ] Tracking: quién refirió a quién, cuántas convirtieron
- [ ] Dashboard de referidos en admin

---

### Fase 4 — Cross-sell, contenido y pulido (2 semanas)

**Objetivo**: features que elevan engagement y conversión a servicios.

- [ ] App de `rutinas`
  - Modelo `RutinaCuidado` y `PasoRutina`
  - UI admin para que esteticista arme rutina post-servicio
  - Pantalla en app con pasos, productos, frecuencia
  - Recordatorios opcionales
- [ ] Push segmentados producto → servicio
  - Ejemplo: "compraste sérum anti-edad hace 14 días → probá radiofrecuencia, 30% off primera sesión"
  - Editor de campañas en admin
- [ ] Feed de contenido
  - Antes/después (consentimiento previo del cliente)
  - Tips editados por staff
  - Ofertas rotativas destacadas
- [ ] Valoraciones de servicios
  - Rating 1-5 + comentario opcional
  - Trigger post-servicio
- [ ] Onboarding mejorado
  - Tutorial interactivo primera vez
  - Empty states con ilustraciones Lottie
- [ ] Performance optimization
  - Imágenes con blur hash
  - Prefetch de rutas comunes
  - Reducir bundle size

---

## 5. Estrategia de testing

### Por qué testear estas cosas específicas

| Riesgo | Severidad | Capa de testing |
|--------|-----------|-----------------|
| Double-booking en reservas | Alta | Integration + E2E |
| Pagos fallidos o duplicados | Alta | Sandbox exhaustivo + E2E |
| Vinculación errónea de cuentas (María ve datos de otra María) | **Crítica** | Tests de seguridad + E2E |
| Predicción de recompra errónea | Media | Unit con edge cases |
| Push notifications no llegan | Media | Manual + métricas prod |
| Crashes | Alta | Sentry en prod, crash-free rate > 99.5% |

### Capas

**1. Unit tests — Jest + React Native Testing Library**
- Funciones puras: predicción de recompra, cálculo de descuentos, puntos
- Hooks: `useCart`, `useReplenishment`, `useAuth`
- Componentes aislados

**2. Integration tests — RNTL + MSW**
- Flujos completos con API mockeada: login, compra, canje de puntos

**3. E2E tests — Maestro**
- Flujos críticos en builds reales EAS
- Frecuencia: por PR + nightly en staging

**4. Backend tests — pytest**
- Cobertura mínima 70% en apps nuevas
- Tests específicos de multi-tenancy (no leak entre centros)
- Tests de vinculación de cuentas (código válido, expirado, ya usado, de otro centro)

**5. Visual regression — Storybook + Chromatic**
- Screenshot testing por componente
- Cubre dark mode, tamaños de texto, estados

**6. Manual QA**
- Matriz: iPhone SE, iPhone 15 Pro, Android gama baja (Samsung A-series), Pixel
- Escenarios: 3G lento, offline, sin permisos
- Accesibilidad: VoiceOver, contraste, tamaños dinámicos

**7. Pagos**
- Sandbox MercadoPago obligatorio
- Casos: éxito, rechazo, pendiente, timeout, webhook duplicado
- Regla: confirmar orden solo cuando llega el webhook, nunca en el callback del cliente

**8. Push**
- Expo Push tool manual en dev
- Deep links tap → navegación correcta
- Métricas prod: % enviados vs entregados vs abiertos

### CI/CD

- **PR**: lint + typecheck + unit + integration
- **Merge a develop**: EAS Build preview + Maestro en device virtual
- **Merge a main**: EAS Build production + submit a TestFlight/Internal Testing
- **Feature flags** con PostHog para rollout gradual
- **Staged rollout** en Play Store: 10% → 50% → 100% según crash-free rate

---

## 6. Build y distribución (APK)

### Generación de APK para testers

**Setup inicial**:
```bash
npm install -g eas-cli
eas login
cd client-app
eas build:configure
```

**eas.json** (perfiles clave):
```json
{
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "android": { "buildType": "apk" }
    },
    "preview": {
      "distribution": "internal",
      "android": { "buildType": "apk" }
    },
    "production": {
      "android": { "buildType": "app-bundle" },
      "autoIncrement": true
    }
  }
}
```

**Generar APK para beta testers**:
```bash
eas build --platform android --profile preview
```

**Distribución**:
- Fase 2 (5-10 testers): link directo del dashboard EAS, compartir por WhatsApp
- Fase 3+ (10-50 testers): Google Play Internal Testing (requiere `.aab`)
- Producción: Google Play Store (`production` profile)

**OTA Updates** con `expo-updates`:
```bash
eas update --branch preview  # para fixes sin rebuild
```

### Costos EAS

- **Free**: 30 builds Android/mes — alcanza para Fase 1-2
- **Production** ($29/mes): ilimitado + cola prioritaria — desde Fase 3 conviene

---

## 7. Decisiones pendientes antes de arrancar

Estas definiciones cambian arquitectura, resolverlas con el cliente antes de código:

1. **¿Fase 0 sí o no?**
   - Recomendación fuerte: sí
   - Si no, arrancar directo en Fase 1 — pero asumir riesgo de construir sobre problema no validado

2. **Identidad multi-centro**
   - ¿`UsuarioCliente` puede pertenecer a múltiples centros o uno solo?
   - Recomendación: M2M (Argentina/LatAm es común ser cliente de varios spas)

3. **Centro piloto**
   - ¿AME Banfield es definitivo? ¿Hay acuerdo con el dueño?
   - Necesitamos datos reales para diseñar sistema de puntos y rutinas

4. **Política de seña para turnos online**
   - ¿Reserva libre o seña obligatoria?
   - Impacto directo en no-shows

5. **Diseñador de producto**
   - ¿Contratamos diseñador freelance 2 semanas para sistema en Figma?
   - Muy recomendable — app de belleza sin diseño premium fracasa

6. **Gateway de pago definitivo**
   - Roadmap dice: MercadoPago primero, MODO después
   - Confirmar con cliente modelo: ¿cuenta del centro o plataforma?

---

## 8. Riesgos principales

| Riesgo | Mitigación |
|--------|-----------|
| Adopción baja (clientes no descargan la app) | Fase 0 valida retención antes; staff invita activamente |
| Datos sucios en base de clientes rompen vinculación | Limpieza en Fase 0, UI de merge en admin |
| Filtración de datos entre clientes por bug de multi-tenancy | Tests específicos + code review enfocado |
| Performance pobre en Android gama baja | Testing temprano en device real + optimizaciones |
| Costo de infra crece sin ingresos (pre-PMF) | Empezar con free tiers, escalar solo cuando haya retención demostrada |
| Staff del centro no invita a la app (proceso manual) | Incentivar: dashboard con métrica de invitaciones por empleado |
| Contenido (antes/después) requiere consentimiento legal | Checkbox explícito en ficha de cliente + consentimiento firmado |

---

## 9. KPIs para medir éxito

### Adopción
- % de clientes activos del centro que instalaron la app (objetivo fase 1: 30%)
- Tasa de vinculación exitosa en primer intento (objetivo: > 80%)

### Engagement
- DAU/MAU (objetivo: > 20%)
- Push open rate (objetivo: > 25%)
- Tiempo promedio por sesión (objetivo: > 2 min)

### Negocio (los que importan de verdad)
- **Recompra rate**: % de clientes que compran producto 2+ veces en 90 días (objetivo: +30% vs pre-app)
- **Tasa de cross-sell producto → servicio**: % de compradores de producto que contratan servicio en 60 días (objetivo: +15%)
- **Revenue per active user (ARPU)** (objetivo: +25% vs cliente sin app)
- **Tasa de referidos efectivos**: referidos que compran (objetivo: > 10%)

### Calidad
- Crash-free sessions (> 99.5%)
- Tiempo de carga de Home (< 1.5s)
- Push delivery rate (> 95%)
	
---

## 10. Por dónde empezamos: primer sprint

Si la decisión es arrancar ya, el **sprint 1 (2 semanas)** debería cubrir:

**Semana 1**:
1. Migración de base: normalización de teléfonos existentes con `phonenumbers`
2. Detector de duplicados en admin + UI de merge
3. Modelos `UsuarioCliente`, `VinculacionCliente`, `CodigoInvitacion`
4. Endpoint de generación de código desde admin

**Semana 2**:
5. Crear app `public_api` con endpoints básicos
6. Autenticación JWT en `client_api` (registro con código, login)
7. UI admin: botón "Invitar a la app" + listado de invitaciones
8. Tests backend de vinculación

**Al final del sprint 1**: backend listo para que empiece el proyecto Expo en paralelo.

Esto es antes de tocar una línea de código mobile. Si saltamos directo a Expo sin esto, no hay manera de que los usuarios se conecten a sus datos reales.

---

**Próximo paso concreto**: confirmar las decisiones pendientes (sección 7) con el cliente piloto y arrancar Sprint 1 del backend.
