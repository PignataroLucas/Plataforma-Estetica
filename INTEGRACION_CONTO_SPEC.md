# Integración con Conto (stock y ventas)

**Estado:** en desarrollo — modelos y admin implementados
**Fecha:** Agosto 2026

## Contexto

El centro opera **Conto**, una plataforma propia que es la **fuente de verdad del stock y del costo de los productos**. Conto se actualiza automáticamente con cada venta de Tienda Nube: guarda el precio, descuenta el stock y registra el costo.

El stock que hoy tiene la Plataforma Estética **no es real** y no se mantiene.

**Decisión:** no se integra contra la API de Tienda Nube. Se integra contra Conto, que ya concentra esa información. Eso evita el registro como partner de TN, el OAuth, la validación HMAC, los webhooks con timeout de 3s, los rate limits y el modelo de variantes de TN.

**Problema que resuelve:** hoy cada venta de Tienda Nube se carga a mano en la Plataforma Estética.

## Contrato de la API

El contrato vive en **`CONTO_API_REQUIREMENTS.md`** (v2), que es el documento que se le pasa al equipo de Conto. Es la única fuente de verdad de la forma de los endpoints; este documento no la duplica para que no puedan divergir.

Resumen: tres endpoints de solo lectura — `GET /api/cuenta/` (identidad), `GET /api/ventas/` (vouchers como eventos) y `GET /api/stock/` (estado del catálogo). Token opaco acotado a una `Empresa` en el origen.

Conceptos del modelo de Conto que impactan en esta implementación:

- Un **voucher** puede ser venta o nota de crédito. Las notas de crédito son documentos aparte vinculados por `relacionada_con`, no cambios de estado de la venta original.
- Los **ítems** traen un discriminador `tipo`: `PRODUCTO`, `ENVIO`, `DESCUENTO`, `OTRO`. Todos los montos llegan positivos; el signo lo da el `tipo`.
- `medio_pago` es grueso (`card` / `transfer`), con `gateway_origen` crudo al lado cuando existe.
- `fecha` llega como `YYYY-MM-DD` ya resuelta en hora de Argentina.
- `canal` usa el enum de Conto en minúsculas: `tiendanube`, `presencial`, `mercadolibre`, `mercadopago`, `concesionario`.

---

## Estado actual

| Etapa | Estado |
|---|---|
| Modelos `ContoIntegration` / `ContoSale` + migración | ✅ Hecho |
| Django admin para cargar el token y configurar | ✅ Hecho |
| Validación de aislamiento a nivel modelo | ✅ Hecho y verificado |
| Diagnóstico de `Producto.sku` | ✅ Corrido en producción el 2026-08-05. Ver §8 |
| Constraint único de `sku` por sucursal | ✅ Aplicado (migración `inventario.0005`) |
| Cliente HTTP + `ContoScope` (`services.py`) | ✅ Hecho |
| Sync de stock e import de ventas (`sync.py`) | ✅ Hecho |
| Notas de crédito y cancelaciones | ✅ Hecho |
| Tasks de Celery + entradas en Beat | ✅ Hecho |
| Comando `verificar_conto` (chequeo de contrato) | ✅ Hecho |
| Endpoints de backend: config, verificar, estado, reprocesar | ✅ Hecho |
| Tests (202 en el backend, 185 de la integración) | ✅ Hecho |
| `import_from` decidido y verificado contra producción | ✅ 2026-07-01. Ver §6.2 |
| Pantalla de configuración en el frontend | ⬜ Pendiente |

Del lado de Conto: los tres endpoints están deployados y verificados contra datos reales. **Lo único pendiente es el token de producción.** La cuenta de prueba dejó de hacer falta al decidirse que la Fase 2 no se ejecuta (§16).

> ### Resuelto y verificado: el envío y el campo `total`
>
> Era un bug de la API de Conto, corregido de su lado. Reimportado en local el 2026-08-07 contra su versión corregida: **41 vouchers, $2.790.413,95 contra $2.790.413,95, diferencia $0,00 y cero descuadres.** Ver §15.

**Convención de nombres:** el código va en inglés y la UI en español, según [CODING_CONVENTIONS.md](CODING_CONVENTIONS.md). Por eso los modelos son `ContoIntegration` y `ContoSale`, con `verbose_name` y `help_text` en español.

---

## 1 — Estructura de la app

```
backend/apps/integraciones/
├── models.py       # ✅ ContoIntegration, ContoSale
├── admin.py        # ✅ Alta de la integración con token enmascarado
├── services.py     # ✅ ContoClient (HTTP) + ContoScope (acceso a base por tenant)
├── sync.py         # ✅ StockSynchronizer + SalesImporter (lógica, sin Celery)
├── tasks.py        # ✅ Wrappers de Celery: scheduling, iteración, reintentos
├── serializers.py  # ✅ Token write-only, center derivado del usuario
├── permissions.py  # ✅ Solo rol ADMIN
├── views.py        # ✅ Config, verificar, estado, sincronizar, reprocesar
├── urls.py         # ✅ Montado en /api/integraciones/
├── tests/          # ✅ 185 tests
└── management/commands/
    ├── verificar_conto.py       # ✅ Chequeo de contrato, antes de cargar nada
    ├── sincronizar_conto.py     # ✅ La corrida real. Es lo que dispara el cron
    ├── emparejar_sku_conto.py   # ✅ Empareja productos locales con el catálogo
    ├── reimportar_conto.py      # ✅ Borra lo importado para volver a traerlo
    └── diagnostico_ingresos.py  # ✅ Desglose por mes para decidir `import_from`
```

