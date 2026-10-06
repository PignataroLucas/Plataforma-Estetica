# Configuración pendiente fuera del código

**Fecha:** 05/10/2026

Todo lo que falta para que la app funcione completa **no es código**: son altas,
credenciales y trámites en consolas de terceros. Está junto acá porque son tareas
de la misma naturaleza —se hacen de a una sentada, con el navegador abierto— y
porque perseguirlas de a pedazos, intercaladas con desarrollo, es lo que las
hizo durar semanas.

Cada bloque dice **qué desbloquea** y **qué rompe mientras no esté**. Están
ordenados por eso, no por dificultad.

Los valores concretos —URLs, nombres de paquete, rutas de menú— están copiados
acá a propósito: la idea es poder atacar un bloque sin releer ninguna
conversación.

No hay bloque 2: era FCM, y quedó hecho el 05/10/2026. Los demás conservan su
número porque otros documentos los citan.

---

## 1. Tienda Nube — desbloquea comprar desde la app

**Mientras no esté:** la pestaña Tienda es un catálogo que no vende. Los 20
productos de producción dan `comprable: false`, así que no aparece el botón de
agregar al carrito ni el carrito mismo. La app muestra un aviso explicándolo, que
se apaga solo en cuanto el primer producto quede emparejado.

Es el bloque más largo porque tiene a AME adentro. Conviene hacerlo entero en una
sentada con ellos disponibles.

### 1.0 Decidir antes de tocar nada

La app `Ame-App-Clientes` vive hoy en una cuenta de partner **personal**
(`lucasmartinpignataro@gmail.com`). Si alguna vez tiene que estar a nombre de una
empresa, **este es el momento más barato para moverla**: hay cero tiendas
instaladas. Mudarla después implica `client_id` y `client_secret` nuevos, link de
instalación nuevo y una reinstalación coordinada con cada centro.

Mudarla hoy cuesta rehacer un formulario y cambiar dos variables en Railway.

### 1.1 Completar *Datos básicos* en partners.tiendanube.com

Es lo único que separa al proyecto del link de instalación. Está en **Datos
básicos → Editar datos**, en estado *Pendiente*.

Lo que falta:

- **Subcategoría** — sin elegir. Cualquiera bajo Marketing que hable de
  fidelización o clientes.
- **Página de la aplicación** — vacía. `https://www.ameesencial.com.ar` sirve; es
  editable y para una app privada nadie la mira.
- **Permisos** — los acordeones. Contra las cuatro llamadas que el código hace de
  verdad (`GET store`, `GET products`, `POST coupons`, `DELETE coupons/{id}`):

  | Recurso | Permiso |
  |---|---|
  | **Products** | Lectura |
  | **Coupons** | Lectura y escritura |

  Todo lo demás destildado. **Ojo con *Discounts***: en Tienda Nube es un recurso
  distinto de *Coupons* y no lo usamos. Si Coupons separa crear de borrar en dos
  casillas, tildá las dos —el comando de limpieza borra los vencidos.

**Ya está bien y no hay que tocarlo:**

- Las cuatro URLs están cargadas: el callback de OAuth y los tres webhooks de
  privacidad. Verificado el 01/10/2026 contra producción, los cuatro endpoints
  responden.
- La distribución es **"Para tus clientes"**, o sea privada. Eso significa que
  **no hay homologación** que esperar.
- "Integrar en el administrador de tiendas" destildado.

### 1.2 Confirmar que se habilitó el Link de Instalación

Al completar Datos básicos, la tarjeta **Link de Instalación** deja de estar
bloqueada. Ese link es el entregable de todo este tramo: es lo que se le manda a
AME.

Que una app *En desarrollo* se pueda instalar en una tienda real está confirmado
por el panel mismo, que dice textual *"Compartí este link con tu cliente para
instalar esta aplicación en la tienda"*.

### 1.3 Declarar la instalación en el admin de Django

En *Instalaciones de Tienda Nube iniciadas*, antes de que AME instale.

**Dura 15 minutos**, así que va pegado al paso siguiente. El OAuth de Tienda Nube
no acepta un `state`, o sea que el callback vuelve sin saber de qué centro es;
esa declaración es lo único que se lo dice. Sin ella el callback **descarta el
token a propósito**, para no emitir cupones en la tienda de otro centro.

