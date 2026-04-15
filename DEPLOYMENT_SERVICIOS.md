# Guía de Deployment y Servicios Necesarios

Documento completo sobre los servicios que debes contratar para poner la plataforma en producción y que tus clientes puedan usarla.

---

## 🎯 Resumen Ejecutivo

Para deployar la plataforma necesitas contratar servicios en **3 categorías principales**:
1. **Hosting/Infraestructura** (backend, frontend, base de datos)
2. **Almacenamiento** (imágenes, archivos)
3. **Comunicaciones** (WhatsApp, email)

### Costos por Etapa

| Etapa | Costo Mensual | Para qué sirve |
|-------|---------------|----------------|
| **Testing/Validación** | **USD $0** | Probar la plataforma, validar producto (5-10 usuarios prueba) |
| **Primeros clientes** | **USD $13-27** | Primeros 10-20 clientes reales pagos ← **EMPEZÁ ACÁ** |
| **Crecimiento** | USD $120-160 | 20-50 clientes activos |
| **Producción escalada** | USD $250-400+ | 50-150+ clientes activos |

**🎯 Para lanzar YA con el mínimo costo**: USD $13-27/mes usando Railway + servicios gratuitos.

---

## 📊 Opciones de Deployment

### Opción 1: GRATIS (Testing/Validación - Primeros 1-3 meses)

**Total: USD $0-10/mes**

Ideal para probar, validar producto, primeros 5-10 clientes de prueba.

| Servicio | Proveedor | Plan | Costo Mensual |
|----------|-----------|------|---------------|
| **Backend** | Render | Free | USD $0 |
| **Database** | Supabase | Free | USD $0 |
| **Redis** | Upstash | Free | USD $0 |
| **Frontend** | Vercel | Hobby (gratis) | USD $0 |
| **Storage (Imágenes)** | Cloudinary | Free Tier | USD $0 |
| **WhatsApp** | Twilio Trial | Créditos gratis | USD $0 (temporal) |
| **Email** | SendGrid | Free Tier | USD $0 |
| **SSL/HTTPS** | Incluido | - | USD $0 |

**Pros**:
- ✅ **Completamente GRATIS** para empezar
- ✅ Sin tarjeta de crédito para comenzar (algunos servicios)
- ✅ SSL automático
- ✅ Suficiente para validar el producto

**Contras**:
- ⚠️ Backend se "duerme" después de 15 min sin uso (tarda 30-60 seg en despertar)
- ⚠️ Render Free se elimina después de 90 días de inactividad
- ⚠️ Supabase Free: límite 500 MB DB
- ⚠️ No apto para producción real con clientes pagos

**⚠️ IMPORTANTE**: Esta opción es para TESTING. Cuando tengas tus primeros clientes reales, debes pasar a Opción 2.

---

### Opción 2: Ultra Low-Cost (Primeros clientes reales)

**Total: USD $12-22/mes**

Ideal para primeros 10-20 clientes pagos, mínima inversión.

| Servicio | Proveedor | Plan | Costo Mensual |
|----------|-----------|------|---------------|
| **Backend + DB** | Railway | Pay-as-you-go | USD $5-10 |
| **Redis** | Upstash | Free Tier | USD $0 |
| **Frontend** | Vercel | Hobby (gratis) | USD $0 |
| **Storage** | Cloudinary | Free Tier | USD $0 |
| **WhatsApp** | Twilio | Pay-as-you-go | USD $7-12 |
| **Email** | SendGrid | Free Tier | USD $0 |

**Alternativas igualmente baratas**:
- **Fly.io**: USD $0-10/mes (backend + DB)
- **DigitalOcean App Platform**: USD $5/mes (backend) + USD $7/mes (DB) = USD $12/mes

**Pros**:
- ✅ MUY económico (menos de $1/día)
- ✅ **No se duerme** (siempre activo)
- ✅ Suficiente para 10-30 clientes
- ✅ Pay-as-you-go real (pagas solo lo que usas)

**Contras**:
- ⚠️ Recursos limitados (512 MB RAM)
- ⚠️ No apto para más de 30-40 clientes activos

---

### Opción 3: MVP Profesional (Crecimiento sostenido)

**Total: ~USD $40-55/mes**

Ideal para 20-50 clientes, crecimiento sostenido.

| Servicio | Proveedor | Plan | Costo Mensual |
|----------|-----------|------|---------------|
| **Backend** | Render | Starter | USD $7 |
| **Database** | Render Postgres | Starter | USD $7 |
| **Redis** | Upstash | Free/Paid | USD $0-5 |
| **Frontend** | Vercel | Hobby (gratis) | USD $0 |
| **Storage (Imágenes)** | Cloudinary | Free Tier | USD $0 |
| **WhatsApp** | Twilio | Pay-as-you-go | USD $20-30 |
| **Email** | SendGrid | Free Tier | USD $0 |
| **Monitoring** | Sentry | Free | USD $0 |

