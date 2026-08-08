# Notificaciones push

Sistema de avisos a la app de clientas. Está pensado para ser **la única tubería
de notificaciones**: turnos, rutina, cumpleaños, promociones y lo que venga
después usan el mismo camino.

---

## Cómo agregar un aviso nuevo

Es el caso más frecuente, así que va primero. Se toca **un solo archivo**:

```python
# backend/apps/notificaciones/eventos.py

SESION_VENCIDA = 'sesion_vencida'

Evento(
    clave=SESION_VENCIDA,
    categoria=Categoria.NOVEDADES,
    titulo='Te queda una sesión',
    cuerpo='Tenés {sesiones} sesión(es) de {tratamiento} sin usar.',
    ruta='/turnos',
    variables=('sesiones', 'tratamiento'),
)
```

Y desde donde corresponda:

```python
from apps.notificaciones import despacho, eventos

despacho.crear_aviso(
    evento=eventos.SESION_VENCIDA,
    usuario_cliente=usuario,
    centro_estetica=centro,
    contexto={'sesiones': 2, 'tratamiento': 'Láser'},
    clave=f'sesiones:{plan.id}',   # opcional: evita repetir el mismo aviso
)
```

No hay que tocar la cola, el canal, las preferencias ni el envío. Si el aviso es
programado (sale a una hora, no ahora), se suma una función a `disparadores.py`.

---

## Arquitectura

```
  quien dispara            despacho.py              cola.py              Expo
 ────────────────         ─────────────           ─────────            ──────
  señal de turno   ─┐                          ┌─ toma en lote
  disparador cron  ─┼──▶  crea el Aviso  ──▶   │  arma mensajes  ──▶  /push/send
  acción del staff ─┘     (tabla outbox)       └─ asienta el resultado
                                                                          │
                            DispositivoPush ◀── da de baja  ◀── /getReceipts
```

| Archivo | Qué resuelve |
|---|---|
| `eventos.py` | Catálogo: qué avisos existen, su texto y su categoría. Datos puros. |
| `despacho.py` | Crea avisos aplicando preferencias, plantillas del centro e idempotencia. |
| `cola.py` | Envía lo vencido, reintenta, procesa recibos y limpia tokens muertos. |
| `disparadores.py` | Lo que nace del paso del tiempo: recordatorios, cumpleaños, rutina. |
| `canales/expo.py` | Cliente HTTP de la Expo Push API. Es lo único que sabe de Expo. |

### Modelos

- **`DispositivoPush`** — un teléfono. Una cuenta puede tener varios; el token es
  único a nivel sistema, así que un aparato que cambia de dueña se reasigna en
  lugar de duplicarse.
- **`PreferenciaNotificacion`** — opt-out por categoría. Solo se guardan las
  categorías apagadas: sumar una categoría nueva no exige migrar a nadie.
- **`PlantillaNotificacion`** — texto propio de un centro. Sin fila, se usa el
  del catálogo.
- **`Aviso`** — el outbox. Una notificación resuelta para una persona.
- **`EnvioPush`** — la entrega a un dispositivo concreto, con su ticket de Expo.

### Las tres decisiones que explican el diseño

**1. Es un outbox, no un envío directo.** Quien dispara escribe una fila y sigue.
El request del staff que confirma un turno no espera a Expo, un pico de avisos no
cuelga a nadie, y si el proceso de envío está caído nada se pierde: sale cuando
vuelve.

**2. La idempotencia es una clave única, no un booleano en el origen.**
`turno:12:recordatorio_24h` entra una sola vez por más que el cron corra
solapado, se atrase o se repita. Por eso los disparadores pueden ser un barrido
simple sobre el estado de la base en lugar de una ventana frágil alrededor del
ahora, y por eso también cubren los turnos cargados por vías que no pasan por
ninguna señal.

**3. La cola toma en dos fases.** Marca las filas como `PROCESANDO` en una
transacción corta con `skip_locked` y recién después habla con Expo. Dos procesos
nunca agarran el mismo aviso, y ninguno sostiene un lock de base durante una
llamada HTTP. Lo que quede colgado por un proceso muerto vuelve solo a la cola a
los 15 minutos.

