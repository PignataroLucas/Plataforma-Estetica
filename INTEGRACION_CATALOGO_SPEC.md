# Catálogo de productos en la app + almacenamiento en la nube

**Estado:** especificado, sin implementar
**Fecha:** 07/08/2026

Documento de handoff: está escrito para que se pueda implementar **sin haber
participado de la conversación donde se decidió**. Todo lo que dice "verificado"
se comprobó contra el código o contra la base de datos en la fecha de arriba.

---

## 1. Qué se quiere y por qué

Una pantalla de **catálogo de productos** en la app de clientas: grilla de
productos activos, y al tocar uno, su ficha con foto, descripción, precio y un
**video de cómo aplicar el producto reproducido dentro de la app**.

Importa porque los productos son la **fuente principal de ingresos del centro**.
Es el equivalente de la ficha de tratamiento, del lado que factura.

### Fuera de alcance (decidido)

- **Almacenamiento privado / datos sensibles.** Las fotos de antes y después de
  clientas, las fotos de staff y los comprobantes financieros **no se migran a la
  nube por ahora**. Los campos existen pero están vacíos (verificado: 0 registros
  en los cinco). Cuando se retomen van a necesitar un bucket privado y URLs
  firmadas con vencimiento, porque son datos de salud de personas
  identificables. La sección 4.1 explica cómo dejar el terreno preparado sin
  hacer el trabajo ahora.
- **Comprar desde la app.** El botón "Comprar" de la rutina sigue siendo un botón
  sin acción. Esto es catálogo, no e-commerce.
- **Stock real.** Ver el punto 7.2: el stock que tiene la plataforma es el del
  depósito, no el del mostrador.

---

## 2. Estado verificado del código

Esto ya existe. **No hace falta construirlo de nuevo.**

| Pieza | Dónde | Estado |
|---|---|---|
| Endpoint público de catálogo | `apps/public_api/views.py::ProductosPublicosView` | ✅ Filtra `tipo=REVENTA` + `activo=True` |
| Serializer público | `apps/public_api/serializers.py::ProductoPublicoSerializer` | ✅ Devuelve nombre, descripción, marca, precio, oferta, `foto`, categoría y campos de recompra |
| Campo de foto | `apps/inventario/models.py::Producto.foto` | ✅ `ImageField(upload_to='productos/')` |
| Cliente HTTP en la app | `client-app/src/services/public.ts::getProductos` | ✅ Escrito, **nunca usado** |
| `STORAGES` (API moderna de Django 4.2) | `backend/config/settings.py` | ✅ El dict ya existe |
| Pillow | `backend/requirements.txt` | ✅ Instalado |

Lo que **no** existe:

- Endpoint de **detalle** de producto (solo hay listado). El molde a copiar es
  `ServicioPublicoDetalleView` en el mismo archivo.
- Campo de **video** en `Producto`.
- Cualquier manejo de **foto en el CRM**: `frontend/src/components/productos/ProductoForm.tsx`
  no menciona el campo. Hoy las fotos solo se cargan desde el admin de Django.
- `boto3` / `django-storages` en las dependencias.

### El dato que manda sobre el cronograma

```
productos de reventa activos: 31
  con foto:        0
  con descripción: 0
  con marca:       1
  con SKU:        31
```

**Ningún producto tiene foto ni descripción.** La pantalla se puede construir en
días; el contenido lo tiene que cargar el centro, y sin él son 31 rectángulos
grises con un nombre y un precio. Un catálogo de cosmética sin fotos no es un
catálogo.

De ahí el orden de fases: primero se habilita **cargar** contenido, para que el
centro empiece mientras se construye la pantalla.

### Nada que migrar

Los siete campos de archivo del proyecto están vacíos (verificado): foto de
producto, logo del centro, foto de cliente, foto antes, foto después, foto de
usuario y comprobante de transacción. **No hay archivos en disco que rescatar**,
así que no hace falta comando de migración ni hay riesgo de pérdida.

---

## 3. Decisiones ya tomadas

Están cerradas. Si algo se reabre, que sea por un motivo nuevo, no por
desconocer el porqué.

