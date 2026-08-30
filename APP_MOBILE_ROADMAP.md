# App Mobile Cliente - Roadmap de Implementación

**Fecha de creación**: Abril 2026
**Última actualización**: 30/08/2026
**Estado**: Fases 1 y 2 construidas y verificadas en producción. Fase 0 salteada
por decisión. Fases 3 y 4 pendientes — ver la sección 0.
**Supersedes parcialmente**: `CLIENTE_APP_ROADMAP.md` (web app, estrategia diferente)

---

## 0. Estado al 30/08/2026

> Esta sección es la verdad; el resto del documento es el plan de abril y se
> conserva porque explica **por qué** cada cosa es como es. Donde los dos se
> contradigan, mandá esta.

### Lo que está funcionando en producción

El 30/08/2026 la app corrió en un teléfono contra el backend de producción, con
una cuenta vinculada por código de invitación a una ficha real de AME, mostrando
turnos y datos reales del CRM.

**Backend** — `public_api` (catálogo) y `client_api` (14 endpoints: auth,
perfil, rutina, descuento, compra, turnos, disponibilidad, push, preferencias).
Vinculación de cuentas por código de invitación, auto-match por teléfono+email y
auto-registro. Compra con cupón contra Tienda Nube. Analytics de ventas de la
app en el CRM. Suite en verde.

**App** (`client-app/`, Expo SDK 57) — 15 rutas. Bienvenida, login, registro y
código de invitación; catálogo y ficha de producto; carrito y checkout en
WebView; turnos con reserva, cancelación e historial; mi rutina; perfil con
preferencias de avisos. Sistema de diseño propio derivado del manual de marca.

**Distribución** — proyecto EAS `@lucaspignataro/ame-esencial`, identidad
`com.ameesencial.app`, cuatro perfiles de build, EAS Update con política
`fingerprint`, y un workflow manual en GitHub Actions.

### Lo que falta para repartir a las primeras testers

En orden de lo que más duele:

1. **Credenciales de FCM** (`google-services.json` por `eas credentials`). Sin
   esto el push está construido de punta a punta y no llega ninguna
   notificación. Es lo único que queda del circuito.
2. **El logo real.** Los íconos de hoy son provisorios, generados con Cormorant.
   Cuando llegue se reemplazan cinco archivos y `app.json` no se toca.
3. **Recuperar contraseña.** No existe ni la pantalla ni el endpoint, y el
   backend **no tiene ningún proveedor de email configurado** — no hay `EMAIL_*`
   en settings y WhatsApp está caído. La primera tester que se olvide la
   contraseña queda afuera. Requiere elegir proveedor (Resend, SendGrid, SES).

### Decisiones de negocio que bloquean valor, no código

Ninguna la puede resolver el equipo técnico, y las tres cambian lo que la app
vale para una clienta:

- **¿El descuento de la app se apila con el 10% de transferencia?** Mientras no
  se responda, el segmento general queda en 0% y **la app no descuenta nada**,
  que era el motivo del proyecto. Se puede medir en vez de preguntar: ver
  `COMPRA_EN_APP_SPEC.md` §7.2.
- **Instalar la app en la tienda real de AME**, bloqueado por la pregunta al
  panel de partners sobre si una app "en desarrollo" se puede instalar en una
  tienda real. Hasta que pase, ningún producto tiene variante mapeada, `comprable`
  da `false` y **no se puede comprar desde la app**.
- **¿Las ofertas del CRM existen también en Tienda Nube?** Si no, la app muestra
  un precio que el checkout no respeta. Hoy no muerde porque no hay ofertas
  activas.

### Lo que sigue, en features

- **Motor de recompra** (Fase 3). Es lo próximo con mayor retorno y los datos ya
  están: `Producto` tiene `duracion_estimada_dias`, `pao_meses`, `contenido_ml` y
  `frecuencia_uso`, que es exactamente lo que come el algoritmo. Falta el cálculo,
  el Celery beat y el push con deep link.
- **Historial de compras y editar perfil.** Hoy Perfil solo muestra centros y
  cierra sesión. El `PATCH` de perfil ya existe en el backend pero solo admite
  nombre y apellido; historial no tiene endpoint.
- **Multi-centro de verdad.** `useCentroActivo` usa la primera vinculación; el
  modelo ya soporta varias. Es un solo punto a cambiar.
- **Vinculación por QR**, que evita dictar el código. Requiere `expo-camera`.
- **Puntos y referidos** (Fase 3), sin modelos todavía.

