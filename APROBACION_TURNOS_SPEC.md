# Aprobación de turnos pedidos desde la app

**Estado:** diseñado, sin implementar.
**Fecha:** 05/10/2026

Lo que pidió AME: que cada reserva hecha desde la app le llegue por mail con toda
la información, que figure como notificación en el CRM, que ella pueda aceptarla o
rechazarla, y que la clienta reciba la resolución por push.

Este documento es el plan. Las decisiones de producto ya están tomadas y figuran
en §1; el porqué de cada una está en §2, que es la parte que conviene leer antes
de cambiar algo.

---

## 1. Las reglas, ya decididas

| Regla | Valor |
|---|---|
| Qué turnos pasan por aprobación | **Todos** los pedidos desde la app |
| Ventana de respuesta del centro | **09:00 a 20:00**, configurable por sucursal |
| Vencimiento del pedido | **3 horas de reloj de respuesta**, configurable |
| Motivo de rechazo | **Obligatorio**, de una lista cerrada |
| Destinatario del mail | `ame.esencial@gmail.com`, configurable |
| Remitente | `info@ameesencial.com.ar` (el que ya está en SES) |
| Resolución a la clienta | **Push**, tanto si se aprueba como si se rechaza |

### Lo que ya existe y no hay que construir

- **La app ya reserva en `PENDIENTE`.** `TurnosView.post` llama a
  `reservar_turno(..., estado=Turno.Estado.PENDIENTE)`.
- **Un pendiente ya bloquea el horario.** `ESTADOS_QUE_OCUPAN` incluye
  `PENDIENTE`, así que no hay carrera entre dos clientas por el mismo slot.
- **El push de confirmación ya está cableado.** La señal de
  `apps/turnos/signals.py` dispara `TURNO_CONFIRMADO` cuando un turno pasa a
  `CONFIRMADO`, venga de donde venga el cambio. Solo falta FCM para que llegue
  (ver `LIVEOPS_PENDIENTE.md` §2).
- **La antelación mínima existe.** `DIAS_MINIMOS_ANTICIPACION = 1`, por día de
  calendario, aplicada en `motivo_fecha_no_reservable`.

---

## 2. Las decisiones de diseño, y por qué

### 2.1 `RECHAZADO` es un estado propio, no un `CANCELADO`

Un turno cancelado existió y se cayó; un pedido rechazado nunca llegó a ser
turno. La diferencia se paga en tres lados:

- **El texto.** "Te cancelamos el turno del martes" versus "No pudimos tomar ese
  horario, elegí otro". La segunda tiene una acción; la primera es una disculpa.
- **Las métricas.** La tasa de rechazo mide si la disponibilidad que publica la
  app se parece a la realidad del centro. La de cancelación mide comportamiento
  de las clientas. Mezcladas, las dos quedan inservibles.
- **La agenda.** Un rechazo libera el slot de inmediato.

### 2.2 El vencimiento corre en horario de respuesta, no de reloj

Con 3 horas de reloj de pared, un pedido hecho a las 23:10 vence a las 02:10 y a
la mañana AME encuentra un rechazo automático de algo que habría aceptado. Eso es
peor que no tener el feature: le dice "no" a una clienta cuando la respuesta era
"sí".

El contador corre solo dentro de la ventana de respuesta. Si el pedido entra
fuera, arranca cuando la ventana abre.

### 2.3 Un horario se ofrece solo si entra en la ventana de respuesta

La antelación mínima es por día de calendario, así que **el margen real en horas
puede ser de 8**: reserva a las 23:59, turno al día siguiente a las 08:00.

Con la regla anterior aparece un caso sin salida: pedido el lunes 23:30 para el
martes 08:00, con ventana que abre a las 09:00. No existe ningún momento en que
AME pudiera aprobarlo.

> **La regla:** un horario se ofrece solo si queda tiempo de respuesta suficiente
> entre ahora y el inicio del turno.

Con ventana 09:00–20:00 y vencimiento de 3 horas:

| Momento de la reserva | Turno martes 08:00 | Turno martes 12:00 |
|---|---|---|
| Lunes 10:00 | ✅ hay 3 h el lunes | ✅ |
| Lunes 23:30 | ❌ no se ofrece | ✅ hay 09:00–12:00 |

