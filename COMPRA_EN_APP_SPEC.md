# Compra desde la app, con Tienda Nube por detrás

**Estado:** terminado y **probado de punta a punta contra la tienda demo el
30/08/2026**, incluida la detección del retorno. Falta instalarlo en la tienda
real de AME, confirmar que Conto manda el cupón (7.1) y las dos decisiones del
centro (7.2 y 6.1).
**Fecha:** 11/08/2026, con notas del 15, 17 y 30/08/2026

Documento de handoff: está escrito para que se pueda implementar **sin haber
participado de la conversación donde se decidió**. Todo lo que dice "verificado"
se comprobó contra el código, contra la documentación de Tienda Nube o contra
una respuesta del equipo de Conto, en la fecha de arriba.

---

## 1. Qué se quiere y por qué

Que una clienta pueda **comprar un producto sin salir de la app**, con tres
condiciones que vienen del centro:

1. **Sin redirecciones al navegador.** Si la compra empieza en la app, termina
   en la app.
2. **Un descuento por comprar desde la app.** Es el incentivo para que la
   clienta la instale y la use en vez de ir a la web.
3. **Ofertas segmentadas.** Poder darle un porcentaje distinto a una clienta VIP.

Y una cuarta condición que no puso el centro pero sin la cual esto no se puede
evaluar: **saber cuánto vende la app**. Si dentro de tres meses no se puede
separar lo que vendió la app de lo que vendió la web, no hay forma de decir si
valió la pena.

Importa porque los productos son la **fuente principal de ingresos del centro**.
El catálogo de la app ya está construido; esto es lo que lo convierte en ventas.

---

## 2. Estado verificado

### Lo que ya existe

| Pieza | Dónde | Estado |
|---|---|---|
| Grilla del catálogo | `client-app/src/app/(tabs)/tienda.tsx` | ✅ Con foto, marca, precio y badge de oferta |
| Ficha de producto | `client-app/src/app/producto/[id].tsx` | ✅ Foto, qué es, beneficios, precio |
| Endpoints públicos | `apps/public_api/views.py` | ✅ Listado y detalle, con scope por centro |
| Fotos en S3 | bucket `ame-catalogo` | ✅ URLs públicas absolutas |
| Sistema de ofertas | `Producto.en_oferta`, `precio_oferta`, `Oferta`, `VentaOferta` | ✅ Existe y la app ya lo muestra |
| Sync de ventas de TN | `apps/integraciones/` vía Conto | ✅ Andando en producción |
| `origen_venta` y `app_origen` | endpoint de ventas de Conto | ✅ Agregados a pedido, 08/08/2026 |
| `cupon` y `descuento_cupon` | endpoint de ventas de Conto | ⚠️ Agregados 11/08/2026, **sin compilar** — ver 7.1 |

### Lo que se construyó después de escribir esto

| Pieza | Dónde | Punto |
|---|---|---|
| Campos crudos de Conto en `ContoSale` | `apps/integraciones/sync.py` | 5.6 |
| Carrito en la app | `client-app/src/stores/carrito.ts`, `src/app/carrito.tsx` | 5.4 |
| `SegmentoApp`, descuento por clienta y endpoint autenticado | `apps/clientes/`, `apps/client_api/`, CRM y app | 5.8 |
| App de Tienda Nube, OAuth y token por centro | `apps/integraciones/tiendanube.py`, `TiendanubeIntegration` | 5.1 |
| Ids de Tienda Nube en `Producto` y emparejador por nombre | `emparejar_variantes_tiendanube` | 5.2 |
| `CuponApp`, emisión y limpieza programada | `apps/integraciones/cupones.py` | 5.3 |
| Preparación de la compra y checkout en WebView | `apps/integraciones/compra.py`, `client-app/src/app/checkout.tsx` | 5.5 |
| Atribución de la venta al importarla | `SalesImporter._atribuir` | 5.6 |
| Callback de OAuth y los tres webhooks de privacidad | `apps/integraciones/tiendanube_views.py`, `instalacion.py`, `privacidad.py` | 5.1 |
| Limpieza de cupones por cron | `tasks.limpiar_cupones_app`, `railway.cupones.cron.json` | 6.5 |
| Simulador de la vuelta de la venta | `simular_venta_app` | 5.6 |
| Medición de ventas de la app | `apps/analytics/ventas_app.py`, `VentasAppSection` | 5.7 |

### Lo que no existe

- **La instalación en la tienda real de AME.** Todo lo demás se ejercitó
  contra la de demostración, que ya tiene medio de pago y catálogo.
- **La confirmación de que Conto manda el campo `cupon`** (7.1). Es lo único
  que el simulador no puede probar, porque ahí el campo se lo ponemos
  nosotros.
- **El ensayo del OAuth contra la demo**: desinstalar y reinstalar la app,
  que es lo que hace disparar el callback con un código real y el webhook de
  borrado. Ojo: reinstalar emite un token nuevo y mata el de desarrollo.

### El dato que manda sobre la arquitectura

**El centro ya vende online.** Del `INTEGRACION_CONTO_SPEC.md`:

> El centro opera Conto... **Conto se actualiza automáticamente con cada venta de
> Tienda Nube**: guarda el precio, descuenta el stock y registra el costo.

O sea que ya existe un checkout que funciona, con pagos, stock real y envíos
resueltos. Todo lo que sigue parte de no reconstruir eso.

---

## 3. Decisiones tomadas

Están cerradas. Si algo se reabre, que sea por un motivo nuevo.

| Decisión | Motivo |
|---|---|
| **Se usa el checkout de Tienda Nube, embebido en un WebView** | Ver 3.1. Es más barato de construir *y* más barato por venta. |
| **WebView, no redirección al navegador** | La clienta no sale de la app: no hay barra de direcciones ni salto de contexto. El marco de la pantalla es nuestro; solo el contenido es de TN. |
| **El descuento se aplica con un cupón único de un solo uso** | Ver 3.2. Resuelve descuento, segmentación y atribución con un solo mecanismo. |
| **La atribución NO se hace con parámetros en la URL** | Verificado: el checkout de TN ignora variables personalizadas agregadas a mano en la URL. |
| **No se toca el stock de la plataforma** | El stock de la plataforma no es real (es el del depósito). Quien valida es Tienda Nube, que tiene el stock del mostrador. |

### 3.1 Por qué el checkout de Tienda Nube y no uno propio

Se evaluaron tres caminos:

| | Desarrollo | Comisión por venta | Estética |
|---|---|---|---|
| **WebView del checkout de TN** | ~1,5-2 semanas | La que ya se paga hoy | TN desde "Comprar" |
| Cobro propio + orden por API de TN | 3-5 semanas | MercadoPago **+ 0,7-2% de TN** | AME salvo la pantalla de pago |
| Checkout propio con Checkout API | 5-8 semanas | MercadoPago **+ 0,7-2% de TN** | AME en todo |