**Pros**:
- ✅ Económico pero profesional
- ✅ Siempre activo (no se duerme)
- ✅ Backups automáticos
- ✅ Suficiente para primeros meses

**Contras**:
- ⚠️ Render Starter tiene solo 512 MB RAM
- ⚠️ DB Starter tiene solo 1 GB storage

---

### Opción 4: Producción Estable

**Total: ~USD $80-120/mes**

Ideal para 20-100 clientes, crecimiento sostenido, profesional.

| Servicio | Proveedor | Plan | Costo Mensual |
|----------|-----------|------|---------------|
| **Backend (App)** | Railway/Render | Standard | USD $25-35 |
| **Base de datos** | Railway/Render Postgres | Standard | USD $15-20 |
| **Redis Cache** | Upstash Redis | Pay-as-you-go | USD $5-10 |
| **Frontend** | Vercel | Pro | USD $20 |
| **Storage** | AWS S3 | Standard | USD $5-10 |
| **CDN** | CloudFront (AWS) | Standard | USD $5-10 |
| **WhatsApp** | Twilio | Pay-as-you-go | USD $20-50 |
| **Email Transaccional** | SendGrid | Essentials | USD $15 |
| **Monitoring** | Sentry | Team | USD $26 |
| **Backups DB** | Incluido | - | USD $0 |

**Pros**:
- ✅ Rendimiento estable
- ✅ Escalabilidad media
- ✅ Monitoreo de errores
- ✅ Backups automáticos
- ✅ Profesional

**Contras**:
- ⚠️ Mayor costo mensual
- ⚠️ Requiere más configuración inicial

---

### Opción 5: Alta Escala (100+ clientes)

**Total: ~USD $250-500/mes**

Ideal para 100+ centros estéticos activos, alta demanda.

| Servicio | Proveedor | Plan | Costo Mensual |
|----------|-----------|------|---------------|
| **Backend** | AWS EC2/ECS | t3.medium | USD $35-50 |
| **Base de datos** | AWS RDS PostgreSQL | db.t3.medium | USD $60-80 |
| **Redis** | AWS ElastiCache | cache.t3.micro | USD $15-20 |
| **Load Balancer** | AWS ALB | Standard | USD $25 |
| **Frontend** | Vercel | Pro | USD $20 |
| **Storage** | AWS S3 | Standard | USD $15-30 |
| **CDN** | CloudFront | Standard | USD $20-40 |
| **WhatsApp** | Twilio | Standard | USD $50-100 |
| **Email** | SendGrid | Pro | USD $90 |
| **Monitoring** | Sentry + DataDog | Pro | USD $75 |
| **Backups** | AWS Backup | Standard | USD $10-20 |

**Pros**:
- ✅ Altamente escalable
- ✅ Rendimiento óptimo
- ✅ Control total
- ✅ Multi-región (si se necesita)

**Contras**:
- ⚠️ Mayor complejidad técnica
- ⚠️ Requiere DevOps
- ⚠️ Costo significativo

---

## 🔧 Servicios Detallados

### 1. Backend + API (Django)

Tu aplicación Django necesita correr en un servidor.

#### Opción A: Railway (Recomendado - MÁS BARATO)

**Plan**: Pay-as-you-go (Hobby)
**Costo**: USD $5-10/mes (pagas solo lo que usas)
**Specs**: 512 MB RAM, shared CPU, 1 GB storage (Postgres)
**Crédito gratis**: USD $5/mes GRATIS (suficiente para testing)

**Pros**:
- ✅ **MUY BARATO**: Desde $5/mes con uso real
- ✅ Deploy desde GitHub automático
- ✅ PostgreSQL incluido (mismo precio)
- ✅ SSL automático
- ✅ Variables de entorno simples
- ✅ No se duerme (siempre activo)

**Contras**:
- ⚠️ Plan hobby tiene límite de ejecución mensual (500 horas)
- ⚠️ Recursos limitados (OK para <30 clientes)

**Cómo configurar**:
1. Conecta tu repo GitHub: https://railway.app
2. Selecciona "Deploy from GitHub"
3. Railway detecta automáticamente Django (Dockerfile)
4. Agrega PostgreSQL desde "New Service" → Database → PostgreSQL
5. Configura variables de entorno:
```bash
DATABASE_URL=${DATABASE_URL}  # Auto-generada por Railway
SECRET_KEY=tu-secret-key-generada
ALLOWED_HOSTS=plataforma-production.up.railway.app
DEBUG=False
```
6. Deploy automático