`services.py` separa dos responsabilidades a propósito: `ContoClient` habla HTTP y no sabe nada de nuestros modelos; `ContoScope` es el **único** lugar que resuelve datos de Conto contra la base, y cada consulta que hace está filtrada por sucursal o centro.

## 2 — Modelos

Ver [models.py](backend/apps/integraciones/models.py). Lo que importa del diseño:

**`ContoIntegration`** vincula un centro con una cuenta de Conto. Dos restricciones de unicidad en direcciones opuestas, y las dos hacen falta: `OneToOne` sobre `center` evita que un centro tenga dos cuentas, `unique` sobre `conto_account_id` evita que dos centros lean la misma cuenta. Una sola de las dos deja pasar la mitad de los errores de configuración.

`is_active` arranca en `False` y `can_sync` exige además que la vinculación esté verificada. Cargar el token no alcanza para que empiece a sincronizar: hay un paso explícito de verificación en el medio. Falla cerrado por defecto.

`conto_account_id`, `conto_account_name` y `link_verified_at` son read-only en el admin: los completa la verificación contra Conto, no se tipean. Si fueran editables el tripwire de §3 sería decorativo.

**`ContoSale`** es el candado de idempotencia y el registro de auditoría. `unique_together` sobre `(integration, voucher_id)` — incluye la integración porque los ids de Conto son únicos dentro de una empresa, no entre empresas. El `payload` crudo se guarda **siempre**, también en las que fallan, para poder reprocesar sin volver a consultar.

**Dónde va el token:** en `ContoIntegration.token`, en la base. Un solo camino, también en desarrollo. No va en variables de entorno: es dato de un tenant, no configuración de la app, y una variable de entorno funciona para un centro y se rompe con el segundo. Se carga desde Django admin mientras no exista la pantalla del frontend, y nunca sale en una respuesta de la API (write-only en el serializer).

## 3 — Vinculación y aislamiento entre tenants

El riesgo a evitar: que un centro quede leyendo o escribiendo datos de la cuenta de Conto de otro. Es un error que no se ve hasta que ya contaminó los libros de dos negocios distintos.

**1. La vinculación se deriva del usuario, nunca del payload.** `center` se toma de `request.user.centro_estetica`. Nunca se acepta un id de centro que venga en el request.

**2. La sucursal se valida contra el centro.** `ContoIntegration.clean()` rechaza una `branch` que no pertenezca al `center`. Está en el modelo y no solo en el serializer para que el admin también quede cubierto — que es el camino que se usa primero. Sin esto, mandar el id de la sucursal de otro centro alcanza para escribir stock en el tenant equivocado.

**3. Identidad verificada contra el origen.** Al guardar, se llama a `GET /api/cuenta/`, se guarda el `cuenta_id` devuelto y se le muestra al admin *"Vinculado a: AME Centro de Estética (cnt_8f21)"* para que lo confirme un humano.

**4. Unicidad en las dos direcciones.** Ver §2.

**5. Tripwire en cada sincronización.** Cada respuesta trae `cuenta_id`. Si no coincide con el guardado, la sincronización se aborta y alerta.

```python
if payload['cuenta_id'] != integration.conto_account_id:
    raise ContoAccountMismatch(...)   # falla cerrado, no importa nada
```

**6. En Celery no hay `request.user`.** Toda la multi-tenancy del proyecto se apoya en filtrar por `request.user.sucursal` en la capa de vistas. Las tasks corren sin usuario, así que ese colchón no existe: cada filtro sale explícitamente de `integration.branch` o `integration.center`.

Los dos cruces contra la base se encapsulan en **un único método del servicio** que recibe la integración y aplica el filtro adentro. No debe existir un segundo camino que pueda olvidárselo:

- **Producto por SKU** → filtrar por `sucursal=integration.branch`. Los SKU vienen de proveedores y marcas: que dos centros tengan `SER-VITC-30` es lo esperable.
- **Cliente por email o teléfono** → filtrar por `centro_estetica=integration.center`. Una misma persona puede ser clienta de dos centros con el mismo mail.

La task que itera integraciones no comparte cliente HTTP ni querysets entre iteraciones.

**7. Tests.** ✅ En [tests/test_services.py](backend/apps/integraciones/tests/test_services.py):

- Dos centros con el mismo SKU y con el mismo email de cliente, verificando que cada uno resuelve solo su lado.
- El tripwire de cuenta, incluido el caso de una segunda página que pertenece a otra cuenta.
- Una integración sin cuenta verificada se niega a sincronizar.
- `update_stock` no puede escribir sobre un producto de otra sucursal ni recibiendo el objeto equivocado.
- Que crear un producto desde Conto no genere el gasto fantasma.

Falta el test de que el serializer rechace una `branch` de otro centro; la validación del modelo ya está verificada a mano.

## 4 — Sincronización de stock

Celery Beat, cada 30 minutos.

Para cada SKU devuelto, buscar el `Producto` **de la sucursal configurada** y actualizar `stock_actual`, `precio_costo` y `precio_venta`.

