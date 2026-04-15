# Guía Rápida: Deploy en Railway

Deployment en Railway en **30 minutos** - Ultra conciso.

---

## ⚡ Prerequisitos

- [ ] Código en GitHub
- [ ] Docker funciona localmente
- [ ] Cuenta GitHub

---

## 📦 Paso 1: Preparar el Proyecto (10 min)

### 1.1 Verificar que existe `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Código
COPY . .

# Archivos estáticos
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:$PORT", "--workers", "2"]
```

### 1.2 Verificar `requirements.txt` incluye

```txt
gunicorn
psycopg2-binary
django-cors-headers
djangorestframework
djangorestframework-simplejwt
python-decouple
whitenoise
```

### 1.3 Actualizar `backend/config/settings.py`

```python
import os
from decouple import config

# SECURITY
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')

# DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('PGDATABASE'),
        'USER': config('PGUSER'),
        'PASSWORD': config('PGPASSWORD'),
        'HOST': config('PGHOST'),
        'PORT': config('PGPORT', default='5432'),
    }
}

# CORS
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='').split(',')
CORS_ALLOW_CREDENTIALS = True

# Static files (Whitenoise)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Agregar esto
    # ... resto
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### 1.4 Crear `.env.example` en `/backend`

```bash
DEBUG=False
SECRET_KEY=cambiar-en-produccion
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL (Railway auto-genera estas)
PGDATABASE=railway
PGUSER=postgres
PGPASSWORD=password
PGHOST=containers-us-west.railway.app
PGPORT=5432

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,https://tu-app.vercel.app

# Redis (opcional)
REDIS_URL=redis://localhost:6379

# Cloudinary (opcional)
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

### 1.5 Pushear a GitHub

```bash
git add .
git commit -m "Preparar para deploy en Railway"
git push origin main
```

---

## 🚂 Paso 2: Deploy en Railway (10 min)

### 2.1 Crear cuenta

1. Ir a https://railway.app
2. Click "Login" → "Login with GitHub"
3. Autorizar Railway

### 2.2 Crear proyecto

1. Click "New Project"
2. Selecciona "Deploy from GitHub repo"
3. Busca y selecciona `Plataforma-Estetica`
4. Click en el repo

### 2.3 Agregar PostgreSQL

1. Click "New" (botón arriba derecha)
2. Click "Database"
3. Selecciona "Add PostgreSQL"
4. Espera 30 segundos a que se aprovisione

### 2.4 Configurar variables de entorno en el servicio Backend

1. Click en el servicio "plataforma-estetica" (el cuadro del backend)
2. Pestaña "Variables"
3. Click "Raw Editor"
4. Pega esto:

```bash
DEBUG=False
SECRET_KEY=genera-una-clave-aleatoria-de-50-caracteres-aqui
ALLOWED_HOSTS=${{RAILWAY_PUBLIC_DOMAIN}}
CORS_ALLOWED_ORIGINS=https://tu-frontend.vercel.app
```

5. Ahora conecta PostgreSQL (Railway ya tiene las variables):
   - Click "+ New Variable" → "Add Reference"
   - Selecciona cada una de estas del servicio Postgres:
     - `PGDATABASE`
     - `PGHOST`
     - `PGPASSWORD`
     - `PGPORT`
     - `PGUSER`

6. Click "Deploy" (arriba derecha)

### 2.5 Esperar deploy (3-5 min)

- Railway build automáticamente
- Ver logs en tiempo real en la pestaña "Deployments"
- Cuando veas "Build successful" → listo

### 2.6 Obtener URL pública

1. Pestaña "Settings"
2. Sección "Networking"
3. Click "Generate Domain"
4. Copia la URL (ej: `plataforma-production.up.railway.app`)

---

## 🗄️ Paso 3: Migraciones y Superuser (5 min)

### 3.1 Correr migraciones

**Opción A: Desde Railway Dashboard**
1. Click en el servicio backend
2. Pestaña "Settings"
3. Scroll a "Deploy"
4. En "Custom Start Command" poner temporalmente:
```bash
python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```
5. Redeploy

**Opción B: Desde Railway CLI** (más rápido)
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Linkear al proyecto
railway link

# Correr migraciones
railway run python manage.py migrate

# Crear superuser
railway run python manage.py createsuperuser
```