### Deuda técnica anotada, ninguna urgente

- `cache_page` cachea por URL y no por usuario en las vistas viejas de analytics:
  una llamada sin `sucursal_id` deja los números del primer centro cacheados para
  el siguiente.
- El job `check-low-inventory` del `beat_schedule` apunta a `apps.inventario.tasks`,
  que no existe. Nunca corrió. Hay un test que falla el día que alguien lo escriba.
- El blacklist de JWT está configurado pero **inerte**: falta
  `rest_framework_simplejwt.token_blacklist` en `INSTALLED_APPS`, así que no hay
  revocación de sesiones del lado del servidor.
- El admin de Django **no filtra por centro** (ningún `get_queryset` en 23
  ModelAdmin). Hoy no filtra datos porque ningún usuario de centro tiene
  `is_staff` y nada en el código se lo asigna, pero es un invariante tácito.
- Dos errores de lint abiertos en `reservar.tsx` (`set-state-in-effect`).

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

Lo que está instalado de verdad, al 30/08/2026. La tabla original de abril
pedía bastante más; abajo está lo que se descartó y por qué.

| Capa | Librería | Rol |
|------|----------|-----|
| Framework | **Expo SDK 57** | Builds, OTA, EAS |
| Lenguaje | TypeScript | Tipos espejados a mano desde los serializers |
| Routing | Expo Router 57 | File-based, deep linking desde los push |
| Estilos | **Theme tipado propio** (`src/theme/ame.ts`) | Paleta, tipografía, spacing y radios del manual de marca |
| Animaciones | Reanimated 4 | |
| Gestos | React Native Gesture Handler | |
| Estado servidor | TanStack Query 5 | Cache + invalidación desde los avisos |
| Estado global | Zustand 5 | Sesión y carrito |
| Imágenes | Expo Image | Cache + miniaturas WebP del backend |
| Fuentes | **Cormorant Garamond + Inter** | Reemplazos libres de Roseritta y Optima |
| Push | expo-notifications | Canal por categoría en Android |
| WebView | react-native-webview | El checkout de Tienda Nube vive acá |
| Pagos | **Ninguno en la app** | Cobra Tienda Nube; la app aplica un cupón |
| OTA | expo-updates | Política de runtime `fingerprint` |
| Sesión | expo-secure-store | Tokens JWT |

**Planeado y no usado:** NativeWind (se prefirió un theme tipado, sin build step
extra), Skia y Moti (no hizo falta), React Hook Form + Zod (los formularios son
chicos y validan a mano), `@gorhom/bottom-sheet`, expo-haptics, y MercadoPago
—reemplazado por el checkout de Tienda Nube, ver la decisión 5 de la sección 7—.

**Planeado y todavía pendiente:** **Sentry** (hoy un crash en el teléfono de una
tester es invisible) y **PostHog**. Los dos siguen teniendo sentido.

> Quedaron además tres dependencias de la plantilla que no usa nadie: `@expo/ui`,
> `expo-glass-effect` y `expo-symbols`. Se pueden sacar.

### Backend (extensiones sobre Django existente)

| Qué agregar | Ubicación | Rol |
|-------------|-----------|-----|
| App `public_api` | `backend/apps/public_api/` | Endpoints sin auth (info centro, catálogo público) |
| App `client_api` | `backend/apps/client_api/` | Endpoints para clientes autenticados |
| ~~App `fidelidad`~~ | — | **No existe.** Puntos y referidos siguen sin construirse (Fase 3) |
| ~~App `rutinas`~~ | `backend/apps/clientes/models.py` | **Resuelto distinto:** `PlanTratamiento`, `RutinaCuidado` y `RutinaItem` viven en `clientes`, sin app propia |
| Extensiones a `Producto` | Modelo existente | `duracion_estimada_dias`, `pao_meses`, `contenido_ml`, `frecuencia_uso` |
| Modelo `UsuarioCliente` | `backend/apps/clientes/` | Auth separada del `Usuario` (staff) |
| Modelo `VinculacionCliente` | `backend/apps/clientes/` | M2M entre `UsuarioCliente` y `Cliente` |
| Modelo `CodigoInvitacion` | `backend/apps/clientes/` | Códigos únicos para vinculación privada |
| Job Celery `predecir_recompras` | (pendiente) | Cálculo diario + disparo de push — **Fase 3, sin empezar** |
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

