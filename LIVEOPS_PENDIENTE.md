# Configuración pendiente fuera del código

**Fecha:** 06/10/2026

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

## 4. App Store — publicar en iOS

**Mientras no esté:** no hay forma de instalar en un iPhone físico, ni por
TestFlight ni de otra manera.

### 4.1 La cuenta de Apple Developer

US$99 por año. Por lo mismo que en Google (bloque 8), va **individual a nombre de
la titular de AME**: la de organización pide D-U-N-S.

**Diferencia con Google:** en una cuenta individual, el App Store muestra como
vendedor el **nombre legal de la titular**, no "AME esencial". La app se sigue
llamando "AME esencial"; lo que cambia es la línea del vendedor. Que figure la
marca solo se logra con la cuenta de organización.

- Alta en developer.apple.com/programs/enroll, con un Apple ID con verificación
  en dos pasos. La identidad se verifica con el DNI desde la app *Apple
  Developer*. La aprobación tarda 24–48 h.
- Acceso de Lucas: en App Store Connect, *Usuarios y acceso*, con rol
  **Admin**. Una cuenta individual no deja sumar personas al portal de
  certificados; si EAS no puede manejarlos con ese acceso, la alternativa es una
  **API key de App Store Connect** con rol Admin, que la titular genera y se
  carga en `eas credentials`. Confirmarlo cuando la cuenta exista.

### 4.2 Firebase para iOS

**Antes de la primera build de iOS, de cualquier perfil:** en Firebase, *Agregar
app → iOS* con el bundle id `com.ameesencial.app`, bajar el
`GoogleService-Info.plist` a `client-app/` y declararlo en `app.json`:

```json
"ios": { "googleServicesFile": "./GoogleService-Info.plist" }
```

Sin ese archivo el plugin de Firebase corta el prebuild de iOS, **incluida la
build de simulador**. No necesita la cuenta de Apple.

### 4.3 Lo que pide la revisión de Apple

Casi todo es lo mismo que para Google y se prepara una sola vez:

- **Borrar la cuenta desde la app:** hecho (Perfil → Eliminar mi cuenta).
- **Política de privacidad:** la misma URL que en Google.
- **Etiquetas de privacidad** (*App Privacy*) en App Store Connect: los mismos
  datos que *Seguridad de los datos* de Google (8.2).
- **Cuenta de demo** para el revisor, vinculada a un centro.
- **Capturas de iPhone** en el tamaño que pida App Store Connect.
- **Cifrado:** la app solo usa HTTPS. Declarar
  `"infoPlist": { "ITSAppUsesNonExemptEncryption": false }` en `app.json`
  evita la pregunta en cada subida.

Lo que **no** hace falta:

- **"Iniciar sesión con Apple":** es obligatorio solo si la app ofrece login con
  Google o Facebook. Esta usa email y contraseña.
- **Pagos de Apple:** los productos físicos y los servicios presenciales se
  pueden cobrar por fuera, así que el checkout de Tienda Nube y los turnos no
  tienen problema.
- **Prueba con testers:** no hay equivalente a los 14 días de Google.
  TestFlight es opcional: hasta 100 testers internos, o hasta 10.000 externos
  con un link (la primera build externa pasa una revisión corta).

### 4.4 TestFlight y builds

**Decisión pendiente de AME (06/10/2026):** probar primero en Android y recién
con la app validada pagar la cuenta de Apple, o arrancar las dos a la vez.

El plan, cuando se decida:

- **La titular** crea la cuenta, suma a Lucas como Admin en App Store Connect y
  genera una **API key de App Store Connect** con rol Admin (*Usuarios y acceso →
  Integraciones*): el `.p8`, el Key ID y el Issuer ID. Con una cuenta individual
  no se puede sumar a nadie al portal de certificados; con la key, EAS maneja los
  certificados y sube las builds sin pedirle un código de verificación cada vez.
- **Lucas compila en su Mac**, sin cola ni cuota de EAS. Una sola vez: Xcode,
  CocoaPods y fastlane. Después:

  ```bash
  npx eas-cli build --platform ios --profile production --local
  npx eas-cli submit --platform ios --path ./build.ipa
  ```

- **Testers internos** (quienes están en la cuenta): ven la build apenas Apple
  la procesa, sin revisión.
- **Testers externos** (las clientas): entran con un link público e instalan
  desde la app TestFlight. La primera build pasa una revisión corta de Apple
  (alrededor de un día), que pide una descripción de qué probar, un mail de
  contacto y una cuenta de demo. Cada build vence a los 90 días.
- **Los testers de iPhone no cuentan para Google:** los 12 del bloque 8 son de
  Android. Las dos pruebas corren en paralelo, cada una con su gente.
- **La primera build de iOS puede fallar:** nunca se compiló para iOS, y
  Firebase cambia cómo se arman las dependencias (`useFrameworks`). En la Mac se
  depura rápido.