**Actualización directa por queryset, sin crear `MovimientoInventario`.** El movimiento real ocurrió en Conto. Si se crearan movimientos acá, el signal de [inventario/signals.py:39](backend/apps/inventario/signals.py:39) generaría transacciones financieras fantasma en cada sincronización.

```python
Producto.objects.filter(pk=producto.pk).update(stock_actual=..., precio_costo=...)
```

### 4.1 — Creación de productos faltantes

Con `create_missing_products` activo (default), un SKU de Conto que no existe en la sucursal se crea. Conto informa `nombre`, `stock`, `costo`, `precio` y `activo`, que es todo lo necesario para que el producto nazca completo — a diferencia de Tienda Nube, que no informa costo. Eso evita tener que terminar de cargar el catálogo a mano.

**Trampa a evitar:** crear un `Producto` con `stock_actual > 0` y `precio_costo > 0` dispara [create_initial_stock_movement](backend/apps/inventario/signals.py:11), que crea un `MovimientoInventario` de ENTRADA, que a su vez genera una **transacción de gasto** por la compra del stock inicial. Sería un gasto fantasma: el centro no compró ese stock ahora, ya lo tenía.

La secuencia correcta:

```python
producto = Producto.objects.create(..., stock_actual=0, precio_costo=costo)
Producto.objects.filter(pk=producto.pk).update(stock_actual=stock)  # no dispara signals
```

Los productos creados así quedan con `categoria` y `proveedor` en null y sin foto. Se reportan para que el admin los complete; es información cosmética que no bloquea nada.

## 5 — Import de ventas

Celery Beat, cada 15 minutos. Ventana con overlap de 5 minutos sobre `last_sales_sync` para cubrir desfasajes de reloj; la unicidad de `voucher_id` deduplica.

Se procesan los vouchers con `canal` en `channels_to_import`. El resto se guarda con estado `SKIPPED` junto al payload, para no volver a pedirlos y para poder reprocesarlos si más adelante se agrega un canal.

### 5.1 — Ventas

Solo si el estado en Conto es pagado.

1. `get_or_create` de `ContoSale`. Si ya está `PROCESSED`, se saltea.
2. Una `Transaction` por ítem de tipo `PRODUCTO`: `type=INCOME_PRODUCT`, `category` = categoría de sistema `"Productos"` (la misma que usa Mi Caja en [mi_caja/views.py:274](backend/apps/mi_caja/views.py:274), **no** `"Venta de Productos"`), `auto_generated=True`, `product` si el SKU resuelve dentro de la sucursal, `date` = `fecha` tal cual llega.
3. Ítems de tipo `ENVIO` u `OTRO` → una `Transaction` `INCOME_OTHER`.
4. Ítems de tipo `DESCUENTO` → **no generan transacción propia**. Se prorratean sobre las líneas de producto, para que el ingreso por producto refleje lo efectivamente cobrado. `Transaction.amount` es siempre positivo por diseño, así que no existe la opción de registrarlos como línea negativa. Si el voucher trae descuento y no tiene líneas de producto sobre las que prorratear, se resta del ítem de envío; si tampoco hay, el voucher queda en `ERROR` para revisión manual. Nunca se ignora en silencio.
5. Si viene `cliente`, matchear **dentro del centro** por email normalizado y después por teléfono. Si no existe y `create_missing_clients` está activo, crearlo marcado por origen.

**No se crea `MovimientoInventario`.** El stock ya llega por §4; crear movimientos acá lo descontaría dos veces y además duplicaría la transacción vía signal.

`registered_by` queda en `null`: no es la caja de ningún empleado. Por eso estas ventas no aparecen en Mi Caja ni afectan cierres de caja individuales, que es el comportamiento correcto.

Un ítem de tipo `PRODUCTO` sin SKU, o con un SKU que no resuelve, **igual registra el ingreso** — sale de `precio_unitario × cantidad`. Solo se pierde la atribución al producto, y se reporta.

### 5.2 — Mapeo de medio de pago

Conto confirmó que `medio_pago` tiene **seis valores**, no dos como se había informado al principio: `transfer`, `card`, `cash`, `check`, `mercadopago`, `mercadolibre`.

`gateway_origen` gana cuando se lo reconoce: es el gateway crudo que informa Tienda Nube, así que distingue Pago Nube de Mercado Pago, algo que `medio_pago` no puede cuando dice `card`.

| Señal | `Transaction.payment_method` |
|---|---|
| `gateway_origen` contiene `mercadopago` | `MERCADOPAGO` |
| `medio_pago = cash` | `CASH` |
| `medio_pago = transfer` | `BANK_TRANSFER` |
| `medio_pago = mercadopago` | `MERCADOPAGO` |
| `medio_pago = mercadolibre` | `MERCADOPAGO` (se liquida por Mercado Pago) |
| `medio_pago = check` | `OTHER` (no existe cheque de nuestro lado) |
| `medio_pago = card` con gateway desconocido o nulo | `default_payment_method` |
| ausente | `default_payment_method` |

Para el canal `tiendanube` —el único que se importa por defecto— los valores reales son solo `mercadopago` o `transfer`, así que en la práctica el mapeo es exacto.