El dato que cierra la discusión es la segunda columna. Tienda Nube aplica un
costo por transacción de entre **0,7% y 2%** sobre las ventas con medios de pago
externos, y una orden creada por API y marcada como paga por fuera de su
checkout entra en esa categoría. Bonificado solo con Pago Nube.

Sobre un producto de $20.900, ese 2% son unos **$418 por venta, para siempre**.
Los caminos caros cuestan más de construir **y** más por cada venta. Normalmente
se paga desarrollo para ahorrar comisión; acá se pagarían las dos cosas.

> **Pendiente de confirmar.** La cifra del 0,7-2% viene de fuentes secundarias
> vía el equipo de Conto, no de una respuesta oficial sobre el plan del centro.
> Es un indicio fuerte y es la base de esta decisión, así que hay que
> confirmarlo. Ver §7.

### 3.2 Por qué el cupón resuelve tres problemas a la vez

El cupón nació como forma de aplicar el descuento, pero termina resolviendo
también la atribución y una fuga que iba a aparecer sola.

**Como descuento.** La API de Tienda Nube permite crear cupones por porcentaje o
monto fijo, con vigencia, tope de usos, monto mínimo y restricción a productos o
categorías (verificado en `POST /coupons`).

**Como atribución.** El objeto `Order` de Tienda Nube trae `coupon` (cada
elemento con `code`, `type` y `value`) y `discount_coupon` (el monto descontado
por el código, separado de `discount_gateway`). Si el único que emite esos
códigos es la app, entonces **una venta que llega con uno de nuestros códigos es,
por definición, una venta de la app**. No hace falta que TN soporte nada nuevo.

Conto ya lo reenvía, crudo y sin interpretar:

```json
"gateway_origen": "mercadopago",
"origen_venta": "store",
"app_origen": null,
"cupon": "BIENVENIDA10",
"descuento_cupon": 1500.00
```

Con más de un cupón, `cupon` trae los códigos separados por coma; sin cupón,
`null`. Nótese el `origen_venta: "store"` del ejemplo: es exactamente lo que va a
llegar por este camino, y por eso la atribución va por el código y no por ahí
(6.3).

**Como candado.** Un cupón general tipo `APP10` termina en un grupo de WhatsApp
en una semana y se lo aplica cualquiera desde la tienda web: se pierde el margen
y se pierde el incentivo a instalar la app. Uno de un solo uso, con código
impredecible y vigencia corta, no.

**La limitación a conocer:** la API **no permite atar un cupón a un cliente o
email concreto**. Solo tiene `first_consumer_purchase`, que es otra cosa. Por eso
el mecanismo es un código único por compra y no un cupón por clienta.

---

## 4. Arquitectura

<!-- DIAGRAMA -->

El recorrido completo, con quién hace qué:

1. **La clienta arma el carrito en la app.** Vive en el dispositivo (zustand, ya
   está en el stack). No se persiste en el backend.

2. **Toca "Comprar".** La app le pide a nuestro backend que prepare la compra.

3. **Nuestro backend calcula el descuento** que le corresponde: el general de la
   app, o el de su segmento si tiene uno. La regla vive en la plataforma, no en
   Tienda Nube (5.8).

4. **Nuestro backend crea un cupón en Tienda Nube** con ese porcentaje,
   `max_uses: 1` y vigencia corta. Guarda el código, a qué clienta se lo dio y
   cuándo. **El token de Tienda Nube nunca sale del backend.**

5. **El backend devuelve la URL del checkout** con el carrito y el cupón
   aplicados, y la app la abre en un WebView, dentro de su propio marco.

6. **La clienta paga en el checkout de Tienda Nube**, con los medios que el
   centro ya tiene configurados. Nada que configurar del lado de la app.

7. **Tienda Nube valida el stock, cobra y crea la orden.** Si no hay unidades, no
   se cobra: el stock real lo tiene TN, no nosotros.

8. **El backend detecta la URL de retorno**, cierra el WebView y muestra la
   pantalla de confirmación de AME. La clienta no ve la página de gracias de TN.

9. **El centro despacha** desde su panel de Tienda Nube, con el flujo de siempre.

10. **Conto importa la venta** como importa cualquier otra de TN, y el sync la
    baja a la plataforma como `Transaction`, con el medio de pago ya mapeado
    (§5.2 del spec de Conto).

11. **La atribución se resuelve al importar**: si la venta trae uno de nuestros
    códigos de cupón, es una venta de la app y sabemos de qué clienta.

---

## 5. Implementación

### 5.1 App de Tienda Nube (OAuth)

Hay que registrarse como partner de Tienda Nube y crear una app que el centro
instala en su tienda. De ahí sale el token que autoriza a crear cupones y leer
órdenes.

Esto **reintroduce** algo que el spec de Conto había evitado a propósito:

> **Decisión:** no se integra contra la API de Tienda Nube. Se integra contra
> Conto... Eso evita el registro como partner de TN, el OAuth, la validación
> HMAC, los webhooks con timeout de 3s, los rate limits...

Sigue siendo válido **para las ventas**: se leen por Conto. Lo que se agrega acá
es un canal chico y acotado hacia TN, solo para **emitir cupones**. No se leen
productos, ni órdenes, ni stock por esa vía.

El token se guarda cifrado, por centro, con el mismo patrón que ya usa
`ContoIntegration` para su token.

#### El trámite

*Verificado contra la documentación de Tienda Nube el 15/08/2026.*

Lo hace quien desarrolla, no el centro. En **partners.tiendanube.com** se crea
la cuenta de partner y desde ahí "Crear aplicación": nombre, tipo de
disponibilidad y permisos. El `client_id` y el `client_secret` salen de la
sección "Claves de Acceso" de esa misma pantalla.

**El tipo de disponibilidad es la decisión que importa:**

| | Alcance | Homologación |
|---|---|---|
| Tienda de Aplicaciones | Pública, listada en el marketplace de TN | Sí |
| **Para sus clientes** | Solo los comercios que se elijan | La doc dice que no |

Acá corresponde la privada: es una app para un comercio. Si eso se sostiene no
hay aprobación de terceros que esperar, y el tiempo de calendario ajeno que
supone el §8 casi desaparece.

> **Reserva.** La página de homologación de la misma documentación dice que
> todas las apps pasan por algún tipo de validación, con distinto rigor según la
> categoría. Es lo primero a confirmar al entrar al portal.

#### Cómo queda vinculada la tienda del centro

No se vinculan dos cuentas: se vincula **una app con una tienda**. Funciona
sobre la tienda que el centro ya tiene, sin migrar nada.