**URL**: https://railway.app
**Costo real para la plataforma**: ~USD $5-10/mes con 10-20 clientes

---

#### Opción B: Fly.io (Alternativa barata)

**Plan**: Pay-as-you-go
**Costo**: USD $0-15/mes
**Specs**: 256 MB RAM (gratis), Postgres 1 GB (gratis)
**Crédito gratis**: Máquinas pequeñas GRATIS para siempre

**Pros**:
- ✅ **Tier gratis PERMANENTE** (no expira)
- ✅ 3 máquinas pequeñas gratis (256 MB c/u)
- ✅ 3 GB Postgres gratis
- ✅ Global (múltiples regiones)

**Contras**:
- ⚠️ Más técnico de configurar (usa flyctl CLI)
- ⚠️ 256 MB RAM puede ser poco

**URL**: https://fly.io

---

#### Opción C: Render

**Plan FREE**: USD $0/mes (⚠️ se duerme después de 15 min)
**Plan Starter**: USD $7/mes (512 MB RAM, siempre activo)
**Plan Standard**: USD $25/mes (2 GB RAM)

**Database**:
- **Starter**: USD $7/mes (1 GB storage, 7 días backups)
- **Standard**: USD $15/mes (10 GB storage, 30 días backups)

**Pros**:
- Setup muy simple
- SSL automático
- Deploy desde GitHub

**Contras**:
- Más caro que Railway/Fly.io
- Plan Free se duerme (no apto para producción)

**Recomendación**: Usa Render Starter (USD $7) + Render Postgres Starter (USD $7) = USD $14/mes si quieres simplicidad

---

#### Opción D: PythonAnywhere (Muy específico para Django)

**Plan**: Hacker (USD $5/mes)
**Specs**: 1 web app, 512 MB, MySQL incluido

**Pros**:
- ✅ Muy barato (USD $5/mes)
- ✅ Diseñado específicamente para Django
- ✅ MySQL incluido

**Contras**:
- ⚠️ Requiere PostgreSQL → MySQL migration (mucho trabajo)
- ⚠️ Menos moderno que otras opciones
- ⚠️ No tiene buen soporte para Docker

**Recomendación**: Solo si presupuesto es EXTREMADAMENTE limitado y aceptas migrar a MySQL

---

#### Opción B: DigitalOcean App Platform

**Plan**: Basic
**Costo**: USD $12/mes (app) + $15/mes (DB) = USD $27/mes

**Pros**:
- Más económico que Render
- Servidores en múltiples regiones (incluye Sao Paulo, Brasil - más cerca de Argentina)
- Buena documentación

**Contras**:
- Menos automático que Render
- Requiere más configuración manual

---

#### Opción C: AWS (Solo para producción escalada)

**Plan**: EC2 t3.medium + RDS db.t3.medium
**Costo**: USD $95-130/mes

**Pros**:
- Máximo control y escalabilidad
- Múltiples servicios integrados
- Mejor rendimiento

**Contras**:
- Complejidad alta
- Requiere conocimientos DevOps
- Costo elevado

---

### 2. Base de Datos (PostgreSQL)

Tu aplicación necesita PostgreSQL 15+.

#### Opción A: Render Postgres (Recomendado con Render Backend)

**Plan**: Standard
**Costo**: USD $15/mes
**Specs**: 2 GB RAM, 10 GB storage, backups diarios

**Pros**:
- Integración perfecta con Render
- Backups automáticos (7 días)
- SSL por default

---

#### Opción B: Railway Postgres

**Plan**: Pay-as-you-go
**Costo**: ~USD $10-20/mes (depende de uso)

**Pros**:
- Más flexible en pricing
- Backups incluidos

---

#### Opción C: Supabase (PostgreSQL as a Service)

**Plan**: Pro
**Costo**: USD $25/mes
**Specs**: 8 GB DB, backups diarios, 50 GB bandwidth

**Pros**:
- Dashboard excelente
- Backups automáticos
- Extensiones Postgres avanzadas
- API REST automática

**Contras**:
- Un poco más caro

---

#### Opción D: AWS RDS PostgreSQL (Para alta escala)

**Plan**: db.t3.medium
**Costo**: USD $60-80/mes
**Specs**: 4 GB RAM, Multi-AZ opcional

**Pros**:
- Altamente disponible
- Backups automáticos (35 días)
- Read replicas para escalar lecturas

---

### 3. Redis (Cache + Celery)