### 1.4 Que AME autorice

Necesitan el usuario administrador de la tienda. Mensaje sugerido:

> Para que la app pueda vender necesito instalar nuestra integración en la tienda
> de Tienda Nube de AME. Les paso un link: lo abre el administrador de la tienda
> y son dos clics.
>
> Qué hace: lee el catálogo de productos para emparejarlos con los de la
> plataforma, y crea cupones de descuento de un solo uso, que son los que la app
> le da a la clienta al comprar. **No lee clientes, ni órdenes, ni datos de
> ventas** —eso sigue llegando por Conto—. Es reversible: si la desinstalan, el
> acceso se corta en el acto. No toca la web, ni el diseño de la tienda, ni los
> precios.

### 1.5 Emparejar los productos

```bash
python manage.py emparejar_variantes_tiendanube             # propone, no escribe
python manage.py emparejar_variantes_tiendanube --aplicar   # escribe los seguros
```

Es conservador a propósito: empareja por nombre con dos escalones de confianza y
un control de precio. Lo que no está seguro lo deja para una persona. Un
emparejamiento errado le pone a la clienta un producto que no eligió.

### 1.6 Cargar el descuento

AME lo decidió el 04/10/2026: **15% con tope de $5.000 por compra**. Se carga en
el CRM, en el segmento general de la app. Hoy está en 0%, así que hasta que se
cargue la app no descuenta nada.

El código ya soporta las dos cosas: el porcentaje y el tope viajan al cupón y a
la app, para que el total del carrito sea el que el checkout va a cobrar.

### 1.7 Verificar

`comprable` tiene que pasar a `true`:

```bash
curl -s "https://plataforma-estetica-production.up.railway.app/api/public/centros/1/productos/?page_size=100"
```

Con eso aparece el botón de agregar al carrito, el carrito, y se apaga el aviso
de la pestaña Tienda.

### 1.8 Las tres mediciones, en la tienda demo

Una sola compra de prueba las responde. Están sin verificar y las tres cambian
plata:

1. **¿El cupón porcentual se aplica sobre el subtotal de productos o sobre el
   total con envío?** Lo preguntó AME y no está documentado en ningún lado.
2. **Con `combines_with_other_discounts: false`, ¿sigue aplicando el 10% de
   transferencia?** AME quiere que el cupón no conviva con las promos de la
   tienda (2x1) **pero sí** con el descuento por transferencia. Son dos perillas
   distintas —la nuestra y la del medio de pago, que tiene su propia casilla del
   lado del comercio— y la hipótesis es que no se pisan. Si se pisaran, hay que
   elegir.
3. **Con un 2x1 activo, ¿el cupón queda efectivamente bloqueado?**

### Plan B, si el alta se traba

Existen las **"Aplicaciones a medida"**: el token lo genera el dueño de la tienda
desde su propio panel, con permisos granulares, privado a esa tienda y sin OAuth
ni link de instalación. Se carga a mano en el admin de Django.

No es el camino recomendado —tira el callback y los webhooks que ya están
construidos, y obliga a repetir el trámite manual en cada centro nuevo— pero
resuelve el caso de AME en una tarde si hace falta.

---

## 3. Salir del sandbox de SES — desbloquea recuperar contraseña

**Mientras no esté:** la recuperación de contraseña funciona, pero **solo contra
direcciones verificadas** —hoy, las de Lucas, `info@ameesencial.com.ar` y
`ame.esencial@gmail.com`—. Una
tester que se olvide la contraseña no recibe nada, y como el endpoint responde
200 siempre (a propósito, para que no se pueda averiguar quién es clienta del
centro), ni ella ni vos se enteran salvo mirando los logs de Railway.

### 3.1 Conseguir que se publiquen los tres CNAME de DKIM

**Esto es un ticket a Tienda Nube, y no tiene nada que ver con el bloque 1.** La
zona DNS de `ameesencial.com.ar` la administra Tienda Nube: el dominio está
delegado a sus nameservers de Route 53, y su panel no permite editar registros —
hay que mandárselos a soporte y los cargan ellos. Es el mismo mecanismo por el
que ya están cargados los MX de Hostmar y el DMARC de Perfit.