Quien reserva de noche ve menos horarios temprano al día siguiente. Es preferible
no ofrecer un horario antes que ofrecerlo y rechazarlo solo tres horas después.

**Se deriva del vencimiento, no es una constante aparte.** Si mañana el
vencimiento baja a 1 hora, la regla se ajusta sola. Dos constantes independientes
se contradicen tarde o temprano.

### 2.4 El motivo es una lista, no texto libre

Dos razones. El texto libre frena a AME justo cuando está apurada y termina
escribiendo "no". Y el reporte de rechazos no se puede agrupar, con lo cual la
métrica más útil del feature —*por qué estamos rechazando*— no existe.

Hay un motivo que **AME no puede elegir**, que lo pone el sistema:
`VENCIDO_SIN_RESPUESTA`. Separa "dijimos que no" de "nadie lo miró", que son dos
problemas distintos con dos soluciones distintas.

### 2.5 La bandeja del CRM no es el outbox de avisos

`Aviso` es un **outbox**: una entrega pendiente, atada a una `UsuarioCliente`,
que se manda y se olvida. La bandeja del CRM es otra cosa: durable, con
leído/no leído, accionable, y de una sucursal y no de una persona.

Además, `cola.py` está íntegramente armado alrededor de `usuario_cliente` y de
dispositivos push: `_dispositivos_por_usuario`, `select_related('usuario_cliente')`,
el canal de Android por categoría. Generalizarlo para que acepte una dirección de
mail obliga a tocar el camino caliente del push por una funcionalidad que no es
de push.

### 2.6 Una sola fila para la notificación del centro, con la entrega adentro

El aviso al centro llega a dos lugares —la campanita del CRM y el mail— pero es
**un solo hecho**. Modelarlo como una fila de bandeja más una fila de outbox
obliga a mantenerlas sincronizadas sin ganar nada.

`NotificacionInterna` es una fila que lleva su propia entrega por mail: estado,
intentos, error. El bell la lee directo; un barrido manda los mails pendientes con
reintentos. No se toca `cola.py` y la disciplina de reintento vive donde está el
dato.

### 2.7 La bandeja es una cola de trabajo, no un buzón personal

Si la recepcionista resuelve el pedido, la dueña no necesita seguir viéndolo
pendiente. Por eso el estado de leído es **compartido por sucursal** y no por
usuario: una fila, con quién la leyó y cuándo.

Y lo accionable no se guarda, **se deriva**: la campanita cuenta las
notificaciones cuyo turno sigue en `PENDIENTE`. Así no hay un segundo estado que
se pueda desincronizar del turno.

### 2.8 El mail lleva a la decisión, no la ejecuta

Botones de aceptar y rechazar en el mail necesitarían un token firmado que cambie
estado sin sesión: cualquiera que reenvíe el mail confirma el turno. En un sistema
con datos de salud no corresponde.

El mail lleva un **link profundo al turno en el CRM** (`/turnos?turno=<id>`), que
abre la ficha con los botones y el contexto al lado: la agenda del día, el
historial de la clienta, si debe algo. Desde el teléfono es un toque más y una
decisión mejor informada.

### 2.9 Tiempo real: polling, y es la respuesta correcta

Django Channels significa un proceso más en Railway, Redis como transporte y un
modo de falla nuevo, para ganar segundos de latencia en un evento que pasa un
puñado de veces por día. No se paga.

`refetchInterval` de 30–60 segundos más `refetchOnWindowFocus` cubre el uso real.

**Qué cambiaría la decisión:** que quieran la agenda viva y compartida entre
varias personas a la vez, o volumen de otro orden.

### 2.10 El origen del turno es explícito

Hoy se puede inferir —`creado_por` es nulo si lo creó la app— pero es implícito y
frágil, y el flujo de aprobación tiene que aplicarse solo a los turnos de la app.
Un campo `origen` lo resuelve, y Analytics lo va a querer igual: "cuántos turnos
vienen de la app" es un KPI del roadmap.

### 2.11 `vence_en` se guarda, no se calcula al vuelo