Necesario para caché de sesiones y cola de tareas (Celery).

#### Opción A: Upstash Redis (Recomendado para empezar)

**Plan**: Pay-as-you-go (Free tier generoso)
**Costo**: USD $0-10/mes

**Pros**:
- Free tier: 10k comandos/día
- Serverless (no servidor dedicado)
- Global replication

**URL**: https://upstash.com

---

#### Opción B: Render Redis

**Plan**: Standard
**Costo**: USD $10/mes
**Specs**: 512 MB RAM

**Pros**:
- Integrado con Render backend
- Simple configuración

---

#### Opción C: Redis Cloud (Redis Labs)

**Plan**: Fixed
**Costo**: USD $7/mes
**Specs**: 30 MB, 30 conexiones

**Pros**:
- Proveedor oficial de Redis
- Muy confiable

---

### 4. Frontend (React/Vite)

Tu aplicación React compilada en archivos estáticos.

#### Opción A: Vercel (Recomendado)

**Plan**: Hobby (gratis) o Pro (USD $20/mes)
**Límites Free**: 100 GB bandwidth/mes, 100 deployments/mes

**Pros**:
- Deploy automático desde GitHub
- SSL automático
- CDN global incluido
- Preview deployments (testing)
- Excelente DX

**Contras**:
- Free tier tiene límites de bandwidth (suficiente para empezar)

**Cómo configurar**:
1. Conecta tu repo de GitHub
2. Framework: Vite
3. Build command: `npm run build`
4. Output directory: `dist`
5. Deploy!

---

#### Opción B: Netlify

**Plan**: Starter (gratis) o Pro (USD $19/mes)
**Límites Free**: 100 GB bandwidth/mes

**Pros**:
- Similar a Vercel
- Buena integración con GitHub
- Forms y Functions incluidas

---

#### Opción C: Cloudflare Pages

**Plan**: Free
**Límites**: Ilimitado bandwidth, 500 builds/mes

**Pros**:
- Totalmente gratis sin límites de bandwidth
- CDN Cloudflare (super rápido)

**Contras**:
- Menos features que Vercel

---

### 5. Almacenamiento de Archivos (Imágenes)

Fotos de clientes (antes/después), logos, etc.

#### Opción A: Cloudinary (Recomendado para empezar)

**Plan**: Free
**Límites Free**: 25 GB storage, 25 GB bandwidth/mes
**Costo Pro**: USD $89/mes (100 GB storage, 100 GB bandwidth)

**Pros**:
- Free tier generoso
- Transformación de imágenes on-the-fly
- CDN incluido
- Fácil integración con Django

**Instalación**:
```bash
pip install cloudinary
```

**Configuración Django**:
```python
# settings.py
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'tu-cloud-name',
    'API_KEY': 'tu-api-key',
    'API_SECRET': 'tu-api-secret'
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
```

---

#### Opción B: AWS S3 + CloudFront

**Plan**: Standard
**Costo**: USD $5-15/mes (según uso)
**Specs**: 50 GB storage, 500 GB transfer

**Pros**:
- Económico para alto volumen
- Altamente escalable
- CloudFront CDN para servir rápido

**Contras**:
- Más complejo de configurar
- No tiene transformación de imágenes (necesitas thumbnail manual)

**Instalación**:
```bash
pip install django-storages boto3
```

---

### 6. WhatsApp Notifications

Sistema crítico para notificaciones a clientes.

#### Opción A: Twilio (Recomendado)

**Plan**: Pay-as-you-go
**Costo por mensaje**: USD $0.005-0.01 (varía por país)
**Costo estimado**: USD $10-50/mes (100-500 mensajes/mes)

**Límites Free Trial**: USD $15 en créditos gratis

**Pros**:
- Fácil integración
- API excelente
- WhatsApp Business API aprobado
- Soporte para Argentina

**Contras**:
- Requiere número de teléfono validado
- Aprobación de templates de mensajes (tarda 1-2 días)

**Cómo configurar**:
```bash
pip install twilio
```

**Templates de mensajes** (deben aprobarse en Twilio):
1. **Confirmación de turno**: "Hola {{1}}, confirmamos tu turno para {{2}} el {{3}} a las {{4}}."
2. **Recordatorio 24h**: "Hola {{1}}, te recordamos tu turno mañana a las {{2}}."
3. **Recordatorio 2h**: "Hola {{1}}, tu turno es en 2 horas. Te esperamos!"

**Documentación**: https://www.twilio.com/docs/whatsapp

---

#### Opción B: Meta WhatsApp Business API (Directo)

**Plan**: Pay-as-you-go
**Costo**: Similar a Twilio, pero sin intermediario