---

## Cómo corre

**Producción (Railway).** El despliegue levanta solo Gunicorn: **no hay worker ni
beat de Celery**. El motor es un servicio de cron que corre el comando:

```bash
python manage.py procesar_notificaciones
```

Config lista en `backend/railway.notificaciones.cron.json`. Cada 5 minutos
alcanza: los recordatorios ya están encolados con su hora exacta, el cron solo
los saca.

**Desarrollo.** `docker-compose` sí levanta worker y beat, y las tasks de
`tasks.py` llaman a las mismas funciones que el comando. Que compartan función es
lo que evita que dev y producción se comporten distinto.

Etapas por separado, para depurar:

```bash
python manage.py procesar_notificaciones --disparadores   # solo encolar
python manage.py procesar_notificaciones --cola           # solo enviar
python manage.py procesar_notificaciones --recibos        # solo confirmar
```

---

## Endpoints de la app

| Método | Ruta | Qué hace |
|---|---|---|
| `POST` | `/api/client/push/register/` | Registra el teléfono. Reasigna el token si era de otra cuenta. |
| `DELETE` | `/api/client/push/register/` | Lo da de baja (logout). |
| `GET` | `/api/client/notificaciones/preferencias/` | Mapa `categoria -> bool`. |
| `PATCH` | `/api/client/notificaciones/preferencias/` | Enciende o apaga categorías. |

Los avisos **transaccionales** (turno confirmado, turno cancelado) ignoran las
preferencias: apagar "Turnos" silencia los recordatorios, no el aviso de que te
cancelaron el turno de mañana.

---

## Cómo se prueba sin Expo y sin teléfono

Es lo primero que hace falta, porque los dos requisitos de la sección siguiente
tardan en estar. La simulación se hace en dos mitades, y entre las dos cubren el
recorrido completo.

### Mitad backend: canal de consola

`NOTIFICACIONES_CANAL=consola` reemplaza el envío por una impresión. Corre la
tubería entera —disparadores, cola, reintentos, recibos, idempotencia, estados—
sin salir a internet. **Es el default en `DEBUG`**, así que una máquina de
desarrollo no manda una notificación real por accidente.

```bash
# Revisar la redacción de los 9 avisos. No toca la base.
docker-compose exec backend python manage.py simular_notificacion --listar

# Mandar uno y ver exactamente qué le llegaría a la clienta.
docker-compose exec backend python manage.py simular_notificacion \
    --evento cumpleanos --email sofi@mail.com

# Uno de cada tipo, para revisar la tanda completa con el centro.
docker-compose exec backend python manage.py simular_notificacion \
    --todos --email sofi@mail.com

# Estado de la cola: qué se acumuló, qué falló, cuántos dispositivos hay.
docker-compose exec backend python manage.py simular_notificacion --estado
```

Cada aviso sale dibujado como se vería en pantalla:

```
┌────────────────────────────────────────────┐
│ ¡Feliz cumple, Sofía!                      │
│ Que lo pases hermoso. Te esperamos en AME. │
├────────────────────────────────────────────┤
│ → /promos                                  │
│ canal: novedades                           │
└────────────────────────────────────────────┘
```

Si la cuenta no tiene dispositivos, el comando le crea uno simulado (el aviso
quedaría en `SIN_DESTINO` si no). Y si el canal activo es `expo`, avisa antes de
mandar de verdad.

### Mitad app: simulador de notificaciones locales

El panel de **Perfil → Simulador de avisos**, visible solo en `__DEV__`, programa
una notificación local con la misma carga útil que manda el backend. Con eso se
prueba lo que el canal de consola no puede: el permiso, el banner, el canal de
Android, el tap, el deep link y el refresco de datos. Aparece a los 3 segundos,
para dar tiempo a mandar la app al fondo.

⚠️ **En Android necesita un development build.** La doc de Expo dice que las
notificaciones locales siguen disponibles en Expo Go, y es cierto en iOS; en
Android el paquete **ni siquiera se puede importar** dentro de Expo Go, así que
tampoco hay simulación local. Con `npx expo run:android` funciona todo.