### 3.2 Verificar

Abre en el navegador:
```
https://tu-app.up.railway.app/api/
```

Deberías ver la API de Django REST Framework.

---

## 🎨 Paso 4: Deploy Frontend en Vercel (5 min)

### 4.1 Crear cuenta Vercel

1. Ir a https://vercel.com
2. "Sign Up" → "Continue with GitHub"

### 4.2 Deploy

1. Click "Add New" → "Project"
2. Import tu repo `Plataforma-Estetica`
3. Configurar:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Variables de entorno:
```bash
VITE_API_URL=https://tu-app.up.railway.app/api
```
5. Click "Deploy"
6. Espera 2-3 min

### 4.3 Actualizar CORS en Railway

1. Vuelve a Railway
2. Click en el servicio backend → Variables
3. Actualiza `CORS_ALLOWED_ORIGINS`:
```bash
CORS_ALLOWED_ORIGINS=https://tu-app.vercel.app
```
4. Guarda (auto-redeploy)

---

## ✅ Paso 5: Verificar que Funciona

### 5.1 Checklist

- [ ] Backend responde: `https://tu-app.up.railway.app/api/`
- [ ] Frontend carga: `https://tu-app.vercel.app`
- [ ] Login funciona
- [ ] Puedes crear datos de prueba

### 5.2 Si algo falla

**Ver logs en Railway:**
1. Click en el servicio backend
2. Pestaña "Deployments"
3. Click en el último deploy
4. Ver logs en tiempo real

**Errores comunes:**
- `DisallowedHost`: Actualiza `ALLOWED_HOSTS`
- `CORS error`: Actualiza `CORS_ALLOWED_ORIGINS`
- `Database connection`: Verifica que las variables `PG*` estén referenciadas

---

## 🔧 Comandos Útiles

```bash
# Ver logs en tiempo real
railway logs

# Abrir consola de Django
railway run python manage.py shell

# Correr comandos custom
railway run python manage.py <comando>

# Ver variables de entorno
railway variables

# Ver info del proyecto
railway status
```

---

## 💰 Monitorear Uso

1. Dashboard de Railway
2. Click en tu proyecto
3. Ver "Usage" (arriba derecha)
4. Verás cuánto del crédito gratis ($5) has usado

**Mientras estés bajo $5/mes → Gratis**

---

## 🚀 Próximos Pasos

### Servicios adicionales (cuando los necesites):

**Redis (Cache)**:
1. En Railway: New → Database → Add Redis
2. Agregar variable: `REDIS_URL=${{Redis.REDIS_URL}}`

**Cloudinary (Imágenes)**:
1. Signup en https://cloudinary.com
2. Agregar variables en Railway:
```bash
CLOUDINARY_CLOUD_NAME=tu-cloud-name
CLOUDINARY_API_KEY=tu-api-key
CLOUDINARY_API_SECRET=tu-api-secret
```

**Twilio (WhatsApp)**:
1. Signup en https://twilio.com
2. Agregar en Railway:
```bash
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=tu-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

---

## 📋 Resumen

| Paso | Tiempo |
|------|--------|
| 1. Preparar proyecto | 10 min |
| 2. Deploy Railway | 10 min |
| 3. Migraciones | 5 min |
| 4. Deploy Vercel | 5 min |
| **TOTAL** | **30 min** |

**Costo**: USD $0/mes (hasta 10-20 usuarios)

---

## 🆘 Ayuda Rápida

**Railway Dashboard**: https://railway.app/dashboard
**Railway Docs**: https://docs.railway.app
**Vercel Dashboard**: https://vercel.com/dashboard

**Problemas?** Revisa los logs en Railway y Vercel.

---

✅ **LISTO! Tu plataforma está online.**