**Pros**:
- Sin intermediario (costo potencialmente menor)
- Control directo

**Contras**:
- Proceso de aprobación complejo (2-4 semanas)
- Requiere Meta Business Manager
- Más técnico de configurar

**Recomendación**: Empieza con Twilio, migra a Meta API si creces mucho.

---

### 7. Email Transaccional

Para emails de confirmación, recuperación de contraseña, reportes.

#### Opción A: SendGrid (Recomendado)

**Plan**: Free
**Límites Free**: 100 emails/día (3000/mes)
**Plan Essentials**: USD $15/mes (50k emails/mes)

**Pros**:
- Free tier generoso para empezar
- Excelente deliverability
- Dashboard con analytics
- Templates HTML

**Instalación**:
```bash
pip install sendgrid
```

**Configuración Django**:
```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = 'tu-sendgrid-api-key'
DEFAULT_FROM_EMAIL = 'noreply@tuplataforma.com'
```

---

#### Opción B: Mailgun

**Plan**: Foundation (USD $35/mes - 50k emails)

**Pros**:
- Mejor para alto volumen
- Validación de emails

**Contras**:
- Sin plan free

---

#### Opción C: AWS SES

**Plan**: Pay-as-you-go
**Costo**: USD $0.10 por 1000 emails

**Pros**:
- Muy económico para alto volumen
- Integrado con AWS

**Contras**:
- Requiere salir de "sandbox" (proceso de aprobación)

---

### 8. Dominio y SSL

#### Dominio (.com.ar o .com)

**Proveedor**: NIC Argentina (para .com.ar) o Namecheap/GoDaddy (para .com)
**Costo**: USD $10-20/año

**Ejemplos**:
- `tuplataforma.com.ar`
- `gestionestetica.com`

#### SSL (HTTPS)

**Proveedor**: Incluido GRATIS en todos los servicios modernos
- ✅ Render: SSL automático
- ✅ Vercel: SSL automático
- ✅ Cloudflare: SSL gratis

**No necesitas pagar por SSL**.

---

### 9. Monitoring & Error Tracking

#### Opción A: Sentry (Recomendado)

**Plan**: Developer (gratis) o Team (USD $26/mes)
**Límites Free**: 5k eventos/mes

**Pros**:
- Tracking de errores en tiempo real
- Stack traces completos
- Alertas por email/Slack
- Integración con Django y React

**Instalación Backend**:
```bash
pip install sentry-sdk
```

**Configuración**:
```python
# settings.py
import sentry_sdk

sentry_sdk.init(
    dsn="tu-sentry-dsn",
    traces_sample_rate=0.1,
    environment="production",
)
```

---

#### Opción B: LogRocket (Frontend)

**Plan**: Team (USD $99/mes)

**Pros**:
- Session replay (ver lo que hizo el usuario)
- Ideal para debugging frontend

---

### 10. Backups

#### Base de Datos

**Incluido en**:
- ✅ Render Postgres: 7 días de backups automáticos
- ✅ AWS RDS: 35 días configurables
- ✅ Supabase: Backups diarios

**Recomendación adicional**: Exportar backup manual mensual a S3 (script automatizado con Celery).

---

## 💰 Resumen de Costos por Escenario

### Escenario 1: GRATIS - Testing/Validación (0-5 clientes de prueba)

| Servicio | Costo |
|----------|-------|
| Render Free (Backend) | USD $0 |
| Supabase Postgres (Free) | USD $0 |
| Upstash Redis (Free) | USD $0 |
| Vercel (Frontend) | USD $0 |
| Cloudinary | USD $0 |
| Twilio Trial | USD $0 (créditos) |
| SendGrid | USD $0 |
| **TOTAL** | **USD $0/mes** |

**⚠️ Limitaciones**: Backend se duerme, solo para testing

---

### Escenario 2: Ultra Low-Cost (5-20 clientes)

| Servicio | Costo |
|----------|-------|
| Railway (Backend + DB) | USD $5-10 |
| Upstash Redis | USD $0 |
| Vercel (Frontend) | USD $0 |
| Cloudinary | USD $0 |
| Twilio WhatsApp | USD $7-15 |
| SendGrid | USD $0 |
| Dominio | USD $1-2/mes |
| **TOTAL** | **USD $13-27/mes** |

**✅ Recomendado para EMPEZAR con primeros clientes reales**

---

### Escenario 3: Crecimiento (20-50 clientes)