1. El centro abre `https://www.tiendanube.com/apps/{app_id}/authorize` con una
   cuenta con permisos de administrador sobre su tienda.
2. Autoriza los permisos que la app declara.
3. TN redirige a nuestra URL de retorno con un `code` que **dura 5 minutos**.
4. El backend lo cambia por el token: `POST` a
   `https://www.tiendanube.com/apps/authorize/token` con `client_id`,
   `client_secret` y `code`.
5. La respuesta trae el `access_token` y el `user_id`, que es el id de la tienda.

**El token no vence**: vale hasta que el centro desinstale la app o hasta que se
genere otro. No hay refresh que implementar, es guardarlo cifrado y listo.

Dos consecuencias prácticas:

- **La URL de retorno tiene que ser pública** y apuntar al backend de
  producción, no a localhost. Para desarrollo, la tienda de demostración (§9)
  contra esa misma URL.
- **Es reversible y acotado.** El centro desinstala y el token muere. La app
  pide solo los permisos que se tilden: acá alcanza con los de cupones, no hace
  falta pedir productos, órdenes ni clientes — las ventas se siguen leyendo por
  Conto.

> **NubeSDK.** Es obligatorio para homologar apps nuevas desde el 05/06/2026, y
> hay bloqueo por front-end para las apps que inyectan scripts en la tienda, con
> retiro progresivo desde el 30/10/2026. Esta app no inyecta nada —es servidor a
> servidor para emitir el cupón, más el checkout de siempre dentro de un
> WebView—, así que a priori no la alcanza. Confirmarlo al dar el alta.

> **Hecho el 17/08/2026: el callback y los tres webhooks.**
> `apps/integraciones/tiendanube_views.py`, con la lógica de vinculación en
> `instalacion.py` —compartida con `vincular_tiendanube`, que sigue siendo el
> camino de atrás— y la de privacidad en `privacidad.py`.
>
> **El hallazgo que le dio la forma: el OAuth de Tienda Nube no acepta un
> `state`.** Su URL de autorización recibe solo el id de la app y el callback
> vuelve solo con `code`. Verificado en su documentación y, sobre todo, en su
> SDK oficial de PHP, que ni lo manda ni lo lee. O sea que **cuando el token
> vuelve no hay nada en el pedido que diga de qué centro es**, y esto es
> multi-inquilino.
>
> La salida, en dos pasos y sin adivinar nunca:
>
> 1. **Reinstalación o reautorización:** el `store_id` que devuelve el
>    intercambio ya tiene integración, así que el centro está fuera de
>    discusión. Es el caso que más va a pasar, y el que hoy rompe en silencio —
>    reinstalar emite un token nuevo y el viejo deja de emitir cupones.
> 2. **Primera instalación:** hay que declararla antes. Se hace desde
>    *Instalaciones de Tienda Nube iniciadas* en el admin de Django, que
>    redirige derecho a Tienda Nube y deja anotado qué centro está instalando.
>    Esa anotación dura 15 minutos.
>
> Con cero anotaciones abiertas, o con más de una, el callback **descarta el
> token y no vincula nada**. Adivinar costaría emitir cupones en la tienda de
> otro centro; reinstalar cuesta un click.
>
> Va al admin y no al CRM porque el CRM no tiene pantalla de integraciones —el
> token de Conto se carga por el mismo lugar—. No se expuso como endpoint: sin
> pantalla que lo llame sería una ruta que existe solo para tener tests, y la
> URL de autorización es una constante que se puede pasar a mano.
>
> **Los tres webhooks** (`store/redact`, `customers/redact`,
> `customers/data_request`) validan HMAC-SHA256 del **cuerpo crudo** contra el
> `client_secret`, en el header `x-linkedstore-hmac-sha256`. Sin secreto
> configurado contestan 401 en vez de dejar pasar: son endpoints públicos y uno
> de ellos desactiva la integración del centro. Contestan sin salir a la red,
> porque el timeout es de 3 segundos y un no-2xx se reintenta 16 veces durante
> 48 horas.
>
> Qué borra cada uno, que es la decisión de fondo:
>
> - `store/redact` borra el token y apaga la integración. **No borra la fila ni
>   los `CuponApp`**: el FK es CASCADE y se llevaría puesta la historia de
>   cupones emitidos, que es sobre lo que se apoya el §5.7. Lo que Tienda Nube
>   pide borrar es su dato, que es la credencial.
> - Los dos de comprador **no borran nada**, y quedan registrados en
>   `TiendanubePrivacyRequest` para que los conteste una persona. Esta app pide
>   leer productos y escribir cupones: nunca leyó clientes ni órdenes de la
>   tienda, así que no hay dato de Tienda Nube acá para borrar. La ficha de la
>   clienta en el CRM es dato del centro, no de la tienda.
>
> **Falta un trámite que no es código:** cambiar la URL de redirección en el
> panel de partners, que todavía apunta a la página del panel, por
> `https://plataforma-estetica-production.up.railway.app/api/integraciones/tiendanube/oauth/callback/`,
> y cargar las tres URLs de webhook. Hasta que eso pase, esto no se ejercita
> contra Tienda Nube de verdad.

### 5.2 Mapeo producto ↔ variante de Tienda Nube

Para armar la URL del carrito hace falta el identificador de la variante en TN.
Hoy no existe.

- Campo nuevo en `Producto`: `tiendanube_variant_id`.
- Comando de emparejamiento por nombre, con el mismo criterio conservador que
  `emparejar_sku_conto`: propone, y solo escribe los matcheos seguros. Ese
  comando ya existe y es el molde exacto a copiar.
- El campo se puede completar a mano desde el CRM para los que no matcheen.

**Un producto sin `tiendanube_variant_id` no se puede comprar.** La ficha tiene
que ocultar el botón, no fallar al tocarlo.

> **Corrección del 15/08/2026, verificada contra la tienda demo: el carrito se
> arma con el ID DE PRODUCTO, no con el de variante.** Mandando el id de
> variante, Tienda Nube contesta *"Este producto no está disponible"*; con el de
> producto, agrega. Se guardan los dos: `tiendanube_product_id` es el que arma
> el carrito y decide si el producto se puede comprar, y
> `tiendanube_variant_id` identifica cuál unidad cuando el producto tiene más de
> una. El emparejador escribe ambos.