```
Tipo:   CNAME
Nombre: mwexuunlwauciiuofidjho6lvdyulxzw._domainkey.ameesencial.com.ar
Valor:  mwexuunlwauciiuofidjho6lvdyulxzw.dkim.amazonses.com

Tipo:   CNAME
Nombre: sf6mksrxl35gmrhiqpch5os5rc25vd2v._domainkey.ameesencial.com.ar
Valor:  sf6mksrxl35gmrhiqpch5os5rc25vd2v.dkim.amazonses.com

Tipo:   CNAME
Nombre: plsfo2wksmils6l3fvd4lgxtdgpi7qs5._domainkey.ameesencial.com.ar
Valor:  plsfo2wksmils6l3fvd4lgxtdgpi7qs5.dkim.amazonses.com
```

Son tres altas nuevas. **No hay que modificar ni borrar nada**, y hay que pedir
explícitamente que dejen como están el CNAME de `_dmarc` (apunta a Perfit) y los
registros de correo de Hostmar.

> **El registro TXT de `_dmarc` que trae el CSV de SES NO se carga.**
> `_dmarc.ameesencial.com.ar` ya es un CNAME hacia Perfit, y un CNAME no puede
> convivir con un TXT en el mismo nombre. Agregarlo rompería el DMARC del centro.

El SPF ya incluye `amazonses.com`, así que esa parte está hecha.

### 3.2 Pedir acceso a producción

El botón recién se habilita cuando el dominio verifica con los CNAME. Hasta
entonces: 200 correos cada 24 h, 1 por segundo, y solo a direcciones verificadas.

### 3.3 Cambiar el remitente al definitivo

Con el dominio verificado se puede usar cualquier dirección de
`@ameesencial.com.ar` sin verificarla una por una, y los mails quedan firmados
con DKIM del dominio en vez del de Amazon.

Hoy sale desde `info@ameesencial.com.ar`: se cambia en `EMAIL_REMITENTE`, en las
variables de Railway.

---

## 4. Apple Developer — desbloquea iOS

**Mientras no esté:** no hay forma de instalar en un iPhone físico. Ni TestFlight
ni ad-hoc: la cuenta paga (US$99/año) es obligatoria y no hay atajo.

Es el **camino crítico de todo lo iOS**, y la aprobación tarda 24–48 h. La
modalidad **individual** es la rápida; la de *organización* pide número D-U-N-S y
puede sumar días.

**Antes de la primera build de iOS, de cualquier perfil:** en Firebase, *Agregar
app → iOS* con el bundle id `com.ameesencial.app`, bajar el
`GoogleService-Info.plist` a `client-app/` y declararlo en `app.json`:

```json
"ios": { "googleServicesFile": "./GoogleService-Info.plist" }
```

Sin ese archivo el plugin de Firebase corta el prebuild de iOS, **incluida la
build de simulador**. En Android no afecta. Son dos minutos y no necesitan la
cuenta de Apple.

Gratis y sin cuenta se puede, mientras tanto:

- **Expo Go** en el iPhone: valida layout, safe areas, gestos y el WebView del
  checkout. No valida ícono, splash ni push.
- **Build de simulador** (`preview-simulador-ios`), si hay una Mac a mano: la app
  compilada de verdad, con ícono y splash, sin push.

Con la cuenta activa: `eas build -p ios --profile production` → `eas submit -p
ios` → grupo interno de TestFlight. El bundle id `com.ameesencial.app` ya está
definido.

---

## 5. Sentry — desbloquea ver los errores de producción

**Mientras no esté:** un error en el teléfono de una tester no deja rastro en
ningún lado.

El backend **ya está cableado** y es inerte sin DSN. Falta:

1. Crear el proyecto en Sentry y sacar el DSN.
2. `SENTRY_DSN` en las variables de Railway.
3. `@sentry/react-native` en la app, que necesita rebuild nativo.

> **`send_default_pii=False` no se cambia.** Está puesto a propósito: este
> backend maneja datos de salud y belleza —fichas, tratamientos, alergias— y
> mandarle a un tercero los cuerpos de request convertiría una herramienta de
> diagnóstico en una fuga de datos sensibles. Con el stack trace y la URL alcanza.

El punto 3 necesita una build nativa propia. Conviene que viaje con la próxima
que haga falta por otro motivo.

---

## 6. El logo real — cierra la identidad