| Servicio | Costo |
|----------|-------|
| Railway Pro (Backend + DB) | USD $20-30 |
| Upstash Redis (Paid) | USD $10 |
| Vercel Pro | USD $20 |
| Cloudinary Free | USD $0 |
| Twilio WhatsApp | USD $30-60 |
| SendGrid Essentials | USD $15 |
| Sentry Team | USD $26 |
| Dominio | USD $2 |
| **TOTAL** | **USD $123-163/mes** |

---

### Escenario 4: Producción (50-150 clientes)

| Servicio | Costo |
|----------|-------|
| DigitalOcean Droplet (4GB) | USD $24 |
| DigitalOcean Managed Postgres | USD $15 |
| Redis Cloud | USD $15 |
| Vercel Pro | USD $20 |
| AWS S3 + CloudFront | USD $15 |
| Twilio WhatsApp | USD $80-150 |
| SendGrid Pro | USD $90 |
| Sentry Team | USD $26 |
| Backups | USD $5 |
| Dominio | USD $2 |
| **TOTAL** | **USD $292-382/mes** |

---

## 🚀 Plan de Deployment Paso a Paso

### Fase 1: Preparación Local (Día 0)

1. ✅ Asegurar que la aplicación corre con Docker Compose
2. ✅ Variables de entorno externalizadas (`.env.example`)
3. ✅ Tests pasando
4. ✅ Migraciones de DB al día

---

### Fase 2: Setup de Servicios (Día 1)

**Mañana (2-3 horas)**:
1. Crear cuenta en Render.com
2. Conectar repositorio GitHub
3. Crear servicio PostgreSQL en Render
4. Crear servicio Redis (Upstash o Render)

**Tarde (2-3 horas)**:
5. Crear Web Service (Backend) en Render
6. Configurar variables de entorno
7. Configurar Cloudinary y agregar credenciales
8. Hacer primer deploy del backend

---

### Fase 3: Frontend Deploy (Día 1-2)

1. Crear cuenta en Vercel
2. Conectar repo GitHub (carpeta `/frontend`)
3. Configurar `VITE_API_URL` apuntando al backend en Render
4. Deploy automático

---

### Fase 4: Dominio y SSL (Día 2)

1. Comprar dominio (ej: `tuplataforma.com.ar`)
2. Configurar DNS en Render:
   - `api.tuplataforma.com.ar` → Backend
3. Configurar DNS en Vercel:
   - `app.tuplataforma.com.ar` → Frontend
4. Esperar propagación DNS (1-24 horas)

---

### Fase 5: Servicios Adicionales (Día 2-3)

1. Configurar Twilio WhatsApp
2. Configurar SendGrid
3. Configurar Sentry
4. Probar todos los flujos end-to-end

---

### Fase 6: Testing en Producción (Día 3-4)

1. Crear usuario admin de prueba
2. Crear centro estético de prueba
3. Probar todos los módulos:
   - [ ] Clientes (CRUD)
   - [ ] Servicios (CRUD)
   - [ ] Turnos (CRUD, notificaciones)
   - [ ] Finanzas (transacciones, categorías)
   - [ ] Mi Caja (ventas)
   - [ ] Inventario (productos)
   - [ ] Analytics (reportes)
4. Probar notificaciones WhatsApp
5. Probar emails

---

### Fase 7: Lanzamiento (Día 5)

1. Habilitar sistema de registro (si está implementado)
2. Comunicar a primeros usuarios
3. Monitorear errores en Sentry
4. Estar disponible para soporte

---

## 📋 Checklist Pre-Deploy

### Backend
- [ ] `DEBUG = False` en producción
- [ ] `ALLOWED_HOSTS` configurado correctamente
- [ ] `SECRET_KEY` generada con secretos seguros
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SECURE_HSTS_SECONDS = 31536000`
- [ ] CORS configurado correctamente
- [ ] Migraciones aplicadas
- [ ] Archivos estáticos configurados (Whitenoise)
- [ ] Celery workers corriendo
- [ ] Celery beat corriendo (tareas programadas)

### Frontend
- [ ] `VITE_API_URL` apunta a producción
- [ ] Build optimizado (`npm run build`)
- [ ] Analytics configurado (si aplica)
- [ ] Error boundaries en componentes críticos

### Base de Datos
- [ ] Backups automáticos habilitados
- [ ] Conexiones SSL habilitadas
- [ ] Usuario de DB con contraseña fuerte
- [ ] Indexes creados en tablas críticas

### Seguridad
- [ ] HTTPS habilitado
- [ ] CORS configurado
- [ ] Rate limiting habilitado
- [ ] Secrets en variables de entorno (no en código)
- [ ] Logs no exponen información sensible

### Monitoreo
- [ ] Sentry configurado y probado
- [ ] Alertas configuradas
- [ ] Dashboard de métricas configurado

---

## 🔐 Variables de Entorno Críticas

```bash
# Backend (.env)
DEBUG=False
SECRET_KEY=tu-secret-key-super-segura-64-caracteres-minimo
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://user:password@host:6379
ALLOWED_HOSTS=api.tuplataforma.com.ar,tuplataforma.com.ar