> **Mejorado el 30/08/2026: el emparejador ya no depende solo del nombre.**
> Ahora mira, en este orden:
>
> 1. **SKU exacto.** Es certeza, no parecido: dos productos con el mismo SKU son
>    el mismo producto, sin importar cómo esté escrito el nombre de cada lado.
>    Estos no pasan por similitud ni por el testigo del precio. El SKU **ya se
>    leía de Tienda Nube y no se usaba** — se imprimía en el reporte de dudosos y
>    nada más. Un SKU repetido del otro lado no se usa: si el identificador que
>    debía ser único aparece dos veces, elegir uno es adivinar.
> 2. **Nombre**, con los mismos dos escalones de siempre.
> 3. **El precio como testigo.** No empareja: solo desconfía. Un match que
>    convence por nombre pero cuyo precio difiere más del 50% baja a decisión
>    humana. La tolerancia es amplia a propósito, porque los precios se desfasan
>    solos (§6.2) y en Tienda Nube puede haber una promoción; solo tiene que
>    atajar disparates. **Nunca frena un match por SKU.**
>
> Probado contra la tienda de demostración: **pasó de 4 a 5 emparejamientos**, y
> el quinto es el que el nombre no podía resolver —`Bruma Hidratante Y Calmante
> - 150 ML` contra `Bruma Descongestiva x150ml`—, unidos por SKU. El reporte
> ahora distingue `SKU` de `100%`: una coincidencia de identificador y un
> parecido perfecto de nombre no valen lo mismo para quien revisa la lista.
>
> Esto importa sobre todo para el catálogo real de AME, donde los nombres de los
> dos lados casi nunca coinciden palabra por palabra.

### 5.3 Emisión de cupones

Un modelo nuevo, `CuponApp`, con: código, clienta, porcentaje, fecha de emisión,
vencimiento, y si se usó. El porcentaje sale de 5.8.

- Se emite al tocar "Comprar", no antes.
- `max_uses: 1` y vigencia corta (una hora alcanza).
- Código impredecible, no secuencial, **con prefijo `APP-`**. El prefijo importa:
  ver 5.7.
- **Limpieza**: los que vencen sin usarse se borran de TN con un comando
  programado, con el mismo patrón de cron que ya usan las notificaciones.

> **El prefijo `APP-` funciona. Verificado contra la API el 15/08/2026**, con
> un cupón real creado en la tienda demo:
>
> ```json
> {"id": 67713598, "code": "APP-PRUEBA1", "type": "percentage", "value": 15,
>  "max_uses": 1, "combines_with_other_discounts": true, "used": 0}
> ```
>
> Lo aclaro porque la documentación de `POST /coupons` dice que el `code` solo
> admite caracteres alfanuméricos, y eso haría inválido el guion. **La API real
> lo acepta.** Vale más la prueba que la doc, pero conviene saber que no
> coinciden: si algún día TN empieza a validarlo, el prefijo pasa a ser `APP`
> pegado y hay que revisar cómo se agrupan en el reporte de Conto (5.7).
>
> La respuesta confirma además los campos sobre los que se apoya este punto
> —`max_uses`, `min_price`, `products`, `start_date`/`end_date`,
> `first_consumer_purchase`— y trae dos que el spec no contemplaba:
> `max_uses_per_client` y **`max_discount_amount`**, un tope en pesos al
> descuento. Ese segundo puede servir para acotar el riesgo de un porcentaje
> alto sobre un carrito grande.

### 5.4 Carrito en la app

Store de zustand, pantalla de carrito, y el botón "Agregar" en la ficha. Nada
que se persista del lado del servidor: si la clienta cambia de teléfono, pierde
el carrito, y está bien.

> **Hecho el 15/08/2026.** `client-app/src/stores/carrito.ts` y
> `src/app/carrito.tsx`. Tres cosas que decidió la implementación y el punto no
> decía: el carrito se descarta si cambia el centro y se vacía en login y
> logout (vive en memoria, y sin eso la próxima clienta del mismo teléfono ve el
> pedido de la anterior); la pantalla relee el catálogo y prefiere el precio
> fresco (6.2); y **tampoco sobrevive a cerrar la app** — persistirlo localmente
> pide `@react-native-async-storage/async-storage`, que es una dependencia
> nueva y quedó sin agregar.

### 5.5 WebView y retorno

El WebView va dentro de un screen propio, con el header de AME: una X para
cerrar, el título, y un candado. Sin barra de direcciones.

El retorno se detecta por URL: cuando TN llega a su página de gracias, se cierra
el WebView y se muestra la confirmación de AME. **Si eso se maneja mal, la
clienta ve un parpadeo de página web**, que es exactamente la sensación que se
quiere evitar.

> **Hecho el 30/08/2026, y medido.** Desde "Comprar" hasta el cupón aplicado
> pasan **unos 18 segundos** en el emulador: dos cargas de página, un pedido por
> producto, el arranque del checkout de Tienda Nube y recién ahí la escritura
> del cupón. Son inherentes al camino, no un defecto optimizable.
>
> El problema no era la demora sino **qué veía la clienta durante esos
> segundos**: el total sin descuento, que después bajaba solo. Una versión suave
> del §6.1 — acá el precio baja, así que no pierde la venta, pero la acostumbra
> a ver el número alto primero y el día que el cupón falle no va a notar que no
> bajó.
>
> Se resolvió con una **cortina**: el WebView se monta y trabaja detrás de una
> pantalla nuestra que dice "Preparando tu compra" con el porcentaje, y se
> levanta cuando llega `cupon-ok`. La clienta nunca ve el precio equivocado.
>
> Y se corrigió un defecto que la medición destapó: **la app se rendía antes que
> su propio script**. El temporizador que muestra el código para pegar a mano
> estaba en 20 segundos, contra un recorrido de 18 y un presupuesto del script
> —15 s para el link, 8 para el campo, 10 para verificar, por hasta tres
> intentos— muy superior. Ahora son 45 segundos, y el temporizador es una red de
> contención: lo que decide es el mensaje del script.

### 5.6 Consumir el cupón desde el sync

Depende de que Conto exponga el código del cupón en el payload de la venta
(§7). Cuando lo haga:

- Guardarlo crudo en `ContoSale`, sin interpretar, junto a `origen_venta` y
  `app_origen`. **Hecho el 15/08/2026** (7.1).
- Al importar, si el código coincide con un `CuponApp`, marcar la venta como
  originada en la app y vincularla a la clienta. **Hecho el 17/08/2026.**

> Detalles que resolvió la implementación:
>
> - **Se atribuye antes de los early returns.** Una venta de un canal que no
>   importamos, o todavía impaga, igual usó el cupón: si no se marcara, la
>   limpieza lo borraría de Tienda Nube creyendo que venció sin usarse.
> - **Es idempotente.** Reprocesar un voucher no mueve la fecha de uso, que es
>   de donde sale cuánto tarda una clienta entre "Comprar" y pagar.
> - **La clienta del cupón se usa solo como respaldo.** Si el email o el
>   teléfono del comprador resuelven una ficha, gana esa: son datos de quien
>   compró de verdad, y el código pudo haber circulado (6.7). La atribución de
>   la venta a la app no depende de eso — va por el vínculo al cupón.

