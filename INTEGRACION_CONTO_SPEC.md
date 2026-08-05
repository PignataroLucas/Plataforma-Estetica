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
| Diagnóstico de `Producto.sku` | ✅ Comando hecho, falta correrlo en producción |
| Constraint único de `sku` por sucursal | ⬜ Pendiente del diagnóstico en producción |
| Cliente HTTP + `ContoScope` (`services.py`) | ✅ Hecho |
| Sync de stock e import de ventas (`sync.py`) | ✅ Hecho |
| Notas de crédito y cancelaciones | ✅ Hecho |
| Tasks de Celery + entradas en Beat | ✅ Hecho |
| Comando `verificar_conto` (chequeo de contrato) | ✅ Hecho |
| Endpoints de backend: config, verificar, estado, reprocesar | ✅ Hecho |
| Tests (108) | ✅ Hecho |
| Pantalla de configuración en el frontend | ⬜ Pendiente |

Del lado de Conto: el sistema de `ApiToken` y la corrección de canales históricos ya están. Los tres endpoints, no.

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
├── tests/          # ✅ 108 tests
└── management/commands/verificar_conto.py   # ✅ Chequeo de contrato
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

| `medio_pago` | `gateway_origen` | `Transaction.payment_method` |
|---|---|---|
| `transfer` | cualquiera | `BANK_TRANSFER` |
| `card` | contiene `mercadopago` | `MERCADOPAGO` |
| `card` | otro valor conocido | según tabla configurable |
| `card` | `null` o desconocido | `default_payment_method` |
| ausente | — | `default_payment_method` |

La tabla de gateways vive en configuración, no en código, para poder agregar valores sin deploy. **No se parsea el campo de notas** de Conto: es texto libre y se rompe en silencio.

### 5.3 — Notas de crédito

Genera una `Transaction` de tipo `EXPENSE` por el total, en una categoría `"Devoluciones"` (se crea si no existe, siguiendo el patrón de las demás), vinculada a la misma `ContoSale` y con referencia a la venta original en `notes`.

**Por qué compensar y no revertir:** una nota de crédito puede ser parcial. Revertir la venta original solo funciona si es total, y haría falta un camino distinto para cada caso — dos comportamientos para el mismo evento, que es cómo aparecen los bugs raros seis meses después. La transacción compensatoria maneja parcial y total igual, no destruye nada y deja el rastro de que hubo una devolución.

**Contrapartida asumida:** el ingreso bruto por productos queda inflado respecto del neto. El balance es correcto; el desglose por categoría muestra la devolución del lado del gasto en vez de descontarla del ingreso. Para el volumen de devoluciones de este negocio es aceptable.

Si la nota de crédito llega antes que la venta que referencia, queda en `PENDING` y se reintenta en la corrida siguiente.

## 6 — Cancelaciones

Si un voucher ya procesado vuelve cancelado, se revierten sus `Transaction` y la `ContoSale` pasa a `SKIPPED`, conservando el payload. Acá sí se revierte en vez de compensar: una cancelación es total por definición.

## 6.1 — Tareas programadas

En [config/celery.py](backend/config/celery.py):

| Task | Frecuencia | Qué hace |
|---|---|---|
| `import_conto_sales` | cada 15 min | Trae vouchers desde `last_sales_sync − 5 min` |
| `sync_conto_stock` | cada 30 min | Trae el estado del catálogo |
| `verify_conto_links` | diaria 7:30 | Reconfirma que cada integración siga resolviendo a su cuenta |

`verify_conto_links` existe porque el tripwire por sincronización solo salta cuando hay datos para traer: una integración sin ventas recientes podría quedar apuntando a otra cuenta durante semanas sin que nadie se entere. Si detecta que el token resuelve a otra cuenta, **desactiva la integración**.

Las tasks distinguen dos clases de error. `ContoAuthError`, `ContoAccountMismatch`, `ContoAccountInactive` y `ContoNotLinked` **no se reintentan**: reintentar un token revocado solo demora la alerta. `ContoUnavailable` sí, con hasta 3 reintentos cada 5 minutos.

## 6.2 — Desde cuándo importar

`import_from` es obligatorio para la primera corrida de ventas. Sin él, la primera sincronización intentaría traer todo el histórico de la cuenta. Para ampliar el histórico después, se mueve la fecha hacia atrás y se limpia `last_sales_sync`; la unicidad de `voucher_id` hace que lo ya importado no se duplique.

**Decidido: se importa desde julio de 2026.** Se carga `import_from = 2026-07-01 00:00` (hora Argentina) al configurar la integración.

## 7 — Falla visible

Si el token se revoca o rota en Conto, la sincronización empieza a recibir 401. Eso tiene que aparecer como alerta en la pantalla de estado, no simplemente dejar de traer datos. Una integración que muere en silencio se descubre en el cierre de mes con semanas de ventas faltando — es el modo de falla más caro y el más fácil de prevenir.

Lo mismo para el tripwire de `cuenta_id` de §3 y para vouchers en estado `ERROR`.

## 8 — Trabajo previo pendiente

- **Diagnóstico de `Producto.sku` en producción.** El comando [diagnostico_sku](backend/apps/inventario/management/commands/diagnostico_sku.py) es de solo lectura. En la base de desarrollo hay 2 productos de demo, así que el resultado local no dice nada. Se corre desde el contenedor local apuntando a la base de producción, usando la URL pública de Postgres de Railway (la interna `.railway.internal` solo resuelve dentro de Railway):

  ```bash
  docker-compose exec -e DATABASE_URL="<DATABASE_PUBLIC_URL de Railway>" backend python manage.py diagnostico_sku
  ```

- **`Producto.sku` único por sucursal.** Hoy no es único ni obligatorio ([inventario/models.py:99](backend/apps/inventario/models.py:99)). Único **por sucursal**, nunca global. Depende del diagnóstico anterior.
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

2. Correr **"Corregir canales"** en Conto. Las ventas históricas quedaron marcadas como `presencial` aunque vinieran de Tienda Nube; si se importa antes, el histórico entra clasificado mal. Es idempotente, se puede repetir.
3. Cargar la integración en Django admin con `base_url`, token e `import_from`.
4. Verificar la vinculación y confirmar el nombre de cuenta que devuelve Conto.
5. Activar con `channels_to_import = ['tiendanube']`.
6. Primera corrida de stock, revisar los SKU que no matchean.
7. Primera corrida de ventas sobre una ventana corta antes de ampliar `import_from` al histórico completo.

## 10 — Estimación restante

| Etapa | Días | Bloqueado por Conto |
|---|---|---|
| Constraint de SKU por sucursal + backfill | 0,5 | Sí (diagnóstico en producción) |
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
| `POST /api/integraciones/conto/{id}/sincronizar/` | Encola un sync ahora (`ventas`, `stock` o `todo`) |
| `GET /api/integraciones/conto-ventas/` | Vouchers importados. Filtrable por `status`, `type`, `channel` |
| `POST /api/integraciones/conto-ventas/{id}/reprocesar/` | Reprocesa desde el payload guardado, sin consultar Conto |

Códigos de alerta que devuelve `estado`: `SIN_VINCULAR`, `INACTIVA`, `SIN_FECHA_DE_INICIO`, `VOUCHERS_CON_ERROR`, `NUNCA_SINCRONIZADA`, `SINCRONIZACION_DETENIDA`.

`SINCRONIZACION_DETENIDA` es el que implementa §7: salta si pasaron más de 2 horas sin importar ventas, cuando debería pasar cada 15 minutos.