**No se parsea el campo de notas** de Conto. En las ventas de concesionario el medio de pago real solo existe ahí como texto libre, y Conto decidió no exponerlo justamente para evitar ese parseo. Ese canal no se importa.

### 5.3 — Notas de crédito

Genera una `Transaction` de tipo `EXPENSE` por el total, en una categoría `"Devoluciones"` (se crea si no existe, siguiendo el patrón de las demás), vinculada a la misma `ContoSale` y con referencia a la venta original en `notes`.

**Por qué compensar y no revertir:** una nota de crédito puede ser parcial. Revertir la venta original solo funciona si es total, y haría falta un camino distinto para cada caso — dos comportamientos para el mismo evento, que es cómo aparecen los bugs raros seis meses después. La transacción compensatoria maneja parcial y total igual, no destruye nada y deja el rastro de que hubo una devolución.

**Contrapartida asumida:** el ingreso bruto por productos queda inflado respecto del neto. El balance es correcto; el desglose por categoría muestra la devolución del lado del gasto en vez de descontarla del ingreso. Para el volumen de devoluciones de este negocio es aceptable.

Si la nota de crédito llega antes que la venta que referencia, queda en `PENDING` y se reintenta en la corrida siguiente.

## 6 — Cancelaciones

Si un voucher ya procesado vuelve cancelado, se revierten sus `Transaction` y la `ContoSale` pasa a `SKIPPED`, conservando el payload. Acá sí se revierte en vez de compensar: una cancelación es total por definición.

## 6.1 — Cómo se dispara la sincronización

**Celery no está deployado en producción** y nunca se configuró. Por eso la lógica vive en clases planas en `sync.py` y hay dos formas de invocarla, que hacen exactamente lo mismo:

**Comando** — no necesita broker ni worker. Es la vía prevista para producción:

```bash
python manage.py sincronizar_conto --que ventas   # o stock, o todo
```

Termina con código de salida distinto de cero si algo falló, para que un scheduler lo reporte en vez de informar una corrida exitosa que no importó nada.

**Tasks de Celery** ([tasks.py](backend/apps/integraciones/tasks.py)) — quedan definidas y registradas en el beat schedule para el día que Celery se deploye. Hoy no corren.

| Trabajo | Frecuencia prevista | Qué hace |
|---|---|---|
| Ventas | cada 15 min | Trae vouchers desde `last_sales_sync − 5 min` |
| Stock | cada 30 min | Trae el estado del catálogo |
| Verificar vínculo | diaria | Reconfirma que cada integración siga resolviendo a su cuenta |

**La verificación de vínculo está incluida en cada corrida del comando**, no en un job aparte. Antes de sincronizar, pregunta a `/api/cuenta/` y compara. Si el token resuelve a otra cuenta, **desactiva la integración y corta sin importar nada**.

Es una request extra por corrida y cierra un hueco: el tripwire del cliente valida `cuenta_id` en cada página de listado, pero solo cuando hay datos para devolver. Una integración sin ventas recientes podría quedar apuntando a otra cuenta indefinidamente. Con la verificación adentro del comando, un solo cron cubre todo y no hace falta un segundo schedule.

Un problema de vínculo en un centro **no silencia a los demás**: se reporta, se lo saltea y se sigue con el resto.

Ambas vías distinguen dos clases de error. Token revocado, cuenta cruzada o cuenta inactiva **no se reintentan**: reintentar solo demora la alerta. `ContoUnavailable` sí es transitorio, y la corrida siguiente recupera lo que falte gracias a la ventana con solapamiento.

**Pendiente de decisión:** con qué scheduler se corre el comando en Railway. Ver §12.

## 6.2 — Desde cuándo importar

`import_from` es obligatorio para la primera corrida de ventas. Sin él, la primera sincronización intentaría traer todo el histórico de la cuenta. Para ampliar el histórico después, se mueve la fecha hacia atrás y se limpia `last_sales_sync`; la unicidad de `voucher_id` hace que lo ya importado no se duplique.

**Decidido: se importa desde julio de 2026.** Se carga `import_from = 2026-07-01 00:00` (hora Argentina) al configurar la integración.

**Verificado contra producción el 2026-08-07.** El desglose de `INCOME_PRODUCT` por mes en la sucursal Banfield muestra que **julio y agosto están en cero**: la última venta de producto cargada es de junio. Importar desde el 1 de julio llena un hueco y no puede duplicar nada.

| Mes | Ventas cargadas | Monto |
|---|---|---|
| 2026-06 | 3 | $74.995,00 |
| 2026-05 | 31 | $495.537,25 |
| 2026-04 | 19 | $345.780,00 |
| 2026-07 en adelante | **0** | **$0,00** |

La medición se hace con [diagnostico_ingresos](backend/apps/integraciones/management/commands/diagnostico_ingresos.py), que separa las ventas por origen — cargadas a mano, de mostrador (movieron stock) o importadas — porque solo las primeras pueden chocar con un import.

**Decidido también: no se amplía hacia atrás.** Abril, mayo y junio quedan como están, aunque lo cargado a mano en esos meses sea una fracción de los ~$2,8M mensuales que factura Tienda Nube. Traerlos exigiría clasificar 53 transacciones una por una para saber cuáles se duplicarían, y el valor de completar meses ya cerrados no lo justifica.