### 5.7 Analytics

Con lo anterior, el módulo de analytics puede responder: cuánto vendió la app,
qué productos, a qué clientas, y con cuánto descuento. Esa es la métrica que
justifica el proyecto y la que decide si conviene invertir en el checkout propio
más adelante.

La agregación fina la hacemos nosotros, contra `CuponApp`: sabemos cada código
emitido, a qué clienta y cuándo, así que podemos cruzarlo con datos que Conto no
tiene.

**Ojo con el reporte de cupones de Conto.** Conto tiene *Reportes → Ventas →
Ventas por cupón*, que muestra por período qué cupones se usaron, cuánto facturó
cada uno, cuánto costó en descuento, y el ticket promedio con cupón contra sin
cupón. Está pensado para campañas: pocas filas, muchas ventas cada una.

**Un cupón por compra lo rompe**: pasa a haber una fila por venta, todas con un
uso, y deja de ser un reporte. De ahí el prefijo `APP-` del 5.3 — hace que los de
la app se puedan agrupar o excluir. Vale avisarle a Conto que esto viene, porque
les va a pasar con cualquier cliente que emita cupones por transacción.

Y quedarse con la métrica que ellos proponen: **ticket promedio con cupón contra
sin cupón**. Es mejor pregunta que "cuánto vendió la app", porque distingue las
compras que el descuento trajo de las que iban a pasar igual y solo le costaron
margen al centro.

> **Hecho el 30/08/2026.** `GET /api/analytics/dashboard/ventas-app/`, con el
> cálculo en `apps/analytics/ventas_app.py` y la sección `VentasAppSection` en
> la página de Analytics del CRM.
>
> Devuelve cuatro bloques: el **resumen** (facturado de la app contra el resto,
> ticket promedio de cada lado, descuento otorgado y participación), los
> **productos** que vende la app, las **clientas** que compran por ahí, y los
> **cupones** —emitidos, usados, sin usar y conversión—.
>
> Detalles que resolvió la implementación:
>
> - **No hay campo de origen en `Transaction`.** La atribución sigue viviendo
>   solo en `ContoSale.cupon_app`, y las consultas llegan por ahí. Copiarla a la
>   tabla financiera daría dos lugares que discrepan al reprocesar un
>   comprobante.
> - **`cache_page` no se usa acá, y es a propósito.** Ese decorador cachea por
>   URL y no por usuario; como el centro sale del usuario, la URL es idéntica
>   para todos y el primero en pedirla le deja sus números al siguiente. Se
>   descubrió porque los tests de este módulo se pisaban entre sí. **El resto de
>   las vistas de analytics sí lo usan** y quedan expuestas cuando se las llama
>   sin `sucursal_id`: es un problema anterior a este trabajo y sin resolver.
> - **El join a `Transaction` va por subconsulta, no por `distinct`.**
>   `conto_sales` es un many-to-many y `.distinct()` no de-duplica agregados:
>   aplica al SELECT final, que después de `values().annotate()` ya incluye el
>   `Sum`.
> - La métrica de **cupones emitidos contra usados** es la única del tablero que
>   Tienda Nube no puede dar: allá el cupón no existe hasta que se usa. Cada uno
>   sin usar es un carrito abandonado en el checkout.

### 5.8 Los segmentos y el descuento de cada clienta

**La segmentación vive en la plataforma, no en Tienda Nube.** No es preferencia:
la API de TN no permite atar un cupón a un cliente (3.2), así que TN no tiene ni
puede tener el concepto de "esta clienta es VIP". Solo recibe un código con un
porcentaje ya resuelto.

En el CRM:

- Un modelo `SegmentoApp` con nombre, porcentaje y activo.
- Una relación desde `Cliente`. **No un porcentaje suelto por clienta**: el día
  que VIP pase de 15% a 20% hay que editar un registro, no cuarenta.
- Un segmento por defecto, que es el descuento general de la app.

La asignación arranca a mano, desde la pantalla de la clienta en el CRM. Más
adelante puede ser por regla —la plataforma ya tiene el historial de gasto en el
módulo financiero—, pero eso es otro trabajo.

**El precio que muestra la app tiene que ser el segmentado.** Y acá aparece una
consecuencia: el catálogo hoy es público y sin autenticación, así que devuelve el
precio de lista. Si la grilla muestra $20.900 y el checkout cobra $17.700,
volvemos a la trampa 6.1 con el signo invertido.

La salida: con la clienta logueada, la app pide su porcentaje al API de cliente
—que sí está autenticada— y lo aplica a los precios que muestra. **Ese mismo
porcentaje es el que después se materializa como cupón.** Un solo número en los
tres lugares: lo que se muestra, lo que se emite y lo que se cobra.

Sin sesión, el catálogo sigue mostrando el precio de lista, que es lo correcto:
el descuento es de la app y de la clienta, no del producto.

> **Hecho el 15/08/2026.** `SegmentoApp` y `Cliente.segmento_app` en
> `apps/clientes/`, `GET /api/client/descuento/` en `apps/client_api/`, ABM y
> selector en el CRM, y los precios de la grilla, la ficha y el carrito de la
> app tomando el porcentaje de ahí.
>
> Detalles que resolvió la implementación: un segmento desactivado **cae al
> general y no a cero**; el general no se puede borrar (se pone en 0); la
> migración crea uno en 0% por centro, porque cuánto descuenta es decisión del
> centro y además depende del 7.2; y si el endpoint falla la app muestra precio
> de lista, nunca un descuento inventado.
>
> `Cliente.descuento_app` es la función que resuelve el número. **La emisión del
> cupón (5.3) tiene que leer de ahí y no recalcular**, que es de lo que depende
> todo este punto.

---

## 6. Trampas conocidas

### 6.1 El precio que muestra la app y el que cobra el checkout

**Es la trampa más peligrosa de todo el documento.**

La plataforma ya tiene sistema de ofertas y la app ya pinta el badge de "-X%".
Si la app muestra $15.000 y el checkout de Tienda Nube cobra $20.900 porque allá
no hay ninguna oferta cargada, la clienta ve cambiar el precio **justo cuando va
a pagar**. Es la peor forma de perder una venta.

**Regla:** el descuento que muestra la app tiene que ser exactamente el cupón que
se aplica. Un solo origen para ese número. Concretamente: la ficha muestra el
precio con el descuento que **el backend va a materializar como cupón**, no un
`precio_oferta` cargado a mano en otro lado.