| Decisión | Motivo |
|---|---|
| **AWS S3** | Encaja técnicamente y es lo que más pesa en búsquedas laborales, que es un objetivo explícito del dueño del proyecto. Cloudflare R2 es compatible con la API de S3: si algún día el tráfico pesa, se cambia el endpoint sin tocar código. |
| **Un storage con nombre, no `default`** | Ver 4.1. Falla cerrado. |
| **Video con archivo propio, no YouTube** | Se quiere el video reproducido dentro de la app. Verificado: `expo-video` **no reproduce YouTube** — para eso hace falta un WebView con el player de YouTube, con su marca y su chrome. "Player nativo" y "YouTube" son incompatibles. |
| **Video en fase aparte** | El catálogo está frenado por las fotos, que se resuelven en 1-2 días. El video suma transcodificación, que merece pensarse sin bloquear el catálogo. |
| **Transcodificar con ffmpeg + cron** | Reutiliza el patrón de comando programado que ya existe y está probado para notificaciones. AWS MediaConvert es lo correcto a otra escala; acá es pagar complejidad que no se necesita. |
| **Costo y precio son de solo lectura en el CRM** | El centro confirmó que no los va a editar más. Conto es la fuente de verdad. Ver 5.2, que además arregla una condición de carrera. |

---

## 4. Fase 1 — Imágenes en S3

**Estimación: 1 a 2 días.**

### 4.1 Arquitectura: por qué NO usar `default`

Lo intuitivo sería apuntar el storage `default` a S3. **No hacerlo.**

De los siete campos de archivo, solo dos son públicos (foto de producto y logo
del centro). Los otros cinco son sensibles. Si `default` fuera el bucket público,
el día que alguien suba una foto de antes/después desde el admin de Django, ese
archivo aterriza en un bucket de lectura pública **sin que nadie se entere**.

En cambio, con un storage con nombre al que los campos públicos optan
explícitamente, un campo nuevo que nadie pensó nace privado. Falla cerrado, que
es como tiene que fallar cuando hay datos de salud de por medio. Cuesta lo mismo.

```python
# backend/config/settings.py
STORAGES = {
    'default': {                      # sigue en disco local; los campos
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'publico': {                      # solo para lo que va al catálogo
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'bucket_name': config('AWS_STORAGE_BUCKET_NAME'),
            'region_name': config('AWS_S3_REGION_NAME', default='sa-east-1'),
            'querystring_auth': False,   # URLs limpias: el contenido es público
            'file_overwrite': False,     # dos subidas homónimas no se pisan
            'default_acl': None,         # los buckets nuevos tienen ACLs deshabilitadas
            'custom_domain': config('AWS_S3_CUSTOM_DOMAIN', default=None),
        },
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}
```

`custom_domain` queda vacío por ahora. Cuando llegue CloudFront (fase 4), se
completa con el dominio de la distribución y **todas las URLs cambian solas**,
sin tocar código.

### 4.2 Enganchar los campos públicos

```python
# backend/apps/inventario/models.py (y empleados/models.py para el logo)
from django.core.files.storage import storages

def storage_publico():
    """
    Callable y no la instancia: Django serializa el `storage` dentro de la
    migración, y una instancia dejaría el bucket congelado en el historial.
    """
    return storages['publico']


class Producto(models.Model):
    foto = models.ImageField(
        upload_to='productos/', storage=storage_publico, null=True, blank=True
    )
    foto_thumb = models.ImageField(
        upload_to='productos/thumbs/', storage=storage_publico, null=True, blank=True,
        help_text="Miniatura generada automáticamente. No cargar a mano.",
    )
```

Genera una migración de `AlterField`. Es inocua: no hay archivos.

### 4.3 Miniaturas

S3 no transforma imágenes (Cloudinary sí; es la única ventaja que se resigna).
Servir una foto de 3 MB por datos móviles en una grilla de 31 productos es una
mala experiencia.

Se genera la miniatura al subir, con Pillow, que ya es dependencia:

- Ancho 400 px, alto proporcional.
- Formato WebP con calidad ~80. Pesa la mitad que JPEG a igual calidad y lo
  soportan todas las versiones de Android e iOS que la app targetea.