**Mientras no esté:** los íconos son provisorios, generados con Cormorant.

Cuando llegue el vector se reemplazan **cinco archivos de assets** y `app.json`
no se toca. Es el bloque más corto de todos.

---

## 7. Firebase — cerrar lo que quedó abierto

**Mientras no esté:** no se rompe nada; push y Analytics andan. Es higiene, y se
hace en diez minutos.

### 7.1 Restringir la clave de Android en Google Cloud

https://console.cloud.google.com/apis/credentials, proyecto
**`ame-esencial-e3e6a`**, clave **"Android key (auto created by Firebase)"**.

- **Restricciones de API:** "Restringir clave", solo con APIs de Firebase.
  Firebase suele dejarla así de fábrica; confirmarlo.
- **Restricciones de aplicación:** **dejar en "Ninguna" hasta publicar en la Play
  Store.** Con Play App Signing la firma del APK cambia, y restringir solo por el
  SHA-1 de EAS cortaría el push y Analytics sin ningún error visible. Al publicar,
  restringir a *Apps de Android* con el package `com.ameesencial.app` y **los dos**
  SHA-1: el de EAS (`49:BC:A6:07:C4:7F:E1:A1:0B:4B:65:77:57:D4:DD:34:FC:FA:41:36`)
  y el de Play App Signing.

### 7.2 Cerrar la alerta de GitHub

GitHub marcó como secreto expuesto la `api_key` de
`client-app/google-services.json`. No lo es: es un identificador público que
viaja adentro de cada APK, y rotarla no sirve porque la nueva quedaría igual de
expuesta. El secreto de verdad es la clave de cuenta de servicio, que está en EAS
y nunca entró al repo.

En **Security → Secret scanning**: *Close as → False positive*, con el comentario
*"Firebase Android API key, pública por diseño (va dentro del APK). Restringida a
APIs de Firebase en Google Cloud."*

### 7.3 Lo que NO hay que tocar

**"Enhanced security for push notifications"**, en *Access tokens* de expo.dev,
queda **apagado**. Exige un token en cada envío, y el backend hoy no lo manda:
activarlo corta todas las notificaciones sin un solo error a la vista. Se puede
prender el día que el backend mande el token.

### 7.4 Al publicar en la Play Store

En el formulario de *Seguridad de los datos*, declarar Analytics: actividad en la
app e identificadores de la instalación. **No** se usa el ID de publicidad: está
apagado en `firebase.json` y el permiso `AD_ID` se quita del manifest. Lo mismo va
en la política de privacidad.

---

## Por dónde empezar

Si hubiera que elegir un orden:

1. **Los tres CNAME (3.1).** Es un mail y depende de terceros, así que cuanto
   antes salga, antes vuelve. No bloquea nada mientras tanto.
2. **Apple Developer (bloque 4)**, en paralelo, por los 24–48 h de aprobación.
3. **Tienda Nube (bloque 1)**, cuando tengas a AME disponible para una sentada
   larga.
4. **Firebase (bloque 7)**, cuando haya diez minutos libres.
5. **Sentry (bloque 5)**, con la próxima build nativa.
6. **El logo (bloque 6)**, cuando llegue.

Nada de esto bloquea a las testers. La app funciona hoy contra producción: login,
vinculación por código, turnos con reserva, aprobación del centro y cancelación,
notificaciones push, mi rutina, catálogo, perfil, recuperación de contraseña y
Analytics.

---

## Cuota de EAS, para planificar

15 builds de Android y 15 de iOS por mes en el plan gratuito, con 1 de
concurrencia, 45 minutos de timeout y una cola que llegó a tardar dos horas en
arrancar.

Las builds de Android no tienen por qué pasar por ahí. El workflow **EAS Build**
de GitHub Actions, con `donde = runner`, compila en la máquina de GitHub con las
mismas credenciales y firma que EAS: sin cola y sin gastar la cuota. EAS queda
para iOS. Un cambio que es solo JS no necesita build: sale con `eas update`.

---

## Documentos relacionados

- `COMPRA_EN_APP_SPEC.md` — el porqué de cada decisión del bloque 1. Las trampas
  del §6 valen la pena antes de tocar precios.
- `APP_MOBILE_ROADMAP.md` §0 — el estado real de la app y qué falta en features.