> **Nota del 15/08/2026 — una puerta que esta regla no cierra.** El catálogo
> público devuelve `precio_venta_final`, que **ya aplica el `precio_oferta` de la
> plataforma**, y el descuento por segmento (5.8) se calcula encima de ese
> número. Pero `precio_oferta` es un campo nuestro y Tienda Nube no lo conoce: si
> el centro carga una oferta en el CRM y no en TN, la app muestra un precio que
> el checkout no va a respetar, porque el cupón se aplica sobre el precio de TN.
>
> Hoy no muerde: ningún producto del centro tiene `en_oferta` prendido. La
> pregunta —para el centro— es si las ofertas de producto se cargan también en
> TN. Si la respuesta es que no, la app debería mostrar el precio de lista de TN
> y no `precio_venta_final`, que es un cambio de una línea en el serializer
> público.

> **Otra puerta, encontrada el 30/08/2026 en la primera compra real.** La app
> dijo `$10.625` y Tienda Nube cobró `$10.675`. La diferencia es el **costo de
> envío**, que la clienta elige *dentro* del WebView, después de que el backend
> preparó la compra.
>
> O sea que la pantalla de confirmación de la app afirma un total que no puede
> conocer, y que siempre va a ser **menor** que el real. Lo correcto es no
> afirmar ningún número: el detalle con el total verdadero se lo manda Tienda
> Nube por mail igual. **Resuelto el 30/08/2026:** la pantalla de confirmación
> ya no muestra ningún monto.

### 6.2 El retraso del sync sobre el precio base

El precio base sale de la plataforma, que se actualiza por el sync de Conto. Si
Tienda Nube cambia un precio, la app lo muestra viejo hasta la próxima corrida, y
en el checkout aparece el nuevo.

Mitigación: que el sync corra seguido, y que la ficha relea el precio justo antes
de abrir el checkout.

### 6.3 `storefront` no sirve para atribuir en este camino

Tienda Nube manda `storefront` con valores cerrados (`store`, `api`, `meli`,
`form`, `pos`) y `app_id`. **Una compra hecha en el checkout web llega como
`store`, exactamente igual que una compra desde el navegador.** Solo sirve si la
orden se crea por API, que no es este camino.

Por eso la atribución va por el cupón. Igual conviene guardar `origen_venta` y
`app_origen`: no cuestan nada y el día que algo cambie ya están.

### 6.4 El descuento de la app se apila con el de transferencia

**El centro ya da 10% por pagar con transferencia.** Ese descuento lo aplica el
medio de pago y Tienda Nube lo informa aparte, en `discount_gateway`.

Si la app suma su propio cupón encima, la clienta se lleva los dos: 10% de
transferencia más el de la app. Sobre un producto de $20.900 con un 15% de app,
eso es un 25% acumulado.

Puede ser exactamente lo que el centro quiere —empuja las dos cosas que le
convienen, la app y la transferencia— o puede ser margen que se va sin que nadie
lo haya decidido. **Es una pregunta para el centro, no una decisión técnica.** Los
cupones de Tienda Nube tienen regla de combinación con otras promociones, así que
se controla al crearlos.

> **El campo es `combines_with_other_discounts` y viene en `true` por defecto.**
> Verificado contra la API el 15/08/2026: un cupón creado sin mencionar el campo
> vuelve con `true`. O sea que si nadie decide nada, los descuentos se apilan —
> el default juega a favor de regalar margen.

Y hay que decidirlo antes de construir: cambia qué porcentaje se le pone al cupón.

> **Y son dos perillas, no una. Visto el 30/08/2026** al configurar el medio de
> pago en la tienda demo: el descuento por transferencia tiene **su propia
> casilla** de "permitir combinar el descuento con otras promociones", del lado
> del comercio. O sea que la decisión del §7.2 se controla desde dos lugares que
> tienen que estar de acuerdo — el nuestro (`combines_with_other_discounts` al
> crear el cupón) y el del centro— y todavía no sabemos cómo lo resuelve Tienda
> Nube cuando las dos opinan.
>
> **La buena noticia: esto se puede medir en vez de preguntarlo.** Se pone el
> descuento por transferencia en 10% en la tienda demo, se compra con cupón y se
> mira el total. Si cobra 25% menos, se apilan; si cobra 15%, no. Con eso el
> centro decide sobre un número y no sobre una hipótesis.

### 6.5 Cupones huérfanos

Cada "Comprar" que no termina en compra deja un cupón vivo en Tienda Nube. Sin
limpieza, en unos meses hay miles. De ahí el comando del 5.3.

> **Hecho y verificado contra la tienda demo el 15/08/2026**, emitiendo un cupón
> real y borrándolo con el comando. Dos cosas que se aprendieron ahí:
>
> - **El `DELETE` de Tienda Nube es un borrado lógico.** El cupón sigue
>   respondiendo por su id, pero vuelve con `is_deleted: true` y
>   `valid: false`, o sea que ya no se puede usar. Es lo que importa; no
>   esperar un 404 después de borrar.
> - **`end_date` / `end_time` se mandan en hora local y vuelven en UTC.** Se
>   envió 23:47 (Argentina) y la API devolvió `2026-08-16 02:47`. La conversión
>   la hace TN y es correcta, pero al leer un cupón hay que tenerlo en cuenta.

> **Hecho el 29/08/2026: la limpieza corre sola.** Task de Celery
> `limpiar_cupones_app` en `apps/integraciones/tasks.py`, entrada horaria en el
> `beat_schedule`, y `backend/railway.cupones.cron.json` para producción —donde
> manda el cron, porque no hay worker de Celery levantado—. Las dos vías llaman
> a la misma función, que es lo que evita que dev y producción se comporten
> distinto.
>
> Una pasada por hora alcanza: los cupones duran una hora, así que ninguno
> sobrevive más de dos. **Sin tope por corrida a propósito:** el orden es por
> fecha de vencimiento, así que un cupón que falle siempre quedaría primero para
> siempre y con un tope taparía a los que vienen atrás.
>
> El test del cron importa **todas** las tasks del `beat_schedule`, no solo esta
> —Celery no valida esos nombres al arrancar, y un typo es un job que no corre
> nunca y no avisa—. En la primera corrida encontró que `check-low-inventory`
> apunta a `apps.inventario.tasks`, que no existe: ese job nunca corrió. Queda
> registrado como excepción nombrada, con un test que falla el día que alguien
> lo arregle.

### 6.6 El doble "Comprar"

Si Tienda Nube no ofrece una URL que agregue el producto al carrito y abra el
checkout en un paso, el WebView va a caer en la ficha del producto **dentro de la
tienda web**, y la clienta va a tener que apretar "Comprar" de nuevo. Es feo y no
tiene arreglo elegante. Ver §7.