Vale saber que **el histórico completo es importable**: Conto confirmó que el canal es confiable para todos los registros, así que no hay fecha de corte técnica. Si en algún momento se quiere traer todo, se mueve `import_from` hacia atrás y se limpia `last_sales_sync`.

## 7 — Falla visible

Si el token se revoca o rota en Conto, la sincronización empieza a recibir 401. Eso tiene que aparecer como alerta en la pantalla de estado, no simplemente dejar de traer datos. Una integración que muere en silencio se descubre en el cierre de mes con semanas de ventas faltando — es el modo de falla más caro y el más fácil de prevenir.

Lo mismo para el tripwire de `cuenta_id` de §3 y para vouchers en estado `ERROR`.

## 8 — Trabajo previo pendiente

- ✅ **Diagnóstico de `Producto.sku` en producción.** Corrido el 2026-08-05: **13 productos en la única sucursal (Banfield), ninguno con SKU, sin colisiones y sin códigos de barras.** El comando [diagnostico_sku](backend/apps/inventario/management/commands/diagnostico_sku.py) se corre así:

  ```bash
  docker-compose exec -e DATABASE_URL='<DATABASE_PUBLIC_URL de Railway>' backend python manage.py diagnostico_sku
  ```

- ✅ **Constraint `unique_sku_per_sucursal`.** Aplicado. Es un índice único **parcial** sobre `(Upper(sku), sucursal)` que excluye los SKU vacíos. Tres decisiones:
  - **Por sucursal, nunca global**: los SKU vienen de proveedores y marcas, así que dos centros que vendan la misma línea van a compartir códigos.
  - **Excluye los vacíos**: los 13 productos sin código pueden convivir, así que el constraint no quedó atado a hacer el backfill primero.
  - **Compara en mayúsculas**: coincide con la búsqueda case-insensitive que usa la integración. Si no, `abc` y `ABC` podrían coexistir y después leerse como ambiguos.

  Efecto colateral bueno: la ambigüedad de SKU ahora es imposible a nivel base, no algo que haya que manejar al leer.

- ⬜ **Backfill de los 13 SKU.** No bloquea nada: un producto sin SKU simplemente no matchea con Conto, y como `create_missing_products` está activo, Conto crea su propia versión al lado. La consecuencia es catálogo duplicado, no pérdida de datos ni de plata.

  Ninguno de los 13 tiene código de barras tampoco, así que no hay match automático posible por ese lado. Lo eficiente es hacerlo contra el catálogo real de Conto cuando el endpoint de stock exista: traer su lista, emparejar por similitud de nombre y confirmar 13 veces. Son minutos.
- ~~**Bloquear la edición manual de stock**~~. **Decidido: no se bloquea.** El riesgo es bajo porque el stock se sincroniza desde Conto cada 30 minutos, así que una edición manual se sobrescribe sola en la próxima corrida. No corrompe nada, solo es inútil. Lo que sí conviene en algún momento es que la UI aclare que ese número viene de Conto, para que nadie pierda tiempo editándolo.
- **Revisar `check_low_inventory`** ([config/celery.py](backend/config/celery.py), diario 8:00). Hoy compara contra stock irreal.
- **Unificar categorías de ingreso.** Conviven `"Productos"` ([finanzas/signals.py:25](backend/apps/finanzas/signals.py:25)) y `"Venta de Productos"` ([inventario/signals.py:138](backend/apps/inventario/signals.py:138)), lo que fragmenta los reportes.

## 9 — Secuencia de puesta en marcha

El orden importa:

1. **Verificar el contrato** contra la instancia de Conto, antes de cargar nada:

   ```bash
   docker-compose exec backend python manage.py verificar_conto --base-url https://conto.example
   ```

   Chequea los tres endpoints y reporta cada requisito. Pide el token por consola para que no quede en el historial. Mientras haya `FALLA`, no tiene sentido seguir.

2. Cargar la integración en Django admin con la `base_url`, el token e `import_from`.
3. Verificar la vinculación y confirmar el nombre de cuenta que devuelve Conto.
4. Activar con `channels_to_import = ['tiendanube']`.
5. Primera corrida de stock, revisar los SKU que no matchean.
6. Primera corrida de ventas sobre una ventana corta antes de ampliar `import_from`.

**La corrección de canales históricos ya no hace falta.** Estaba como paso previo obligatorio, pero Conto confirmó que el importador de Tienda Nube siempre asignó el canal bien, y que la API además lo deriva del prefijo del número de comprobante (`TN-`, `ML-`, `CC-`), recurriendo al campo solo cuando no hay prefijo. El canal es confiable para todo el histórico.

**Datos de conexión confirmados:**

| Qué | Valor |
|---|---|
| `base_url` | `https://conto-production.up.railway.app` |
| Red privada | No aplica: Conto corre en un proyecto de Railway distinto, y el networking privado solo funciona dentro de un mismo proyecto |
| Rate limit | 60 requests por minuto, por token |

El rate limit no es un problema: una corrida completa son 3 requests más una por página de resultados.

Del lado de Conto el token se guarda hasheado con SHA-256, cualquier método que no sea GET se rechaza con 403, el alcance por empresa se resuelve en el origen y es revocable individualmente con registro de último uso.

## 10 — Estimación restante