Tres razones: el barrido queda en una consulta indexada en vez de recorrer y
calcular; el CRM puede mostrar "vence en 40 minutos" sin repetir la lógica; y si
mañana cambia la política, **los pedidos viejos conservan su plazo original**, que
es el comportamiento justo.

---

## 3. Modelo de datos

### 3.1 `Turno` (apps/turnos/models.py)

```python
class Estado(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente de Confirmación'
    CONFIRMADO = 'CONFIRMADO', 'Confirmado'
    RECHAZADO = 'RECHAZADO', 'Rechazado'        # nuevo
    COMPLETADO = 'COMPLETADO', 'Completado'
    CANCELADO = 'CANCELADO', 'Cancelado'
    NO_SHOW = 'NO_SHOW', 'No Show'

class MotivoRechazo(models.TextChoices):
    SIN_DISPONIBILIDAD = 'SIN_DISPONIBILIDAD', 'No hay disponibilidad real'
    EQUIPO_NO_DISPONIBLE = 'EQUIPO_NO_DISPONIBLE', 'El equipo no está disponible'
    DEUDA_PENDIENTE = 'DEUDA_PENDIENTE', 'La clienta tiene una deuda'
    REQUIERE_EVALUACION = 'REQUIERE_EVALUACION', 'Requiere evaluación previa'
    OTRO = 'OTRO', 'Otro'
    # Lo pone el sistema; no se ofrece en el CRM.
    VENCIDO = 'VENCIDO', 'Venció sin respuesta'

class Origen(models.TextChoices):
    APP = 'APP', 'App de clientas'
    CRM = 'CRM', 'Cargado en el CRM'
```

Campos nuevos:

| Campo | Tipo | Nota |
|---|---|---|
| `origen` | CharField(choices) | Default `CRM`; la app manda `APP` |
| `vence_en` | DateTimeField null | Solo para pedidos que esperan aprobación |
| `motivo_rechazo` | CharField(choices) blank | |
| `detalle_rechazo` | CharField(300) blank | Texto libre opcional, para `OTRO` |
| `resuelto_por` | FK Usuario null | Quién aceptó o rechazó. Nulo si venció |
| `resuelto_en` | DateTimeField null | |

**`ESTADOS_QUE_OCUPAN` no cambia**: `RECHAZADO` no ocupa, así que el slot se
libera solo.

Índice nuevo para el barrido: `(estado, vence_en)`.

### 3.2 `Sucursal` (apps/empleados/models.py)

| Campo | Default | Nota |
|---|---|---|
| `respuesta_hora_inicio` | `09:00` | Cuándo empieza a correr el reloj |
| `respuesta_hora_fin` | `20:00` | Cuándo se detiene |
| `horas_para_responder` | `3` | Vencimiento, en horas de esa ventana |
| `email_avisos` | `''` | Destinatario. Vacío cae a `Sucursal.email` |

Va en `Sucursal` y no en `CentroEstetica` porque la agenda es de la sucursal: dos
locales pueden tener personas y horarios distintos.

### 3.3 `Servicio` (apps/servicios/models.py)

| Campo | Default | Nota |
|---|---|---|
| `requiere_aprobacion` | `True` | Todos pasan por aprobación hoy |

AME pidió que sea todo manual, pero el campo se crea igual. El día que tenga 40
pedidos por semana y quiera que la limpieza facial se auto-confirme, es cambiar un
check y no una migración con datos encima.

Con `False`, la app crea el turno directamente en `CONFIRMADO` y la señal que ya
existe dispara el push de confirmación. No hay camino nuevo que escribir.

### 3.4 `NotificacionInterna` (apps/notificaciones/models.py)

```python
class Tipo(models.TextChoices):
    TURNO_SOLICITADO = 'TURNO_SOLICITADO', 'Pidieron un turno'
    TURNO_POR_VENCER = 'TURNO_POR_VENCER', 'Un pedido está por vencer'

class EstadoEntrega(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    ENVIADO = 'ENVIADO', 'Enviado'
    SIN_DESTINO = 'SIN_DESTINO', 'Sin destinatario configurado'
    FALLIDO = 'FALLIDO', 'Fallido'
```