> **Resuelto el 15/08/2026, probado contra la tienda demo.**
>
> **No existe una URL que agregue al carrito.** `GET /comprar/?add_to_cart=…`
> deja el carrito vacío. Lo que funciona es un **POST** a `/comprar/` con
> `add_to_cart=<id de producto>` y `quantity=<n>`, que es lo que hace el propio
> botón "Agregar al carrito" del tema.
>
> **Pero no hay doble "Comprar".** El WebView no necesita una URL: carga una
> página nuestra con un formulario oculto que se auto-envía por POST. La clienta
> ve el carrito ya armado en un paso, y no dependemos de que Tienda Nube agregue
> nada. Es la respuesta a la pregunta 1 del §7.3, para el carrito.
>
> **El cupón es otra historia: no se puede pre-aplicar.** Probado contra la
> demo, ninguna de estas vías lo aplica — `?coupon=` sobre la URL del checkout,
> `?coupon=` / `?cupon=` / `?discount_coupon=` / `?add_coupon=` sobre el
> carrito, ni `coupon=` dentro del POST que agrega al carrito. El total sigue
> sin descuento en todos los casos.
>
> Escrito a mano en el campo "Agregar cupón de descuento" del checkout, **sí
> funciona**: $100 → $85 con un cupón del 15%, y el resumen muestra el código.
>
> Así que el §5.5 tiene una decisión que tomar, y es de producto:
>
> 1. **Inyectar JavaScript en el WebView** para llenar el campo y aplicarlo.
>    `injectedJavaScript` corre en la página cargada aunque sea de otro origen.
>    Funciona, pero depende del HTML del checkout de TN: el día que lo cambien
>    se rompe **en silencio** y la clienta paga precio de lista, que es
>    exactamente el §6.1.
> 2. **Que la clienta lo pegue.** Nuestra pantalla muestra el código con un
>    botón de copiar. Un paso más, pero no se rompe nunca y si falla se ve.
> 3. **Inyectar y verificar.** Se inyecta, y si a los pocos segundos el
>    descuento no aparece en la página, se le muestra el código para pegar. Es
>    la 1 sin su modo de fallar peor, a cambio de más trabajo.

### 6.7 El cupón se puede usar desde la web

El código se le muestra a la clienta en el checkout. Nada le impide copiarlo y
usarlo desde el navegador. Con `max_uses: 1` el daño es nulo —lo usa una vez, que
es lo que iba a hacer igual— y la atribución sigue siendo correcta: el código
salió de la app.

---

## 7. Lo que falta confirmar

Ninguna bloquea empezar, pero las tres cambian algo.

### 7.1 Verificar que `cupon` llega de verdad

El equipo de Conto agregó los campos el 11/08/2026 y avisó, con buen criterio,
que **no pudo compilar**: se les cayó el sandbox y revisaron los cambios
leyéndolos, no construyéndolos. La verificación real la hace el build de su
deploy.

Antes de escribir una línea de lógica sobre `cupon`, hay que confirmar contra una
venta real que el campo llega y con qué forma. Es barato: se mira el payload de
una venta con cupón en el sync y listo. Si falla, avisarles.

**Y hay algo que hay que hacer ya**, sin esperar nada más: guardar `cupon`,
`descuento_cupon`, `origen_venta` y `app_origen` crudos en `ContoSale`, sin
interpretarlos. Los campos ya vienen, y **solo funcionan hacia adelante** — las
ventas que pasen mientras tanto los pierden para siempre.

> **Hecho el 15/08/2026**, con una corrección al párrafo de arriba: **no se
> perdían**. `ContoSale.payload` guarda el voucher entero en todos los caminos,
> incluido el de error, así que los campos ya estaban ahí, ilegibles sin parsear
> JSON. Por eso la migración pudo rellenar las columnas hacia atrás.
>
> Las columnas valen igual, pero por otro motivo: el §14 del spec de Conto
> contempla purgar `payload` porque trae datos personales del comprador, y lo
> que no esté en columna propia se pierde ese día.
>
> **La verificación sigue pendiente:** hay que mirar una venta real con cupón.
> `verificar_conto` ahora chequea las cuatro claves, así que es un comando de
> solo lectura contra la API de Conto.

### 7.2 Preguntarle al centro si los descuentos se apilan

Ver 6.4. El centro ya da 10% por transferencia y hay que decidir si el descuento
de la app se suma o lo reemplaza. Cambia el porcentaje del cupón, así que hay que
resolverlo antes de construir.

### 7.3 Preguntas a Tienda Nube

Las dos originales, sin responder:

1. ¿Existe una URL que agregue un producto al carrito **con un cupón ya
   aplicado** y abra el checkout? Define si hay doble "Comprar" (6.6).
2. ~~Confirmar el costo por transacción del plan real del centro.~~ **Visto el
   30/08/2026 en el panel de la tienda demo: los medios de pago personalizados
   figuran con CPT 2%.** Es el extremo alto del rango que se había estimado, y
   confirma la decisión del §3.1: como usamos el checkout de Tienda Nube, ese 2%
   es un costo que el centro ya paga según el medio de pago que elija — crear las
   órdenes por API se lo habríamos sumado a cada venta. Falta confirmarlo contra
   el plan real de AME, que puede ser otro.

Y dos que aparecieron al leer la documentación (15/08/2026), para hacer al
momento del alta:

3. ¿Una app "para sus clientes" pasa por homologación? La documentación se
   contradice consigo misma (5.1).
4. ¿NubeSDK alcanza a una app que no inyecta nada en la tienda? (5.1)

---

## 8. Estimación y orden

**1,5 a 2 semanas** de trabajo efectivo, más el tiempo de calendario ajeno de la
aprobación como partner de Tienda Nube.

| | Trabajo | Días |
|---|---|---|
| 1 | App de TN: registro, OAuth, token cifrado | 2-3 |
| 2 | Mapeo `tiendanube_variant_id` (comando + campo + CRM) | 2 |
| 3 | Carrito en la app | 3 |
| 4 | Emisión de cupones + limpieza programada | 2-3 |
| 5 | WebView, retorno y confirmación | 2 |
| 6 | Atribución en el sync (depende de Conto) | 1 |
| 7 | Pruebas end-to-end con una compra real | 2 |

El orden importa: **1 y 2 son bloqueantes de todo lo demás** y el 1 depende de un
tercero, así que arranca primero aunque el resto no esté decidido.

> **Nota del 15/08/2026 — falta una fila.** `SegmentoApp` y el descuento por
> clienta (5.8) no están en la tabla, y son unos 2 días entre modelo, endpoint,
> ABM en el CRM y precios en la app. La estimación de 1,5-2 semanas se queda
> corta por eso.

---

## 9. Cómo se prueba

**No hace falta ninguna key de Apple ni de Google.** Esas son para compras
in-app de bienes digitales; acá son bienes físicos con checkout externo, así que
las tiendas no intervienen: ni comisión, ni sandbox, ni configuración.