> Las casillas de abajo son el plan de abril y **nunca se marcaron**: el estado
> real de cada fase está en el bloque que sigue a su título, y el resumen
> completo en la sección 0. Se conservan sin tocar porque el detalle de cada
> entregable sigue siendo útil, aunque algunos se hayan resuelto distinto.

### ⚠️ Fase 0 — Validación sin app (2-3 semanas) — NO SALTEAR

> **SALTEADA por decisión.** Se arrancó directo en Fase 1 porque la integración
> de WhatsApp/Twilio, sobre la que se apoyaba casi toda esta fase, estaba caída.
> Ninguno de sus entregables se hizo, y **el riesgo que señalaba sigue vigente**:
> se construyó sobre una hipótesis de retención que no se validó antes.

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

> **HECHA, completa.** `public_api` y `client_api` en producción, los tres
> modelos de vinculación, las cuatro extensiones a `Producto` que alimentan el
> motor de recompra, y Expo Push de punta a punta. Única diferencia: los códigos
> de invitación se generan con una **acción del admin de Django**, no con un
> botón en el CRM.

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

> **HECHA, con cuatro desvíos.** La app está en producción y verificada en un
> teléfono. Lo que se resolvió distinto:
>
> - **El checkout no es MercadoPago.** Se usa el de Tienda Nube con un cupón por
>   compra. Es el cambio de arquitectura más grande respecto de este plan y tiene
>   su propio documento: `COMPRA_EN_APP_SPEC.md`.
> - **No se usó NativeWind.** El sistema de diseño es un theme tipado propio
>   (`src/theme/ame.ts`) derivado del manual de marca.
> - **No hay Sentry** ni QR scanner para vincular.
> - **No hay historial de compras** ni edición de perfil.

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

> **NO EMPEZADA. Es lo próximo con mayor retorno.** Los datos que come el
> algoritmo ya están cargados en `Producto` desde la Fase 1
> (`duracion_estimada_dias`, `pao_meses`, `contenido_ml`, `frecuencia_uso`):
> falta el cálculo, el Celery beat y el push con deep link. Puntos y referidos no
> tienen modelos todavía.

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

> **PARCIAL, y adelantada.** Las rutinas ya existen (`PlanTratamiento`,
> `RutinaCuidado`, `RutinaItem`) y la app las muestra en "Mi rutina". Faltan el
> feed de contenido, las valoraciones de servicios y los push segmentados de
> producto a servicio.

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

## 6. Build y distribución

> Reescrita el 30/08/2026, cuando se armó la configuración de verdad. Lo que
> había acá antes era el plan a priori: perfiles inventados de memoria y ninguna
> mención a iOS. Esto es lo que está en el repo.

### Qué ya está en el repo

- **`client-app/eas.json`** con cuatro perfiles (abajo el detalle).
- **Identidad definitiva** en `client-app/app.json`: la app se llama **AME
  esencial**, slug `ame-esencial`, y el identificador es **`com.ameesencial.app`**
  en las dos plataformas. El package de Android **no se puede cambiar** una vez
  que se sube a Play Store, por eso se definió antes del primer build y no
  después.
- `userInterfaceStyle` pasó a `"light"`: el diseño es claro y el `StatusBar` está
  fijo en `dark`. Con `"automatic"`, un teléfono en modo oscuro pintaba de negro
  las superficies nativas (teclado, action sheets, los controles de formulario
  del WebView del checkout) contra fondos marfil.

### Qué falta antes del primer build

1. **`eas init`** — es lo que crea el proyecto en EAS y escribe
   `extra.eas.projectId` en `app.json`. Sin ese id, `registrarDispositivo()` se
   saltea el registro y no llega ninguna notificación remota
   (`client-app/src/services/push.ts`).
2. **El arte de marca.** El ícono y el splash siguen siendo los de la plantilla
   de Expo: `splash-icon.png` es byte a byte el mismo archivo que
   `expo-logo.png`, y `icon.png` es el cuadrado azul con la "A". Hace falta el
   logo de AME en **1024×1024**. Para iOS tiene que ir **sin canal alfa y sin
   esquinas redondeadas** — Apple rechaza el envío si el ícono tiene
   transparencia, y las esquinas las pone el sistema.
3. **Credenciales de FCM** (Android): `google-services.json` cargado con
   `eas credentials`. El token se emite igual sin esto, pero Expo no puede
   entregar el mensaje.

### Setup por única vez

```bash
npm install -g eas-cli
eas login
cd client-app
eas init
```

### Los perfiles de `eas.json`