# Cloudinary
CLOUDINARY_CLOUD_NAME=tu-cloud-name
CLOUDINARY_API_KEY=tu-api-key
CLOUDINARY_API_SECRET=tu-api-secret

# Twilio WhatsApp
TWILIO_ACCOUNT_SID=tu-account-sid
TWILIO_AUTH_TOKEN=tu-auth-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# SendGrid
SENDGRID_API_KEY=tu-sendgrid-api-key

# Sentry
SENTRY_DSN=tu-sentry-dsn

# CORS
CORS_ALLOWED_ORIGINS=https://app.tuplataforma.com.ar,https://tuplataforma.com.ar
```

```bash
# Frontend (.env.production)
VITE_API_URL=https://api.tuplataforma.com.ar/api
```

---

## 🆘 Soporte y Ayuda

### Documentación Oficial

- **Render**: https://render.com/docs
- **Vercel**: https://vercel.com/docs
- **Django Deployment**: https://docs.djangoproject.com/en/4.2/howto/deployment/
- **Docker**: https://docs.docker.com/
- **Twilio WhatsApp**: https://www.twilio.com/docs/whatsapp

### Comunidades

- **Django**: r/django (Reddit)
- **React**: r/reactjs (Reddit)
- **PostgreSQL**: r/PostgreSQL
- **DevOps**: r/devops

---

## 🎓 Recomendaciones Finales

### 🆓 Para VALIDAR el producto (primeros 1-2 meses):
1. ✅ **Render FREE** para backend (se duerme, pero gratis)
2. ✅ **Supabase Free** para PostgreSQL (500 MB)
3. ✅ **Upstash Free** para Redis
4. ✅ **Vercel Free** para frontend
5. ✅ **Cloudinary Free** para imágenes
6. ✅ **Twilio Trial** créditos gratis

**Inversión total**: USD $0/mes

**⚠️ Solo para testing** - Backend tarda en despertar, no apto para clientes reales.

---

### 💰 Para PRIMEROS CLIENTES REALES (1-20 clientes):
1. ✅ **Railway** para backend/DB (USD $5-10/mes) ← **LA MÁS BARATA**
2. ✅ **Upstash Free** para Redis
3. ✅ **Vercel Free** para frontend
4. ✅ **Cloudinary Free** para imágenes
5. ✅ **Twilio** pay-as-you-go (USD $7-15/mes)
6. ✅ **SendGrid Free** para emails

**Inversión total**: USD $13-27/mes ← **RECOMENDADO PARA EMPEZAR**

**Alternativas al mismo precio**:
- **Fly.io**: USD $0-15/mes (más complejo, pero gratis permanente)
- **Render Starter**: USD $14/mes (más simple, un poco más caro)

---

### 📈 Cuando llegues a 20-50 clientes:
1. Upgrade a **Railway Pro** (USD $20/mes)
2. Upgrade a **Vercel Pro** (USD $20/mes)
3. Agrega **Sentry Team** (USD $26/mes) para monitoreo
4. Total: USD $120-160/mes

---

### 🚀 Cuando llegues a 50-100+ clientes:
1. Migra a **DigitalOcean** o **AWS**
2. Implementa **load balancers**
3. Agrega **read replicas** en DB
4. Considera **multi-región**
5. Total: USD $250-400/mes

---

## 📞 Próximos Pasos

1. **Decide tu escenario**: MVP, Crecimiento, o Producción
2. **Crea cuentas** en los servicios seleccionados
3. **Sigue el plan de deployment** paso a paso
4. **Prueba exhaustivamente** antes de dar acceso a usuarios
5. **Monitorea constantemente** las primeras semanas

**¿Necesitas ayuda con el deployment?** Puedo guiarte paso a paso en la configuración de cualquiera de estos servicios.

---

## 📘 ANEXO: Guía Rápida de Deployment con Railway (La Más Barata)

### Paso 1: Preparar el Proyecto

**1.1 Crear `railway.json` en la raíz del proyecto**:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "backend/Dockerfile"
  },
  "deploy": {
    "startCommand": "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT",
    "healthcheckPath": "/api/health/",
    "healthcheckTimeout": 100
  }
}
```

**1.2 Asegurar que el Dockerfile existe** (`backend/Dockerfile`):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Colectar archivos estáticos
RUN python manage.py collectstatic --noinput