| Etapa | Días | Bloqueado por Conto |
|---|---|---|
| Emparejar los 13 SKU contra el catálogo de Conto | 0,5 | Sí (endpoint de stock) |
| Pantalla de configuración y estado, con las alertas de §7 | 1 | Sí |
| Validación end-to-end contra la cuenta de prueba | 0,5 | Sí |

**Restante: ~2 días, todo bloqueado.** El backend está completo: se puede configurar, verificar, sincronizar y monitorear la integración por API y desde Django admin, sin frontend.

## 11 — API disponible

Todos los endpoints requieren rol `ADMIN` y están acotados al centro del usuario.

| Endpoint | Qué hace |
|---|---|
| `GET/POST/PATCH /api/integraciones/conto/` | Configuración. `center` sale del usuario, `token` es write-only |
| `POST /api/integraciones/conto/{id}/verificar/` | Pregunta a Conto de qué cuenta es el token y lo guarda |
| `GET /api/integraciones/conto/{id}/estado/` | Contadores, últimos errores y alertas |
| `POST /api/integraciones/conto/{id}/sincronizar/` | Corre un sync ahora (`ventas`, `stock` o `todo`) |
| `GET /api/integraciones/conto-ventas/` | Vouchers importados. Filtrable por `status`, `type`, `channel` |
| `POST /api/integraciones/conto-ventas/{id}/reprocesar/` | Reprocesa desde el payload guardado, sin consultar Conto |

Códigos de alerta que devuelve `estado`: `SIN_VINCULAR`, `INACTIVA`, `SIN_FECHA_DE_INICIO`, `VOUCHERS_CON_ERROR`, `NUNCA_SINCRONIZADA`, `SINCRONIZACION_DETENIDA`.

`SINCRONIZACION_DETENIDA` es el que implementa §7: salta si pasaron más de 2 horas sin importar ventas, cuando debería pasar cada 15 minutos.

`sincronizar` **corre inline**, no encola. Sin worker de Celery no hay a dónde encolar, y agregar uno solo para esto implicaría un worker, un beat y un broker para lo que son un par de llamadas HTTP. De paso la respuesta trae el resultado real en vez de obligar a la UI a consultar el estado. Si algún día el import inicial creciera hasta chocar con el timeout de la request, para esa carga se usa el comando.

---

## 12 — Scheduler en producción

Celery nunca se configuró en Railway, así que **sin scheduler nada dispararía la sincronización**. La integración quedaría configurada, verificada y sin traer una sola venta — un síntoma difícil de diagnosticar, porque todo diría OK.

Infraestructura actual en Railway: tres servicios — Postgres, Redis y el backend. Redis está en uso como cache de los dashboards de analytics (`@cache_page` en [analytics/views.py](backend/apps/analytics/views.py), invalidado desde [servicios/views.py:17](backend/apps/servicios/views.py:17)); no se usa como broker porque no hay worker.

**Elegido: cron de Railway.** Un servicio adicional del mismo repo que corre el comando cada 15 minutos, trabaja unos segundos y termina. Un worker de Celery más un beat serían dos contenedores prendidos todo el día para un par de llamadas HTTP.

Configuración del servicio de cron:

| Qué | Valor |
|---|---|
| Repo | el mismo, `Plataforma-Estetica` |
| Config file | `railway.cron.json` |
| Cron schedule | `*/15 * * * *` |
| Variables | `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `DEBUG=0`, `ALLOWED_HOSTS` |

**Detalle crítico: el start command no se sobrescribe desde el dashboard.** [railway.json](railway.json) define `startCommand: /bin/sh /app/entrypoint.sh` para todos los servicios del repo, y la configuración por código le gana a la del dashboard. Un start command puesto en la UI queda pisado, arranca [entrypoint.sh](backend/entrypoint.sh), levanta Gunicorn y el servicio nunca termina — el cron no vuelve a dispararse.

Por eso el cron usa su propio archivo, [railway.cron.json](railway.cron.json), con el comando y `restartPolicyType: NEVER`. Lo segundo importa: el comando sale con código distinto de cero cuando una sincronización falla, y la política `ON_FAILURE` del servicio web lo reintentaría tres veces. No hace falta — la corrida siguiente recupera lo que falte por la ventana con solapamiento.

De paso, saltear `entrypoint.sh` evita que cada corrida ejecute `migrate` y `collectstatic`, que ahí no tienen nada que hacer.

**Se puede validar sin la integración cargada:** sin integraciones activas el comando informa "Nada que hacer" y termina con código 0. Eso permite armar el servicio y confirmar que buildea, corre y cierra antes de que exista un solo dato en juego.

Con `--que todo` el stock se sincroniza cada 15 minutos en vez de cada 30. Es inofensivo: es una lectura de estado, idempotente. Un solo cron en lugar de dos.

Migrar a Celery más adelante es configuración, no código: las tasks ya están escritas y registradas en el beat schedule. Tiene sentido el día que haya un segundo motivo, por ejemplo cuando vuelvan los recordatorios de WhatsApp.

---

## 13 — Compras y gastos (fase 2)

Conto es el sistema de registro del inventario en las dos direcciones: las compras lo hacen subir, las ventas lo hacen bajar. **La Plataforma Estética importa ambas como transacciones financieras** — ventas como ingreso, compras como gasto — y su módulo de inventario queda como espejo.

Eso responde la pregunta que quedó abierta al principio: el inventario de la plataforma **no reemplaza a Conto, lo refleja**.

**Estado actual:** las compras no se están cargando en la plataforma, así que esos gastos hoy no se registran de nuestro lado. No es una regresión, es algo que todavía no existe.

**Por qué el sync de stock no genera el gasto.** `update_stock` usa `.update()` de queryset, que no dispara signals. Si los disparara, cada sincronización generaría un gasto fantasma por producto, cada 15 minutos.

**Por qué no se infiere del delta de stock.** Dos motivos que lo descartan:

- La primera sincronización llevaría el stock local de 0 a los valores reales de Conto. Interpretado como compra, sería un gasto falso enorme.
- Un aumento de stock no siempre es una compra: puede ser un ajuste por conteo, una devolución, una corrección o un traslado. Adivinar ensucia los gastos con datos inventados.

**La solución:** un endpoint `GET /api/compras/` en Conto, con la misma forma que ventas. De nuestro lado es casi el mismo código que `SalesImporter`, creando `EXPENSE` en la categoría "Insumos y Productos" en vez de `INCOME_PRODUCT`. Especificado en el §12 de `CONTO_API_REQUIREMENTS.md`.

**Riesgo a manejar cuando eso exista:** hoy la plataforma genera el gasto sola al crear un producto con stock y costo ([signals.py:11](backend/apps/inventario/signals.py:11)) y al usar `ajustar_stock` con tipo ENTRADA ([views.py:97](backend/apps/inventario/views.py:97)). Con las compras llegando de Conto, esas dos vías tienen que desactivarse para los productos que Conto maneja, o la misma compra se cuenta dos veces.

Vale notar que `create_initial_stock_movement` es discutible incluso hoy: crear la ficha de un producto con un stock inicial no es lo mismo que haber comprado ese stock en ese momento.

---

## 15 — Resuelto: qué representa el campo `total`

**Estado: era un bug de la API de Conto. Corregido de su lado el 2026-08-06.**

**Qué era.** Conto exponía `precio_unitario` con el **precio de lista** en vez del precio efectivo. Un envío bonificado al 100% llegaba con `precio_unitario: 6231` cuando su aporte real al total era 0. No pasaba solo con el envío: cualquier ítem con descuento tenía el mismo desfase, porque el precio de lista es mayor a lo cobrado.

**Qué representa `total`.** Lo que efectivamente pagó el cliente, tomado directo de `order.total` de Tienda Nube, sin recalcular. Es autoritativo.

**Los 40 casos eran envío gratis**, no un error de cálculo. La línea de ENVIO existe con su precio para que quede constancia de cuánto valía, pero bonificada. El costo que absorbió el centro se registra aparte en Conto, como egreso, junto con la comisión del gateway.

**El fix de Conto:** `precio_unitario` ahora es el precio efectivo, más un campo nuevo `precio_lista` informativo, que permite distinguir un envío gratis de uno inexistente. Nuestro código no necesitó cambios en el cálculo: la fórmula ya era "líneas sumadas con el signo de su tipo".

**Lo que sí se agregó de nuestro lado.** Ahora que `total` es autoritativo y las líneas tienen que sumarlo exacto, dejó de ser una duda y pasó a ser un invariante verificable. `ContoSale.total_discrepancy` guarda la diferencia cuando no cuadra:

- Si cuadra, queda en `null`.
- Si no cuadra, **la venta se importa igual** —la plata entró, descartarla sería peor— pero queda marcada, aparece en rojo en el admin y dispara la alerta `VOUCHERS_CON_DESCUADRE` en el endpoint de estado.

La diferencia ya no es una decisión de criterio: significa que nuestro desglose está mal, o que Conto manda algo inesperado. Cualquiera de las dos merece que alguien mire.

**Verificado el 2026-08-07**, reimportando contra la versión corregida de Conto:

| Control | Resultado |
|---|---|
| Vouchers procesados | 41 (julio y agosto) |
| Total según Conto | $2.790.413,95 |
| Total en la plataforma | $2.790.413,95 |
| Diferencia | **$0,00** |
| Vouchers con descuadre | **0** |
| Transacciones anteriores a `import_from` | 0 |
| Envíos bonificados sin generar ingreso | 12 |
| Líneas de producto atribuidas | 76 de 76 |

De paso quedó claro que los $7,5M medidos antes incluían abril y mayo: **el volumen real de Tienda Nube es ~$2,8M por mes.**

**Sin usar todavía:** `precio_lista`. Podría servir para dejar constancia en las notas de la transacción de que un envío se entregó gratis y cuánto valía.

Detectado el 2026-08-06 en la prueba local contra la cuenta real (115 vouchers de Tienda Nube importados desde el 1 de julio).

**El hallazgo.** La cuenta del import es exacta contra las líneas: productos menos descuentos prorrateados da al centavo lo que quedó en `INCOME_PRODUCT`. Pero contra el campo `total` de Conto hay 240.175 de diferencia, y **en los 40 vouchers que difieren la diferencia es exactamente igual a la línea de ENVIO**.

Ejemplo — voucher `f259e41f`, orden TN 2037087304:

```
PRODUCTO   18.900   CONTORNO DE OJOS
PRODUCTO   97.020   RUTINA FULL PIEL NORMAL A SECA
ENVIO       6.231   Envío - Pedido TN #1054
DESCUENTO  11.592   Descuento Transferencia / Depósito