| Perfil | Para qué | Artefacto |
|---|---|---|
| `development` | Dev build con Metro adjunto: es lo único que permite probar push remoto en Android (Expo Go no lo soporta desde SDK 53) | APK / app de simulador iOS |
| `preview` | **El que se reparte a las testers.** Standalone, se instala y anda como app de verdad | APK |
| `preview-simulador-ios` | Igual que `preview` pero para el simulador de iOS. No pide cuenta de Apple | `.app` de simulador |
| `production` | Play Store / App Store | AAB |

Dos decisiones que conviene no tocar sin entender por qué están:

- **`EXPO_PUBLIC_API_URL` solo en `preview` y `production`.** Expo *inlinea* esa
  variable al compilar, así que en un build standalone tiene que venir del perfil
  (apunta a Railway). En `development` no va: ahí el JS lo sirve Metro desde tu
  máquina, y el valor sale del `.env` local. Si la ponés en `development`, la
  variable del perfil no se usa y solo confunde.
- **Ningún perfil declara `channel`.** Ese campo es de EAS Update y todavía no
  está instalado `expo-updates`. Se agregan las dos cosas juntas o el build falla
  pidiendo el paquete.

### Android — el camino de esta semana

```bash
eas build --platform android --profile preview
```

Sale un APK con link en el dashboard de EAS; se comparte por WhatsApp y se
instala habilitando "orígenes desconocidos". Android 13+ pide el permiso de
notificaciones en runtime, y de eso ya se ocupa `expo-notifications`.

> **Ojo con la carpeta `android/` local.** Quedó de un `expo run:android` viejo,
> con el package anterior (`com.anonymous.clientapp`). Está en `.gitignore` y EAS
> no la usa —construye desde la config—, pero si volvés a correr en el emulador,
> primero `npx expo prebuild --clean`.

### iOS — qué se puede hacer sin cuenta de Apple y qué no

Esta es la parte que define el cronograma. **Cualquier instalación en un iPhone
físico exige la cuenta paga de Apple Developer (US$99/año)**: no hay atajo, ni
por TestFlight ni por ad-hoc.

| Camino | ¿Cuenta paga? | Qué valida |
|---|---|---|
| **Expo Go** en el iPhone | No | Layout, safe areas, gestos, el WebView del checkout. No valida ícono, splash ni push remoto |
| **Build de simulador** (`preview-simulador-ios`) | No, pero **necesita una Mac** | La app compilada de verdad, con su ícono y su splash. Sin push (el simulador no recibe push remoto) |
| **Ad-hoc** (UDIDs con `eas device:create`) | **Sí** — máximo 100 iPhones por año, y hay que rebuildear al sumar un aparato | Todo, en un teléfono real |
| **TestFlight interno** | **Sí**, más el registro de la app en App Store Connect | Todo. Hasta 100 testers por Apple ID, sin review para el grupo interno |

**Plan para esta semana**, dado que la cuenta todavía no está:

1. **Hoy, gratis:** Expo Go en el iPhone para mirar diseño y recorrido. Si hay
   una Mac a mano, además `eas build -p ios --profile preview-simulador-ios`,
   que ya da la app compilada.
2. **En paralelo:** sacar la cuenta de Apple Developer. La aprobación suele
   tardar 24–48 h; la modalidad **individual** es la rápida, la de *organización*
   pide número D-U-N-S y puede sumar días. Es el camino crítico de todo lo iOS.
3. **Cuando la cuenta esté activa:** `eas build -p ios --profile production` →
   `eas submit -p ios` → grupo interno de TestFlight. El bundle id ya está
   definido, así que ese paso no vuelve a discutirse.

Mientras tanto, **todo el testeo serio arranca por Android**: es donde se puede
instalar hoy, gratis y en cualquier teléfono.

### Si el build falla en "Configure expo-updates"

Pasó en el primer intento, el 30/08/2026, y va a volver a pasar.

El error dice `Runtime version mismatch` y muestra dos hashes: el que calculó tu
máquina y el que calculó EAS. Es la política `fingerprint` haciendo su trabajo —
detecta que el árbol nativo local y el del build no son el mismo, lo que
significaría que un update publicado desde tu máquina no le corresponde a ese
binario.

La causa típica no es el código: es que `node_modules` quedó desincronizado del
lockfile. `npm install` actualiza de a partes y puede dejar un paquete con
contenido viejo en disco; EAS instala con `npm ci`, que reconstruye el árbol
entero desde el lockfile. La primera vez fue después de un `expo install --fix`,
y el paquete que quedó viejo era `@react-native-masked-view/masked-view`.