**Tampoco hacen falta tarjetas de prueba**, porque no procesamos pagos. La
pasarela es de Tienda Nube y se prueba sola todos los días con las ventas de la
web.

Lo que sí hay que probar es lo que construimos:

| Qué | Cómo |
|---|---|
| El cupón se crea con el % correcto | Leerlo de vuelta por API o en el panel de TN |
| La URL abre el carrito con el cupón aplicado | A ojo, en el WebView |
| El retorno cierra el WebView y muestra la confirmación de AME | A ojo |
| La venta vuelve con `cupon` y matchea el `CuponApp` | Mirar el sync después de la compra |

**El truco para no gastar plata: un cupón del 100%.** Ejercita la cadena entera
—carrito, cupón, URL, WebView, orden en TN, stock descontado, Conto,
atribución— con la compra en $0.

Con una salvedad: en $0 el checkout probablemente saltee el paso de pago, así que
la detección de la URL de retorno puede comportarse distinto. Antes de lanzar,
**una compra real** con un producto barato, y después cancelarla.

> **Hecho el 30/08/2026: la compra de punta a punta salió.** Recorrido completo
> desde la app —carrito, "Comprar", cupón emitido de verdad, checkout, pago— y
> **la app detectó el retorno y mostró su propia confirmación**. La clienta
> nunca vio la página de gracias de Tienda Nube.
>
> Lo que eso confirma, y estaba anotado como sin verificar:
>
> - **`URLS_DE_EXITO` funciona.** Una de las tres direcciones que estaban
>   escritas a ojo matcheó. Falta saber cuál, para dejar solo esa y borrar las
>   otras dos, que hoy son adivinanzas que podrían matchear de más.
> - **La inyección del cupón anda sola.** No apareció el cartel para pegar el
>   código a mano.
> - Tienda Nube devuelve el cupón con `used: 1`, y la orden queda en su panel.
>
> Para que eso fuera posible hubo que **instalar un medio de pago en la tienda
> demo**. Los manuales están en *Configuración → Medios de pago →
> personalizados*: "Transferencia o depósito", "Efectivo" y "A convenir". El
> plan Esencial habilita uno solo; los tres piden subir de plan. **No hace falta
> Pago Nube**, que pide CUIT porque es una pasarela real.
>
> La tienda de demostración de socio es **gratis de por vida** y no permite
> ventas comerciales, pero **sí simular el proceso de compra**, que es
> exactamente lo que se ejercita acá.

**Precaución operativa.** No hay ambiente aparte: esto pasa en la tienda real del
centro. Las órdenes de prueba les aparecen en el panel, así que hay que avisarles
y cancelarlas para que nadie las despache. Cancelar devuelve el stock que el
`claim` descontó. Y un cupón del 100% que se filtre es un desastre: el mismo
recaudo que el resto —un uso, una hora, código impredecible—.

**Los pasos 10 y 11 no se pueden probar contra la demo.** Conto mira la cuenta
del centro, que está atada a la tienda real, así que una compra en la tienda de
demostración nunca vuelve por ahí. Para eso está `simular_venta_app`:

```bash
python manage.py simular_venta_app --cupon APP-XK4M2PQR
python manage.py simular_venta_app --cupon APP-XK4M2PQR --deshacer
```

Arma el comprobante que mandaría Conto por una venta hecha con ese cupón y lo
pasa **por el importador de siempre**, no por un camino paralelo. Muestra la
transacción creada, la venta marcada como originada en la app, el cupón marcado
como usado y la clienta identificada.

Dos recaudos, porque genera ingresos reales en el módulo financiero: se niega a
correr con `DEBUG` apagado salvo que se pase `--forzar`, y `--deshacer` borra la
venta, sus transacciones y libera el cupón. Sin eso, cada ensayo dejaría plata
que no entró contaminando justo los números del §5.7.

Lo que el simulador **no** prueba es que Conto mande el campo `cupon`. Eso lo
contesta `verificar_conto` corrido contra producción (§7.1), que es de solo
lectura y no necesita ninguna venta.


Del lado de la app, el WebView necesita **development build** (`expo run:android`),
no Expo Go.

> **Corregido el 17/08/2026: se prueba en Expo Go.** La documentación de SDK 57
> lista `react-native-webview` como incluido en Expo Go, y así se probó todo el
> checkout en un teléfono. No hace falta compilar nada.
>
> Lo que sí falta para la prueba completa es **un medio de pago en la tienda
> demo**: Tienda Nube sacó los medios manuales de su lista y ahora son apps de
> su tienda de aplicaciones. Sin eso no se llega a la página de gracias y no se
> puede verificar la detección del retorno.

> **Confirmado el 15/08/2026: la tienda de demostración existe.** Se crea desde
> el portal de partners ("Crear tienda de demostración"), así que toda la cadena
> —cupón, URL, WebView, orden, stock— se puede ejercitar sin ensuciar el panel
> del centro. La precaución del párrafo anterior se relaja bastante, pero la
> compra real con un producto barato antes de lanzar sigue valiendo: en la demo
> el checkout puede comportarse distinto.

---

## 10. Fuera de alcance

- **Checkout propio y cobro dentro de la app.** Queda como proyecto aparte, a
  reconsiderar cuando haya datos de cuánto vende la app (5.7). Hoy costaría entre
  3 y 8 semanas más y sumaría 0,7-2% a cada venta.
- **Seguimiento del envío dentro de la app.** Necesita webhooks de TN. La versión
  de esta tanda termina en "compra realizada".
- **Campañas con ventana de tiempo** (tipo Mercado Libre: "solo por 6 horas").
  Encaja bien con lo construido —serían dos campos más sobre `SegmentoApp` y la
  regla decidiría el porcentaje del cupón— pero suma el banner con contador en la
  app, la pantalla para programarla, y una regla de resolución contra los
  segmentos (¿VIP 20% durante un flash de 30% se lleva 30 o 50?). Unos 3-4 días.
  **Se pospone por oportunidad, no por costo:** un contador necesita tráfico y
  push andando para generar urgencia. Con pocas usuarias, solo regala margen a
  las que justo entraron.
- **Carrito persistido en el servidor.** Vive en el dispositivo.
- **Separar el stock del centro del stock del depósito.** No hace falta: quien
  valida el stock es Tienda Nube.

---

## 11. Documentos relacionados

| Documento | Para qué |
|---|---|
| `INTEGRACION_CONTO_SPEC.md` | El canal por el que vuelven las ventas. §5.2 tiene el mapeo de medio de pago |
| `INTEGRACION_CATALOGO_SPEC.md` | El catálogo sobre el que se apoya esto |
| `NOTIFICACIONES_PUSH_SPEC.md` | Patrón de comando + cron, a copiar para la limpieza de cupones |
| `PENDIENTES_AME.pdf` | Dónde encaja esto en el plan general |