total de Conto:  104.328  =  115.920 − 11.592   (sin el envío)
nuestro neto:    110.559  =  115.920 − 11.592 + 6.231
```

De los 477.331 de envío del período, 240.175 quedan afuera del `total` y 237.156 adentro. O sea que Conto no es consistente en esto, o hay algo que distingue esos 40 casos.

**Las dos lecturas posibles:**

1. **`total` es lo que pagó el cliente.** Entonces en esos 40 el envío fue gratis, lo absorbió el centro, y la línea de ENVIO es un **costo** y no un ingreso. Registrarla como `INCOME_OTHER` inventa 240.175 de facturación.
2. **`total` se calcula mal y las líneas son la verdad.** Nuestra cuenta está bien y no hay nada que cambiar.

**La pregunta a Conto:** ¿qué representa `total` exactamente, es lo que pagó el cliente? Y donde no incluye el envío, ¿es porque fue gratis o es un problema del cálculo?

**Lo propuesto, pendiente de esa respuesta:** que el import detecte cuando las líneas no suman el `total` declarado y marque el voucher para revisión, en vez de importarlo en silencio. Eso vale independientemente de cuál lectura gane. Qué número manda es una decisión de plata, no técnica.

## 16 — Decidido: la Fase 2 no se ejecuta

**No se valida el camino de notas de crédito ni cancelaciones contra datos reales.** Decidido el 2026-08-07.

**Por qué.** En 332 vouchers de todo el histórico alcanzable de AME no hay ni una nota de crédito, ni una venta de Tienda Nube cancelada. Y quien opera Conto confirmó que **nunca emitió una nota de crédito**: la función existe por si acaso.

Validar esos caminos exigía anular **irreversiblemente** una venta real —dejando además un comprobante de gasto huérfano, porque en Conto el envío y la comisión son un voucher aparte que no se cancela solo— o ensuciar los números de Tienda Nube con un pedido de prueba, o que Conto modificara su código productivo para permitir forzar el canal. Todo eso para ejercitar un camino que no ocurre.

**Qué cubre el riesgo.** La lógica está testeada: nota de crédito total, parcial, la que llega antes que su venta, y la cancelación que revierte transacciones ya importadas. Lo que quedó sin verificar es que el payload real tenga la forma asumida — riesgo de contrato, no de código.

Y ese riesgo falla de forma segura: un voucher con forma inesperada queda en estado `ERROR` con el payload crudo guardado, dispara `VOUCHERS_CON_ERROR`, y se reprocesa después de ajustar. **La venta original no se modifica.** El peor caso es que una devolución tarde en reflejarse hasta que alguien mire la alerta.

**Nota para la fase de compras (§13):** al cancelar una factura de Tienda Nube en Conto, el comprobante de gasto asociado (envío + comisión) **queda activo**. Solo se cancela solo en ventas de concesionario. Cuando se importen compras, una venta cancelada va a dejar su gasto importado.

**Dato aparte:** Conto no permitía vincular una nota de crédito con su factura —no existía el campo ni el backend lo aceptaba— y lo corrigieron al preparar esta prueba. Así que si alguna vez emiten una, va a llegar con `relacionada_con` y nuestro código la va a procesar.

## 14 — Pendiente: datos personales en el payload guardado

Conto activó `payload_origen`, que guarda el JSON crudo de cada pedido de Tienda Nube. Ese JSON **contiene datos personales del comprador**, y Conto implementó su purga automática vía el webhook `customers/redact` de Tienda Nube.

**Corregido el 2026-08-07: `payload_origen` no llega.** Inspeccionados los 228 vouchers importados en local, el payload que devuelve `GET /api/ventas/` tiene exactamente estas claves:

```
actualizado_en, canal, cliente, estado, fecha, gateway_origen,
id, items, medio_pago, orden_externa_id, relacionada_con, tipo, total
```

Descartar `payload_origen` antes de guardar —que era la opción preferida— sería un no-op contra un campo que no existe de nuestro lado.

**El problema real es otro campo: `cliente`.** 157 de esos 228 vouchers traen un bloque con `nombre`, `email` y `telefono` del comprador. Se diferencia de `payload_origen` en dos cosas que cambian qué se puede hacer con él:

- **Lo usa el reproceso.** Es de donde sale el match de clienta por email y teléfono (§5.1). Borrarlo deja los vouchers viejos sin poder reprocesarse con atribución.
- **En producción esos datos van a estar igual en `Cliente`**, porque `create_missing_clients` va prendido. Esa copia sí es alcanzable por un pedido de borrado; la de `ContoSale.payload` es la que quedaría huérfana.

Las opciones viables quedan en dos:

1. **Retención**: vaciar el payload de vouchers `PROCESSED` con más de X meses. Conserva el reproceso durante la ventana en que sirve, que es corta.
2. **Limpiar el bloque `cliente`** al pasar a `PROCESSED`, dejando el resto del payload. Conserva la capacidad de reprocesar montos y productos, pierde la atribución de clienta.

No bloquea la puesta en marcha.