- **Junto con el plist del 4.2,** y no antes, va
  `"infoPlist": { "ITSAppUsesNonExemptEncryption": false }` en `app.json`.
  Tocar `app.json` cambia el runtime version: hecho antes de tiempo, las
  actualizaciones OTA dejarían de llegar a los APK ya instalados.

La clave de push de Apple (APNs) la genera EAS en la primera build.

Mientras tanto, gratis y sin cuenta, en la Mac: el **simulador de iOS**, con
`preview-simulador-ios` o `npx expo run:ios`, una vez que esté el plist del 4.2.
Valida layout, safe areas, gestos y el WebView del checkout; no valida push.

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

---

## 8. Play Store — publicar en Android

**Estado (06/10/2026):** la titular de AME está creando la cuenta de desarrollador
con `Guia cuenta Google Play - AME.pdf`. Lucas entra como **Administrador**.

### 8.1 La cuenta

Personal, porque AME no tiene D-U-N-S. US$25, un solo pago. Google verifica la
identidad y un teléfono Android; tarda unos días.

Por ser una cuenta personal **nueva**, Google exige la prueba cerrada del 8.3
antes de publicar.

### 8.2 Antes de la prueba cerrada

Google pide completar todo esto antes de publicar en cualquier pista, incluida la
cerrada:

- **Política de privacidad publicada.** El borrador está en
  `POLITICA_DE_PRIVACIDAD.md`, en revisión de AME y de un abogado. Va en
  `ameesencial.com.ar` junto con la página *Eliminación de la cuenta*: Google
  pide las dos URLs.
- **Borrar la cuenta desde la app:** hecho. Falta que llegue a producción.
- **Link a la política desde Perfil,** cuando tenga URL.
- **Pendiente de la revisión legal:** si hace falta aceptar la política al
  registrarse. Hoy la app no lo pide.
- **Seguridad de los datos:** declarar cuenta (email, nombre, teléfono), turnos,
  compras, notificaciones y Analytics (actividad en la app e identificadores de
  la instalación). **No** se usa el ID de publicidad: está apagado en
  `firebase.json` y el permiso `AD_ID` se quita del manifest.
- **Acceso a la app:** toda la app está detrás del login, así que hay que darle
  a Google una cuenta de prueba vinculada a un centro.
- **Cuestionarios:** clasificación de contenido, público mayor de 18, sin
  anuncios, categoría *Belleza*.
- **Ficha de la tienda:** nombre, descripción corta (80 caracteres) y larga,
  ícono de 512×512, gráfico de 1024×500 y al menos 2 capturas. El ícono depende
  del bloque 6.

### 8.3 La prueba cerrada: 12 testers durante 14 días

- **Al menos 12 personas, mejor 15,** con Android y cuenta de Google, anotadas
  sin interrupción durante 14 días. Los iPhone no sirven.
- **Personas reales.** Emuladores o varias cuentas en un mismo teléfono se ven
  como una prueba armada: arriesgan el rechazo y la cuenta de la titular. Una
  cuenta de Lucas en el emulador entre las 12 no es problema.
- **Uso:** no hay mínimo. Que abran la app algunas veces por semana y prueben
  entrar con el código, la tienda, reservar, Mi rutina y los avisos. El
  feedback, por un grupo de WhatsApp: va al formulario del 8.4.
- **Los turnos que reserven son pedidos reales** en producción. Crear un
  servicio "Prueba app" o avisarle a AME que los rechace.
- **Build:** perfil `production` (AAB), por el workflow de GitHub con
  `donde = runner`. El **primer AAB se sube a mano** en Play Console.

### 8.4 Pedir acceso a producción

Al cumplirse los 14 días, desde el *Panel* de Play Console. El formulario
pregunta cómo se consiguieron los testers, cuánto usaron la app, qué feedback
dejaron y qué se cambió a partir de eso. Google tarda alrededor de una semana.

### 8.5 Después de publicar

- **Restringir la clave de Android** con el SHA-1 de Play App Signing (7.1).
- **Opcional, `eas submit`:** para no subir cada AAB a mano. Necesita una clave
  de cuenta de servicio de Google Play, que se carga en `eas credentials` →
  *Submissions*.

---

## Por dónde empezar

Si hubiera que elegir un orden:

1. **Play Store (bloque 8).** Es el camino crítico para publicar: la cuenta
   está del lado de AME, y en paralelo corren la revisión legal de la política
   y la prueba de 14 días.
2. **Los tres CNAME (3.1).** Es un mail y depende de terceros, así que cuanto
   antes salga, antes vuelve.
3. **App Store (bloque 4)**, a la par del 8 si se publica en iOS al mismo tiempo.
4. **El logo (bloque 6)**, antes de armar las fichas de las tiendas.
5. **Tienda Nube (bloque 1)**, cuando AME pueda dedicarle una sentada larga.
6. **Firebase (bloque 7)**, cuando haya diez minutos libres.
7. **Sentry (bloque 5)**, con la próxima build nativa.

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
- `POLITICA_DE_PRIVACIDAD.md` — el borrador de la política y de la página de
  borrado de cuenta, para los bloques 4 y 8.
