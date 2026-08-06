# Puesta en marcha de la integración con Conto

Guía operativa paso a paso. El diseño y las decisiones están en [INTEGRACION_CONTO_SPEC.md](INTEGRACION_CONTO_SPEC.md); acá solo está qué hacer y en qué orden.

**Datos fijos:**

| Qué | Valor |
|---|---|
| `base_url` de Conto | `https://conto-production.up.railway.app` |
| Admin local | `http://localhost:8000/admin/integraciones/contointegration/` |
| Canal a importar | `tiendanube` |
| Importar desde | `2026-07-01 00:00` |

---

## Antes de empezar

**Pedirle a Conto dos tokens, los dos de la empresa de AME.** La pantalla de Conto pide un nombre para cada uno, así que:

- `Plataforma Estética - local`
- `Plataforma Estética - producción`

Son dos porque el que ande en tu máquina lo vas a querer revocar después sin cortar producción.

**Y un tercero cuando esté lista la cuenta de prueba de Conto**, para los casos de reversión (Fase 3). Ese es el único ítem que Conto tiene pendiente.

---

# Fase 1 — Prueba local con datos reales

La integración **solo hace GET** contra Conto, y Conto rechaza con 403 cualquier otro método. Apuntar tu entorno local a la cuenta real de AME no puede modificar nada del lado de ellos: todo lo que se escribe va a tu Postgres local, que es descartable.

## 1.1 Levantar el entorno y frenar el automático

```bash
docker-compose up -d
docker-compose stop celery-beat
```

Beat se frena a propósito. Tu `docker-compose` corre Celery, así que con la integración activa las ventas se importarían solas cada 15 minutos — y en esta fase querés controlar el orden de cada corrida.

## 1.2 Usuario de admin — normalmente no hace falta

Se usa el admin de Django de la Plataforma Estética (`http://localhost:8000/admin`), así que si ya entrás con tu usuario de desarrollo, salteá este paso.

Solo si arrancás con una base vacía:

```bash
docker-compose exec backend python manage.py createsuperuser
```

> **Lo único que conviene chequear** es que tu usuario tenga `rol = ADMIN` y su centro estética asignado. Para el admin de Django alcanza con `is_superuser`, pero los endpoints de `/api/integraciones/` exigen `rol='ADMIN'` y filtran por centro: sin eso devuelven 403 sin motivo aparente. Un usuario recién creado con `createsuperuser` queda en `rol='EMPLEADO'` y sin centro.

## 1.3 Cargar la integración

Andá a `http://localhost:8000/admin/integraciones/contointegration/add/` y completá:

| Campo | Valor |
|---|---|
| Centro estética | el que tengas en local |
| Sucursal | la de ese centro |
| Base url | `https://conto-production.up.railway.app` |
| Token | el token `local` |
| Activa | **apagada** |
| Canales a importar | `["tiendanube"]` |
| Crear productos faltantes | **apagado** |
| Crear clientes faltantes | **apagado** (ver nota abajo) |
| Importar desde | `2026-07-01 00:00` |

Guardá.

> **Sobre "Crear clientes faltantes" en OFF:** si lo dejás prendido, caen en tu base local los nombres, emails y teléfonos reales de los compradores de AME. Apagado igual verificás montos, fechas, medios de pago y productos, que es lo que interesa.

> **Sobre "Crear productos faltantes" en OFF:** con el flag prendido, la primera corrida de stock crea todo el catálogo de Conto. Apagado, en cambio, te **lista** los SKU que no matchean — que es justo lo que necesitás para el emparejamiento.

"Activa" no te va a dejar prenderla todavía. Es correcto: primero hay que verificar.

**Este es el único lugar donde se carga el token.** Queda guardado ahí, enmascarado, y nunca se devuelve por la API.

## 1.4 Chequear el contrato

Antes de sincronizar nada, verificá que lo que Conto expone coincida con lo acordado. Sin argumentos, el comando lee la `base_url` y el token de la integración que acabás de cargar:

```bash
docker-compose exec backend python manage.py verificar_conto
```

Revisá el reporte:

- **Todo `OK`** → seguí
- **Algún `FALLA`** → paralo acá y mandale el reporte a Conto. Importar con el contrato roto ensucia datos
- **`AVISO`** → no bloquea, se pierde información. Mirá qué es

Las líneas `N/D` son informativas: te muestran los valores reales de `canal`, `estado`, `medio_pago` y los tipos de ítem que devolvió Conto. Confirmá que sean los esperados.

Dos detalles: la ventana por defecto es de 30 días, agregale `--days 40` si querés cubrir todo julio. Y el chequeo hace tres requests con un token inventado a propósito, para confirmar que los endpoints devuelvan 401 — si Conto tiene log de accesos van a ver tres intentos rechazados, es esperado.