Se arregla haciendo localmente lo mismo que hace EAS:

```bash
npm ci
```

Y se comprueba **sin gastar un build**, comparando el hash contra el que el log
de EAS dice que calculó:

```bash
npx expo-updates fingerprint:generate --platform android
```

El campo `hash` de la salida tiene que coincidir con el de EAS. Si coincide, el
build pasa esa fase.

### Costos EAS

Consultado el 30/08/2026. Cambia, así que conviene reconfirmarlo antes de
decidir cualquier cosa a partir de estos números.

El plan **gratuito** da **15 builds de Android y 15 de iOS por mes** —se cuentan
por separado—, con cola de baja prioridad, una sola concurrencia y **timeout de
45 minutos**. Ese timeout es el límite que más cerca queda: los planes pagos
tienen dos horas.

Alcanza de sobra mientras los builds sean deliberados, que es justo por lo que
el workflow de Actions está en `workflow_dispatch` y no en cada push.

**Lo que realmente estira el cupo es EAS Update.** Un cambio que es solo JS/TS
no necesita build: sale con `eas update`, llega a los APK ya instalados y no
consume nada del tope. Un build nuevo hace falta solamente cuando cambia lo
nativo —una librería, `app.json`, el SDK—, que es exactamente lo que la política
`fingerprint` del runtime version detecta sola.

Si alguna vez queda corto: el plan Starter son US$19/mes y, pasado el crédito
incluido, un build de Android medium sale US$1.

---

## 7. Decisiones

Actualizado el 30/08/2026. Las seis de abril están resueltas salvo una.

### Tomadas

1. **Fase 0** → **salteada.** WhatsApp/Twilio estaba caído y casi toda la fase
   dependía de eso. Se asumió el riesgo a conciencia.
2. **Identidad multi-centro** → **M2M**, como recomendaba. `VinculacionCliente`
   admite varias fichas por cuenta. La app todavía usa la primera
   (`useCentroActivo`), que es el único punto a cambiar el día que haga falta.
3. **Centro piloto** → **AME**, confirmado y en producción.
4. **Diseñador de producto** → **no se contrató.** El sistema se derivó del
   manual de marca existente, con Cormorant Garamond e Inter como reemplazos
   libres de Roseritta y Optima, que no son cross-platform.
5. **Gateway de pago** → **ninguno.** Cambió de raíz: no se cobra en la app. Se
   usa el checkout de Tienda Nube con un cupón por compra, así el centro cobra
   por donde ya cobra y la plataforma no toca dinero ni datos de tarjeta. El
   panel de la tienda demo mostró un costo por transacción del 2% para medios de
   pago personalizados, lo que terminó de cerrar la decisión. Todo el detalle en
   `COMPRA_EN_APP_SPEC.md` §3.1.

### Abierta

6. **Política de seña para turnos online.** Sigue sin definirse. Hoy la app
   **reserva sin seña**, que es la opción permisiva: si el centro quiere seña
   obligatoria, hay que tocar el flujo de reserva y sumar un medio de cobro, que
   es justo lo que la decisión 5 evitó. Impacto directo sobre los no-shows.

### Nuevas, que aparecieron construyendo

Ninguna es técnica; las tres las tiene que responder el centro o Tienda Nube, y
están detalladas en la sección 0 y en `COMPRA_EN_APP_SPEC.md` §7:

- Si el descuento de la app se apila con el 10% de transferencia. **Mientras no
  se responda, la app no descuenta nada.**
- Si se puede instalar una app "en desarrollo" en la tienda real de AME. **Hasta
  que se resuelva, no se puede comprar desde la app.**
- Si las ofertas del CRM existen también en Tienda Nube.

Y una que sí es nuestra: **qué proveedor de email** se usa para recuperar
contraseña. El backend no tiene ninguno configurado.

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

> **Histórico.** Este sprint se ejecutó y quedó atrás: todo lo que lista está en
> producción. Se conserva porque muestra el orden en que se armaron las
> fundaciones. **Lo que sigue ahora está en la sección 0.**

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

**Próximo paso concreto** (30/08/2026): cargar las credenciales de FCM para
cerrar el circuito de push, y en paralelo empujar las tres preguntas al centro y
a Tienda Nube que hoy mantienen a la app sin descuento y sin poder vender. Una
vez repartido el APK a las primeras testers, el trabajo con mayor retorno es el
motor de recompra de la Fase 3, que tiene los datos listos desde la Fase 1.