# Puerto
EXPOSE 8000

# Comando por defecto
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

---

### Paso 2: Deploy en Railway (15 minutos)

**2.1 Crear cuenta**:
1. Ve a https://railway.app
2. Sign up con GitHub (gratis)
3. Autoriza acceso a tus repos

**2.2 Crear nuevo proyecto**:
1. Click "New Project"
2. Selecciona "Deploy from GitHub repo"
3. Elige tu repositorio `Plataforma-Estetica`
4. Railway detecta el Dockerfile automáticamente

**2.3 Agregar PostgreSQL**:
1. En el proyecto, click "New" → "Database" → "Add PostgreSQL"
2. Railway crea automáticamente la variable `DATABASE_URL`

**2.4 Agregar variables de entorno**:
En el servicio del backend, agrega:
```bash
DEBUG=False
SECRET_KEY=genera-una-clave-super-segura-de-50-caracteres-random
ALLOWED_HOSTS=*.up.railway.app
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=redis://default:password@containers-us-west-123.railway.app:6379
CORS_ALLOWED_ORIGINS=https://tu-frontend.vercel.app
```

**2.5 Deploy**:
- Railway hace deploy automáticamente
- Espera 3-5 minutos
- URL: `https://plataforma-production.up.railway.app`

---

### Paso 3: Frontend en Vercel (5 minutos)

**3.1 Crear cuenta**:
1. Ve a https://vercel.com
2. Sign up con GitHub (gratis)

**3.2 Deploy**:
1. Click "New Project"
2. Importa tu repo
3. Configure:
   - Framework: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
4. Variables de entorno:
```bash
VITE_API_URL=https://plataforma-production.up.railway.app/api
```
5. Deploy (tarda 2-3 min)

---

### Paso 4: Configurar Dominio (Opcional)

**4.1 Comprar dominio** (USD $10-15/año):
- NIC Argentina: https://nic.ar (para .com.ar)
- Namecheap: https://namecheap.com (para .com)

**4.2 Configurar DNS**:

**Para Backend (Railway)**:
1. En Railway → Settings → Domains
2. Click "Generate Domain" o "Custom Domain"
3. Si usas custom: agrega CNAME record:
```
api.tudominio.com → CNAME → plataforma-production.up.railway.app
```

**Para Frontend (Vercel)**:
1. En Vercel → Settings → Domains
2. Add domain: `app.tudominio.com`
3. Agrega CNAME record:
```
app.tudominio.com → CNAME → cname.vercel-dns.com
```

---

### Paso 5: Servicios Complementarios

**5.1 Cloudinary (Imágenes)**:
1. Signup: https://cloudinary.com (Free tier)
2. Obtén credenciales del Dashboard
3. Agrega a Railway:
```bash
CLOUDINARY_CLOUD_NAME=tu-cloud-name
CLOUDINARY_API_KEY=tu-api-key
CLOUDINARY_API_SECRET=tu-api-secret
```

**5.2 Twilio (WhatsApp)**:
1. Signup: https://twilio.com
2. Obtén créditos gratis (USD $15)
3. Configura WhatsApp Sandbox
4. Agrega a Railway:
```bash
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=tu-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

**5.3 SendGrid (Email)**:
1. Signup: https://sendgrid.com (Free: 100 emails/día)
2. Crea API Key
3. Agrega a Railway:
```bash
SENDGRID_API_KEY=SG.xxxx
```

---

### Paso 6: Verificar Deployment

**6.1 Checklist**:
- [ ] Backend responde en `https://tu-app.up.railway.app/api/health/`
- [ ] Frontend carga en `https://tu-app.vercel.app`
- [ ] Login funciona
- [ ] Crear centro de prueba funciona
- [ ] Imágenes se suben correctamente (Cloudinary)
- [ ] Notificaciones WhatsApp funcionan (Twilio)

**6.2 Comandos útiles**:
```bash
# Ver logs en Railway (desde CLI)
railway logs

# Correr migraciones
railway run python manage.py migrate

# Crear superuser
railway run python manage.py createsuperuser
```

---

### Costo Total: USD $5-10/mes

| Servicio | Costo |
|----------|-------|
| Railway (Backend + DB) | USD $5-10 |
| Vercel (Frontend) | USD $0 |
| Cloudinary | USD $0 |
| Upstash Redis | USD $0 |
| Twilio (100 msgs/mes) | USD $7 |
| SendGrid | USD $0 |
| **TOTAL** | **USD $12-17/mes** |

---

**Última actualización**: Enero 2026
**Versión**: 2.0 (Actualizado con opciones más baratas)