- Se dispara solo cuando `foto` cambió, no en cada guardado.

El serializer público devuelve las dos: `foto_thumb` para la grilla, `foto` para
la ficha.

### 4.4 Configuración de AWS

Lo tiene que hacer el dueño de la cuenta.

**Bucket:** uno solo, región `sa-east-1` (São Paulo) por latencia desde
Argentina. En "Block Public Access" hay que **desactivar solo** el bloqueo de
políticas públicas; el resto queda activo.

**Política del bucket** (lectura pública de los objetos):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "LecturaPublica",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::NOMBRE-DEL-BUCKET/*"
    }
  ]
}
```

**Usuario de IAM** para la aplicación, con permisos mínimos. Sin
`s3:PutObjectAcl`, porque las ACLs están deshabilitadas:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ObjetosDelBucket",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::NOMBRE-DEL-BUCKET/*"
    },
    {
      "Sid": "ListarElBucket",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::NOMBRE-DEL-BUCKET"
    }
  ]
}
```

**Variables de entorno** (en el panel de Railway, nunca en el repo):

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_STORAGE_BUCKET_NAME
AWS_S3_REGION_NAME=sa-east-1
AWS_S3_CUSTOM_DOMAIN      # vacío hasta la fase 4 (CloudFront)
```

**Dependencias:** `django-storages[s3]` y `boto3` a `requirements.txt`.

**Costo:** 5 GB gratis los primeros 12 meses; después ~USD 0,023 por GB por mes.
A esta escala, centavos.

---

## 5. Fase 2 — Carga desde el CRM

**Estimación: 1 a 2 días.** Sin esto el centro no puede cargar nada por su
cuenta y depende de que alguien entre al admin de Django.

### 5.1 Formulario

Agregar a `frontend/src/components/productos/ProductoForm.tsx`:

- Carga de **foto** con vista previa y validación (máx. ~5 MB, solo imágenes).
- Campo de **descripción** (hoy el modelo lo tiene y el formulario no lo expone).
- Requiere enviar como `multipart/form-data`, no JSON.

### 5.2 Bloquear los campos que administra Conto

**Esto arregla un defecto real, no es cosmético.**

Verificado: el CRM guarda con `api.put()` mandando **todo el formulario**
(`frontend/src/hooks/useProductos.ts`, `updateProducto`). El sync de Conto
actualiza `stock_actual`, `precio_costo` y `precio_venta` por su cuenta. Entonces:

1. 10:00 — se abre el producto para cargarle la descripción
2. 10:05 — corre el sync de Conto y actualiza stock y precio
3. 10:10 — se guarda la descripción → el `PUT` **reescribe stock y precio con los
   valores viejos de las 10:00**

La descripción se guarda bien, pero los datos de Conto vuelven atrás hasta el
próximo sync. Es silencioso, y el momento de máxima exposición es justamente el
que viene: alguien cargando 31 fotos con formularios abiertos un rato largo.

**Arreglo:** `stock_actual`, `precio_costo` y `precio_venta` pasan a solo lectura
en el formulario, con una nota tipo *"lo administra Conto"*, y **no viajan en el
guardado**. El centro ya confirmó que no los va a editar más, así que no se
pierde nada.

Queda repartido limpio: **Conto manda sobre stock, costo y precio; el centro
manda sobre foto, descripción, nombre y video.** Sin superposición.

> Alternativa equivalente: cambiar `PUT` por `PATCH` mandando solo lo que cambió.
> Resuelve lo mismo y sirve para todos los formularios del CRM, pero toca más
> superficie. A criterio de quien implemente.

### 5.3 Antes de cargar las fotos: revisar el emparejamiento de SKU

El sync de Conto empareja por SKU. Si un producto no matchea y
`create_missing_products` está activo (es el default), Conto **crea uno nuevo** en
vez de actualizar el existente — y el nuevo nace sin foto.

Si eso pasa después de cargar el contenido, quedan dos productos y la pantalla de
catálogo muestra los dos: uno con foto y otro sin.

Los 31 productos tienen SKU cargado (verificado), pero falta confirmar que
**matcheen con los de Conto**. Existe un comando `emparejar_sku_conto` en
`apps/integraciones/management/commands/` que parece hecho para esto. **Correrlo
y revisar el resultado antes de que el centro cargue una sola foto.**

---

## 6. Fase 3 — API pública y pantalla

**Estimación: 3 a 4 días.** Sale con fotos y sin video.

### 6.1 Backend

**Endpoint de detalle.** Copiar `ServicioPublicoDetalleView`
(`apps/public_api/views.py`), que ya resuelve el scope correcto: solo productos
activos del centro pedido, así un id de otro centro devuelve 404 en vez de
filtrar datos.

```
GET /api/public/centros/<centro_id>/productos/<pk>/
```

**Sacar `disponible` del serializer.** Ver 7.2. Es media hora y evita un defecto
visible.

### 6.2 App

Molde a seguir: la ficha de tratamiento, que ya está construida y resuelve los
mismos problemas.

- `src/app/productos.tsx` — grilla con `foto_thumb`, nombre, marca y precio.
  Filtro por categoría, como ya hace la pantalla de tratamientos.
- `src/app/producto/[id].tsx` — ficha: foto grande, descripción, marca, precio,
  distintivo de oferta.
- `getProductos()` ya existe en `src/services/public.ts`; falta `getProducto(id)`.
- Enlazar desde `ProductoMini` (el de Mi rutina) a la ficha: hoy el paso de rutina
  muestra el producto pero no lleva a ningún lado.

**Dónde vive la pantalla.** La tab "Promos" está vacía y es candidata, pero
conviene decidirlo con criterio de producto: un catálogo de productos y un
programa de beneficios no son lo mismo.

---

## 7. Trampas conocidas

### 7.1 El sync de Conto NO pisa foto ni descripción

Verificado en `apps/integraciones/services.py::update_stock`: escribe con un
`update()` de queryset acotado a tres columnas.

```python
fields = {}
if stock is not None: fields['stock_actual'] = stock
if cost  is not None: fields['precio_costo'] = cost
if price is not None: fields['precio_venta'] = price
Producto.objects.filter(pk=producto.pk, sucursal=self.branch).update(**fields)
```

No toca `foto`, `descripcion`, `nombre`, `marca`, `categoria` ni `activo`. Y no
puede fallar: es un UPDATE de SQL sin validaciones ni señales. **Se puede cargar
contenido con tranquilidad.** El único riesgo es el de 5.2, que viene del lado
del CRM y no del sync.

### 7.2 `disponible` miente

`ProductoPublicoSerializer.get_disponible` devuelve `stock_actual > 0`. Pero
según `INTEGRACION_CONTO_SPEC.md` §4.0 (confirmado el 2026-08-07), desde el sync
con Conto `stock_actual` es el stock **del depósito**, no el del mostrador:

| Producto | Centro | Depósito |
|---|---|---|
| Crema Multivitamínica | 1 | 1315 |
| Duo Serum | 9 | **−5** |

O sea que la app le diría a una clienta que el **Duo Serum no está disponible**
mientras hay 9 en la vitrina.

**Sacar `disponible` del serializer público** antes de que exista una pantalla
que lo muestre. Si algún día se quiere mostrar disponibilidad de verdad, hace
falta separar el stock del centro del stock del depósito, que es un trabajo
aparte y está anotado como salida posible en el spec de Conto.

### 7.3 Fotos verticales

Las fotos de producto que saca un centro suelen ser verticales y de proporciones
irregulares. Definir una proporción fija para la grilla y usar `contentFit` de
`expo-image` (ya es dependencia) en vez de deformar.

---

## 8. Fase 4 — Video (proyecto aparte)

No bloquea el catálogo. Se especifica acá para que las fases anteriores no tomen
decisiones que después haya que deshacer.

### 8.1 Por qué es otro problema

Con imágenes el trabajo es subir, guardar y servir. El video suma dos cosas:

**Transcodificar.** Un clip vertical de 40 segundos grabado con un celular puede
pesar 150 MB en 4K. Además hay que mover el índice del archivo al principio
(`faststart`), porque si no **el video no arranca hasta descargarse entero** y
parece que la app se colgó. Ese detalle es el que hace que "subir el MP4 a S3" no
funcione.

**El tráfico de salida**, que es el único costo que escala con el uso. A la
escala de un centro son centavos, pero es la diferencia conceptual con las fotos.

### 8.2 Modelo

```python
class Producto(models.Model):
    video = models.FileField(upload_to='productos/videos/', storage=storage_publico,
                             null=True, blank=True)
    video_poster = models.ImageField(upload_to='productos/videos/posters/',
                                     storage=storage_publico, null=True, blank=True)
    video_estado = models.CharField(choices=[...])  # PENDIENTE/PROCESANDO/LISTO/FALLIDO
    video_url = models.URLField(blank=True)         # link externo, respaldo
```

Se mantienen **los dos**: archivo propio y link externo, con la app prefiriendo
el archivo si existe. Así la migración es gradual y lo que hoy funciona con un
link de YouTube no se rompe mientras se cargan los videos nuevos. El mismo
criterio aplica a `Servicio.video_url`, que ya existe.

### 8.3 Pipeline

Mismo patrón que el sistema de notificaciones: el centro sube, queda `PENDIENTE`,
y un comando programado por el cron de Railway lo procesa. **En producción no hay
worker de Celery** (el despliegue levanta solo Gunicorn), así que el comando es
el camino real. Precedente a copiar: `apps/notificaciones/management/commands/procesar_notificaciones.py`
y `backend/railway.notificaciones.cron.json`.

```bash
# transcodificar
ffmpeg -i entrada.mp4 -vf "scale=-2:1280" -c:v libx264 -preset medium -crf 23 \
       -c:a aac -b:a 128k -movflags +faststart salida.mp4

# imagen de portada
ffmpeg -i salida.mp4 -ss 00:00:01 -vframes 1 poster.jpg
```

Requiere `ffmpeg` en el Dockerfile (~100 MB de imagen).

### 8.4 Reproducción

Verificado para SDK 57: el player es **`expo-video`** (`useVideoPlayer` +
`VideoView`). Reproduce MP4 progresivo y HLS.

Para clips de 40 segundos **alcanza MP4 progresivo**: HLS sería sobreingeniería a
esta escala y a este volumen de audiencia.

`expo-video` **no reproduce YouTube**. Es la razón por la que el video propio es
la única forma de tener el player nativo, y está detrás de la decisión de la
sección 3.

### 8.5 CloudFront

Cuando llegue el video conviene poner CloudFront delante del bucket: cachea cerca
del usuario y abarata el tráfico. Del lado de la aplicación es **completar
`AWS_S3_CUSTOM_DOMAIN`** con el dominio de la distribución. Nada de código.

---

## 9. Orden y checklist

1. **Imágenes en S3** — bucket, IAM, `STORAGES`, campos públicos, miniaturas
2. **Carga en el CRM** — foto y descripción, campos de Conto bloqueados
3. *(en paralelo)* **El centro carga contenido** — es lo que manda el calendario
4. **API de detalle + pantalla de catálogo y ficha**
5. **Video** — proyecto aparte

Antes de dar por cerrada la fase 3:

- [ ] `emparejar_sku_conto` corrido y revisado, **antes** de cargar fotos
- [ ] `disponible` fuera del serializer público
- [ ] Costo, precio y stock de solo lectura en el CRM y fuera del payload
- [ ] Una foto sobrevive a un redeploy de Railway
- [ ] La grilla carga miniaturas, no los originales
- [ ] Un id de producto de otro centro devuelve 404, no datos
- [ ] Las claves de AWS están en Railway y no en el repo

---

## 10. Documentos relacionados

| Documento | Para qué |
|---|---|
| `INTEGRACION_CONTO_SPEC.md` | Qué campos administra Conto y por qué el stock es el del depósito (§4.0) |
| `NOTIFICACIONES_PUSH_SPEC.md` | Patrón de comando + cron de Railway, a copiar para el video |
| `PENDIENTES_AME.pdf` | Dónde encaja esto en el plan general (punto 1.4, almacenamiento) |
| `CLAUDE.md` | Convenciones del proyecto |