Lo único que ninguna de las dos mitades prueba es **el transporte** —que Expo
entregue el mensaje—, y eso solo se verifica con los dos requisitos de abajo.

---

## ⚠️ Regla al tocar notificaciones en la app

**Nunca importar `expo-notifications` de forma estática.** Siempre a través de
`services/notificacionesNativas.ts`, que lo carga con `require()` y devuelve
`null` donde no se puede usar.

El motivo no es estilístico. `expo-notifications` ejecuta
`DevicePushTokenAutoRegistration` **al cargarse**, eso llama a
`warnOfExpoGoPushUsage()`, y esa función hace `throw` cuando detecta Expo Go en
Android (en iOS solo avisa). Un `import` estático en un archivo que la app
siempre carga hace fallar la evaluación de ese módulo y de todo lo que venga
después en la cadena.

Los síntomas quedan lejísimos de la causa. Cuando pasó, el import estaba en
`_layout.tsx`: la cadena se cortaba antes de llegar al store de sesión, el store
nunca registraba el token en la capa de red, y **todos los requests salían sin
`Authorization`**. Se veía como un 401 en `/api/client/turnos/` y parecía un
problema de autenticación. No lo era.

Dos corolarios:

- El import de **tipos** sí puede ser estático (`import type * as ... from
  'expo-notifications'`): TypeScript lo borra al compilar y no ejecuta nada.
- Se usa `getLastNotificationResponseAsync()` dentro de un efecto y **no** el
  hook `useLastNotificationResponse()`. Ese hook lanza donde el módulo nativo no
  está, y al ser un hook la excepción sube durante el render y se lleva puesto
  todo el navegador.

---

## Requisitos para que llegue a un teléfono

El backend está terminado y probado. Del lado de la app faltan dos cosas que
requieren cuenta de Expo y no se pueden resolver desde el código:

**1. `projectId` de EAS.** `getExpoPushTokenAsync` lo exige. Sale de correr
`eas init` en `client-app/`, que lo escribe en `app.json` bajo
`extra.eas.projectId`. Sin esto, `registrarDispositivo()` avisa por consola y no
registra nada — la app funciona igual, pero no recibe push.

**2. Development build.** Desde el SDK 53, **las notificaciones remotas no
funcionan en Expo Go en Android**. Hace falta un build propio:

```bash
npx expo run:android
```

El JDK 17 y el Android SDK ya están instalados en la máquina de desarrollo (ver
`client-app/CORRER_EN_EMULADOR.md`); para este comando hay que exportar
`JAVA_HOME` al JDK 17 en esa terminal. Las notificaciones locales sí siguen
andando en Expo Go, así que la UI se puede probar sin esto.

Además, el emulador **no recibe notificaciones remotas**: para probar de punta a
punta hace falta un teléfono real, que es el punto 1.1 de `PENDIENTES_AME`.

---

## Estado

| Pieza | Estado |
|---|---|
| Núcleo (modelos, despacho, cola, canal) | ✅ Completo, 59 tests |
| Simulación (canal de consola + comando + panel en la app) | ✅ Completo |
| Recordatorios de turno 24h / 2h | ✅ Completo |
| Confirmación y cancelación de turno | ✅ Completo |
| Cumpleaños | ✅ Completo |
| Envío masivo (promociones) | ✅ El motor está; falta la pantalla del CRM para disparar una promo |
| Recordatorio diario de rutina | ⚠️ Implementado y **apagado** (`NOTIFICACIONES_RUTINA_DIARIA`) |
| App: registro, permisos, deep link | ✅ Completo, pendiente de los dos requisitos de arriba |
| App: pantalla de preferencias | ❌ La API está; falta la UI |
| Aviso de fechas nuevas | ❌ El evento está definido; falta dispararlo desde el CRM |

El recordatorio de rutina queda apagado a propósito: es un push por día y el
modelo de rutina todavía no tiene frecuencia por paso (punto 2.1 de
`PENDIENTES_AME`), así que hoy el recordatorio sería impreciso para todo lo que no
va todas las noches.