## 1.5 Verificar la vinculación

**Esto no es un campo del formulario, es una acción del listado.** Guardá el formulario y volvé a `http://localhost:8000/admin/integraciones/contointegration/` (sin el `/add/`).

Ahí: tildá el checkbox de la fila → desplegable **"Acción:"** arriba de la lista → **"Verificar vinculación con Conto"** → botón **"Ejecutar"**.

Tiene que decir *"vinculado a «AME…»"*. **Leé el nombre y confirmá que sea la cuenta correcta** — es el control que evita leer los datos de otro negocio.

Si dice otra cosa, el token está mal. No sigas.

## 1.6 Activar

Editá la integración y prendé **Activa**. Ahora sí te lo va a permitir.

## 1.7 Sincronizar stock y anotar los SKU sin match

Acción **"Sincronizar stock desde Conto"**.

El mensaje te va a decir cuántos se actualizaron, cuántos se crearon y cuántos quedaron sin match. Con el flag apagado deberían quedar todos sin match, porque ninguno de los productos locales tiene código.

**Guardá esa lista de SKU.** Es el catálogo real de Conto y es el insumo para emparejar los 13 productos de producción.

## 1.8 Importar ventas y verificar la plata

Acción **"Importar ventas desde Conto"**.

Después andá a Finanzas y **compará contra la realidad**: tomá una orden de Tienda Nube que conozcas y verificá que coincidan monto, fecha, medio de pago y producto.

Chequeos concretos:

- El **monto por línea de producto** debe ser `precio_unitario × cantidad`, con el descuento prorrateado si hubo
- El **envío** aparece como transacción aparte (`INCOME_OTHER`), no sumado al producto
- La **fecha** es la de Argentina. Una venta del 3 a las 22:30 tiene que aparecer el **3**, no el 4
- El **medio de pago** de una venta con Mercado Pago tiene que decir MercadoPago, no Efectivo

Si algo no cuadra, pará y avisame antes de seguir.

## 1.9 Probar el automático

```bash
docker-compose start celery-beat
```

Esperá 15 minutos y confirmá que la corrida automática hizo lo mismo que la manual. Podés mirar el estado en el admin o en los logs:

```bash
docker-compose logs -f celery
```

---

# Fase 2 — Verificar las reversiones

Requiere el token de la **cuenta de prueba** de Conto, con una nota de crédito y una venta cancelada cargadas.

Son los dos caminos más delicados del código —la nota de crédito genera un gasto compensatorio, la cancelación borra transacciones— y no se pueden probar si esos documentos no existen. Por eso van en una cuenta aparte: crear una nota de crédito falsa en la cuenta real de AME les ensuciaría la contabilidad.

## 2.1 Crear un segundo centro en local

En `http://localhost:8000/admin/` creá otro Centro Estética con su sucursal.

`ContoIntegration` es OneToOne contra el centro y `conto_account_id` es único, así que un centro no puede tener dos cuentas de Conto — pero dos centros sí. De paso esto ejercita el aislamiento entre tenants con datos reales.

## 2.2 Cargar la integración de prueba

Mismos pasos que 1.3 a 1.8, con el token de la cuenta de prueba y el segundo centro.

## 2.3 Qué tiene que pasar

- **Nota de crédito** → una transacción de tipo Gasto en la categoría "Devoluciones", por el monto de la nota, con la venta original referenciada en las notas
- **Venta cancelada** → sus transacciones desaparecen, y el voucher queda como "Omitida" conservando el payload

Y lo más importante: **cada centro tiene que ver solo sus propios datos.** Verificá que las ventas del centro de prueba no aparezcan en Finanzas del centro de AME.

---

# Fase 3 — Producción

> **Antes de arrancar:** confirmá que la reimportación en local dejó los vouchers cuadrando contra el `total` de Conto (columna "Descuadre" en verde en el admin, o cero alertas `VOUCHERS_CON_DESCUADRE`). Era un bug de la API de Conto, ya corregido de su lado, pero hay que verificarlo con datos antes de escribir en los libros reales. Ver §15 de [INTEGRACION_CONTO_SPEC.md](INTEGRACION_CONTO_SPEC.md).

## 3.1 Commitear y deployar

```bash
git add backend/apps/integraciones INTEGRACION_CONTO_SPEC.md PUESTA_EN_MARCHA_CONTO.md
git commit -m "..."
git push
```

En los logs del deploy de Railway confirmá que corrieron las migraciones:

```
Running migrations...
  Applying integraciones.0001_initial... OK
  Applying inventario.0005_alter_producto_sku_producto_unique_sku_per_sucursal... OK
```

Si una falla, el deploy queda en rojo y no sirve tráfico con la base a medias. Eso es lo correcto.