| Campo | Nota |
|---|---|
| `sucursal` | FK. La bandeja es de la sucursal |
| `tipo` | choices |
| `turno` | FK null. Lo accionable sale de su estado |
| `titulo`, `cuerpo` | Para la campanita |
| `datos` | JSON, para el link y lo que haga falta |
| `clave` | Único. Idempotencia: `turno:12:solicitado` |
| `leida_en`, `leida_por` | Compartido por sucursal (§2.7) |
| `email_estado`, `email_intentos`, `email_error`, `email_enviado_en` | La entrega |
| `creada_en` | |

Índices: `(sucursal, -creada_en)` y `(email_estado,)` para el barrido.

> **Cuando aparezca un segundo tipo de recurso** —un pedido de cancelación, una
> alerta de stock— el FK a `Turno` se reemplaza por `recurso_tipo` + `recurso_id`.
> No se hace ahora: sería generalidad especulativa sin un segundo caso a la vista.

---

## 4. La lógica de la ventana de respuesta

Es la parte más delicada del feature y va en funciones puras, sin base, con tests
propios.

```python
# apps/turnos/ventana.py

def sumar_horas_de_respuesta(desde, horas, *, hora_inicio, hora_fin):
    """
    Avanza `horas` contando solo el tiempo dentro de [hora_inicio, hora_fin).

    Si `desde` cae fuera de la ventana, arranca en la próxima apertura.
    """

def vencimiento_de(inicio_turno, pedido_en, *, sucursal):
    """
    Cuándo vence el pedido: lo que pase primero entre agotar las horas de
    respuesta y el inicio del turno.
    """

def hay_ventana_suficiente(inicio_turno, *, ahora, sucursal):
    """
    ¿Queda tiempo de respuesta entre `ahora` y el turno? Es el predicado que
    filtra los slots (§2.3).
    """
```

**Trampas a cubrir con tests:**

- Zona horaria. Todo en hora local de Argentina; la base guarda UTC.
- Cruce de medianoche y de varios días seguidos.
- Pedido justo en el borde: a las 08:59 y a las 20:00 clavadas.
- Ventana invertida o de ancho cero: tiene que fallar fuerte, no colgarse.
- Un turno que ya pasó.
- Sucursal sin configuración: caer a los defaults sin romper.

---

## 5. Fases

Cada fase es desplegable sola y deja el sistema en un estado coherente.

### Fase 1 — Modelo y política

Campos de §3.1 a §3.3, migraciones, y las funciones puras de §4 con su batería de
tests. Sin cambios de comportamiento visible.

`reservar_turno` pasa a aceptar `origen` y a calcular `vence_en` cuando el
servicio requiere aprobación.

### Fase 2 — Los horarios que se ofrecen

`calcular_slots` y `slots_agregados` filtran por `hay_ventana_suficiente`, y
`ReservaSerializer` valida lo mismo del lado del POST — igual que hoy con
`motivo_fecha_no_reservable`, para que la app y el backend nunca discrepen.

**Test que define la fase:** a las 23:30 del lunes, el martes 08:00 no se ofrece y
el martes 12:00 sí.

### Fase 3 — El aviso al centro

- `NotificacionInterna` con su migración.
- Señal: al crear un `Turno` con `origen=APP` y `estado=PENDIENTE`, crear la
  notificación con clave idempotente.
- Barrido `enviar_pendientes()` que manda los mails con
  `apps/notificaciones/correo.py`, el mismo que ya usa la recuperación de
  contraseña. Se engancha a `disparadores.correr_todos`.
- Plantilla del mail: clienta, teléfono, servicio, fecha y hora, profesional,
  notas, **hasta cuándo puede responder**, y el link a `/turnos?turno=<id>`.

**Antes de probar esto hay que verificar `ame.esencial@gmail.com` en SES.**
Seguimos en sandbox: solo se le puede escribir a direcciones verificadas. Es el
mismo trámite de dos minutos que se hizo con `info@`.

### Fase 4 — Resolver, y avisarle a la clienta

Dos funciones de servicio con transacción y auditoría:

```python
confirmar_turno(turno, *, usuario)
rechazar_turno(turno, *, usuario, motivo, detalle='')
```

El push de confirmación **ya sale solo**: la señal existente escucha la transición
a `CONFIRMADO`. Falta el gemelo del rechazo:

```python
Evento(
    clave=TURNO_RECHAZADO,
    categoria=Categoria.TURNOS,
    transaccional=True,          # llega aunque haya apagado Turnos
    ruta='/(tabs)/reservar',     # el tap lleva a elegir otro horario
)
```

**Transaccional igual que la cancelación:** apagar los recordatorios no es apagar
"tu turno no va".

El texto le habla de la acción, no del rechazo: *"No pudimos tomar ese horario.
Tocá para elegir otro."* El motivo queda en el CRM para las métricas; a la clienta
no le llega crudo — "no hay disponibilidad" es muy distinto de leer "tiene una
deuda".

### Fase 5 — Vencimiento automático

En el barrido que ya programa los recordatorios:

- **Vencidos:** `estado=PENDIENTE` y `vence_en <= ahora` → `rechazar_turno` con
  motivo `VENCIDO` y `resuelto_por=None`. Dispara el push y libera el slot.
- **Por vencer:** a 30 minutos del vencimiento, una `NotificacionInterna` de tipo
  `TURNO_POR_VENCER` y su mail. Convierte el vencimiento en algo que AME puede
  atajar en vez de algo que le pasa por encima.

Las dos con clave idempotente: el barrido corre seguido y no puede avisar dos
veces.

### Fase 6 — El CRM

**Backend:** endpoints para listar notificaciones de la sucursal, marcar leída, y
confirmar/rechazar un turno. Permisos: quien pueda ver la agenda.

**Frontend:**

- Campanita en `Layout.tsx` con el contador de **pedidos sin resolver** — turnos
  todavía en `PENDIENTE`, no notificaciones sin leer (§2.7).
- Bandeja desplegable, con `refetchInterval` y `refetchOnWindowFocus`.
- En la ficha del turno: botones de Aceptar y Rechazar; el de rechazar abre el
  select de motivos con el texto libre opcional al lado.
- Soporte de `?turno=<id>` en `/turnos` para que el link del mail abra la ficha.
- En la grilla, los pendientes se distinguen y muestran **cuánto les queda**.

### Fase 7 — La app

- La ficha del turno pendiente dice **"Esperando confirmación del centro"**, con
  su propio tratamiento visual. Si se ve igual que uno confirmado, el rechazo se
  siente como que le sacaron algo que tenía.
- La pantalla de confirmación de reserva explica que falta el visto bueno.
- El turno rechazado se muestra como tal, con el camino a elegir otro horario en
  el mismo lugar.
- `TurnoAppSerializer` ya manda `estado`; hay que contemplar el valor nuevo.

---

## 6. Qué puede salir mal

| Riesgo | Mitigación |
|---|---|
| Rechazos falsos por vencimiento | El reloj corre en ventana de respuesta (§2.2) y hay aviso previo a 30 min |
| Horarios que no se pueden aprobar a tiempo | No se ofrecen (§2.3) |
| El mail no llega y nadie se entera | Entrega con estado y reintentos en la misma fila; `email_estado` visible en el admin |
| SES en sandbox | Verificar `ame.esencial@gmail.com` antes de la Fase 3 |
| El push no llega | Depende de FCM (`LIVEOPS_PENDIENTE.md` §2). El mail y la campanita funcionan sin eso |
| Dos procesos avisando dos veces | Clave de idempotencia en `NotificacionInterna`, igual que en `Aviso` |
| La política cambia y rompe pedidos vivos | `vence_en` guardado: los viejos conservan su plazo (§2.11) |

---

## 7. Dependencias

- **FCM** es lo único que bloquea el circuito completo. El mail a AME y la
  campanita del CRM andan sin eso; el push a la clienta no.
- **`ame.esencial@gmail.com` verificado en SES**, antes de la Fase 3.
- Salir del sandbox de SES no es necesario para este feature: el único
  destinatario es una casilla que se puede verificar a mano.

---

## 8. Documentos relacionados

- `NOTIFICACIONES_PUSH_SPEC.md` — el outbox de avisos y el circuito de push.
- `LIVEOPS_PENDIENTE.md` §2 y §3 — FCM y SES.
- `APP_MOBILE_ROADMAP.md` §0 — estado de la app.