## 3.2 Emparejar los 13 SKU

En producción hay 13 productos en la sucursal Banfield, **ninguno con código**. Con la lista de SKU de Conto que sacaste en 1.7, cargá el código de cada uno desde el admin o desde la UI de productos.

Si te equivocás y repetís un código, ahora te lo rechaza con un mensaje claro en vez de dar error 500.

Los que no correspondan a nada de Conto, dejalos sin código: no molestan.

## 3.3 Cargar la integración

Mismos pasos que 1.3 a 1.6, pero:

- Con el token de **producción**, no el que usaste en local
- Sucursal **Banfield**
- **Crear productos faltantes: apagado** para la primera corrida
- **Crear clientes faltantes: prendido** — acá sí lo querés, es la base de compradores online del centro

## 3.4 Primera corrida controlada

1. **Sincronizar stock desde Conto (catálogo completo)** → los 13 emparejados deberían actualizarse. Revisá el listado de los que no matchean
2. Si el listado es razonable, prendé **Crear productos faltantes** y volvé a correr **la completa**: se crean los que Conto tiene y la plataforma no
3. **Importar ventas** → revisá en Finanzas antes de seguir

> **Usá siempre la acción "catálogo completo" en estos primeros pasos.** La incremental le pregunta a Conto qué cambió desde la última corrida, y cuando el cambio es de nuestro lado —prender un flag, emparejar SKU— la respuesta es "nada" y la sincronización no hace nada. Se ve como si el flag no funcionara.
>
> Una vez que todo está andando, la incremental es la correcta y es la que corre el cron.

## 3.5 Ampliar el histórico (opcional)

Conto confirmó que el canal es confiable para todos los registros, así que **no hay fecha de corte técnica**. Si querés traer más atrás que julio: movés "Importar desde" a la fecha nueva, borrás "Última sincronización de ventas" y volvés a importar. Lo ya importado no se duplica.

---

# Fase 4 — El cron de Railway

Sin esto, en producción **nada dispara la sincronización**. La integración quedaría configurada, verificada y sin traer una sola venta.

En el proyecto de Railway: **New** → **GitHub Repo** → el mismo repo.

| Config | Valor |
|---|---|
| Nombre | `conto-sync` |
| Start command | `python manage.py sincronizar_conto --que todo` |
| Cron schedule | `*/15 * * * *` |
| Variables | `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `DEBUG=0`, `ALLOWED_HOSTS` |

**El start command es el paso crítico.** Si no lo sobrescribís, el servicio usa `entrypoint.sh`, levanta Gunicorn y nunca termina — el cron no volvería a dispararse nunca.

Esperá 15 minutos y confirmá en el admin que la última sincronización se movió.

---

# Si algo sale mal

**Mirá el estado de la integración.** El endpoint `GET /api/integraciones/conto/{id}/estado/` devuelve contadores y alertas con código:

| Código | Qué significa |
|---|---|
| `SIN_VINCULAR` | Falta verificar la vinculación |
| `INACTIVA` | Está apagada, no sincroniza |
| `SIN_FECHA_DE_INICIO` | Falta "Importar desde" |
| `VOUCHERS_CON_ERROR` | Hay ventas que no se pudieron importar |
| `NUNCA_SINCRONIZADA` | Todavía no importó nada |
| `SINCRONIZACION_DETENIDA` | Pasaron más de 2 horas sin importar, cuando debería ser cada 15 minutos |

**Ventas con error:** en el admin, en "Ventas de Conto", filtrá por estado Error. Cada una guarda el payload crudo y el mensaje. Arreglás la causa (el producto que faltaba, el código mal cargado) y la reprocesás con `POST /api/integraciones/conto-ventas/{id}/reprocesar/`, sin volver a consultar a Conto.

**Si el token se revoca o rota:** la sincronización empieza a fallar con 401 y salta `SINCRONIZACION_DETENIDA`. No se reintenta a propósito: reintentar un token revocado solo demora la alerta.

**Si el token pasa a resolver a otra cuenta:** la sincronización se aborta sin importar nada y la integración se desactiva sola. Es el control que evita mezclar los datos de dos negocios.

---

# Decisiones que quedan pendientes

- **`payload_origen` y datos personales** (§14 del spec). Decidilo **antes** de importar el histórico completo, o hay que limpiar retroactivamente. Lo más simple es descartar ese campo antes de guardar el payload.
- **¿Importamos el canal `mercadopago`?** Conto lo tiene aparte de `tiendanube`. Si son ventas por link de pago directo, es facturación real que hoy queda afuera del filtro. Vale preguntarles qué son.
- **`GET /api/compras/`** (fase 2, §13 del spec). Mientras no exista, los gastos por compra de mercadería no se registran.
- **Revocar el token local** cuando termines de probar.
