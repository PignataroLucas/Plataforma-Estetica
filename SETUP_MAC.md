# Setup en macOS - Plataforma de Gestión Estética

Guía rápida para levantar la plataforma en macOS.

---

## 📋 Requisitos Previos

Instala estas herramientas (si no las tienes):

```bash
# Homebrew (gestor de paquetes para Mac)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Docker Desktop para Mac
brew install --cask docker

# Git (si no lo tienes)
brew install git

# Node.js y npm
brew install node
```

Verifica las versiones:
```bash
docker --version          # Debe ser 20.x o superior
docker-compose --version  # Debe ser 2.x o superior
node --version           # Debe ser 18.x o superior
npm --version            # Debe ser 9.x o superior
```

---

## 🚀 Instalación Rápida

### 1. Clonar el repositorio

```bash
cd ~/Documents
git clone https://github.com/tu-usuario/Plataforma-Estetica.git
cd Plataforma-Estetica
```

### 2. Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar con nano, vim o VSCode
nano .env
```

**Variables mínimas requeridas:**
```env
# Base de datos
POSTGRES_DB=estetica_db
POSTGRES_USER=estetica_user
POSTGRES_PASSWORD=tu_password_seguro
DATABASE_URL=postgresql://estetica_user:tu_password_seguro@db:5432/estetica_db

# Django
SECRET_KEY=tu-secret-key-super-largo-y-aleatorio-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Twilio (opcional - dejar vacío si no usas WhatsApp todavía)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=
```

### 3. Levantar con Docker

```bash
# Construir y levantar todos los servicios
docker-compose up --build -d

# Ver logs en tiempo real (opcional)
docker-compose logs -f
```

**Esto levanta:**
- ✅ PostgreSQL (base de datos)
- ✅ Redis (caché)
- ✅ Backend Django (API)
- ✅ Frontend React (Admin App)
- ✅ Celery Worker (tareas async)
- ✅ Celery Beat (tareas programadas)

### 4. Crear base de datos inicial

```bash
# Correr migraciones
docker-compose exec backend python manage.py migrate

# Crear superusuario
docker-compose exec backend python manage.py createsuperuser
```

Ingresa:
- Username: `admin`
- Email: `admin@tucentro.com`
- Password: `admin123` (cambiar en producción)

### 5. Cargar datos de prueba (opcional)

```bash
# Crear centro de estética y datos iniciales
docker-compose exec backend python manage.py shell

# Dentro del shell Python:
from apps.clientes.models import CentroEstetica, Sucursal

centro = CentroEstetica.objects.create(
    nombre="Mi Centro de Estética",
    email="info@micentro.com",
    telefono="+541112345678"
)

sucursal = Sucursal.objects.create(
    centro_estetica=centro,
    nombre="Sucursal Principal",
    direccion="Av. Corrientes 1234, CABA",
    telefono="+541112345678",
    email="principal@micentro.com"
)

print(f"✅ Centro creado: {centro.nombre}")
print(f"✅ Sucursal creada: {sucursal.nombre}")

# Salir del shell
exit()
```

---

## 🌐 Acceso a la Plataforma

Una vez levantado, accede a:

- **Admin App (Frontend)**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Admin Django**: http://localhost:8000/admin

**Credenciales:**
- Usuario: `admin`
- Password: el que creaste en el paso 4

---

## 🛠️ Comandos Útiles

### Gestión de servicios

```bash
# Ver estado de todos los servicios
docker-compose ps

# Ver logs de un servicio específico
docker-compose logs backend
docker-compose logs frontend
docker-compose logs celery

# Reiniciar un servicio
docker-compose restart backend

# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (⚠️ BORRA LA BASE DE DATOS)
docker-compose down -v
```

### Backend (Django)

```bash
# Ejecutar comandos de Django
docker-compose exec backend python manage.py <comando>

# Ejemplos:
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py shell

# Acceder a la consola del contenedor
docker-compose exec backend bash
```

### Frontend (React)

```bash
# Instalar dependencias (si agregas nuevas)
docker-compose exec frontend npm install

# Ver logs del frontend
docker-compose logs -f frontend

# Reconstruir el frontend
docker-compose up --build frontend
```

### Base de datos

```bash
# Acceder a PostgreSQL
docker-compose exec db psql -U estetica_user -d estetica_db

# Crear backup
docker-compose exec db pg_dump -U estetica_user estetica_db > backup.sql

# Restaurar backup
docker-compose exec -T db psql -U estetica_user -d estetica_db < backup.sql
```

---

## 🔧 Troubleshooting

### Error: "Port already in use"

Si el puerto 5173, 8000 o 5432 está ocupado:

```bash
# Ver qué proceso usa el puerto
lsof -i :5173
lsof -i :8000
lsof -i :5432

# Matar el proceso
kill -9 <PID>

# O cambiar el puerto en docker-compose.yml
```

### Error: "Cannot connect to Docker daemon"

```bash
# Asegúrate que Docker Desktop está corriendo
open -a Docker

# Espera a que aparezca el ícono de Docker en la barra superior
```

### Error: "Module not found" en backend

```bash
# Reinstalar dependencias
docker-compose exec backend pip install -r requirements.txt

# O reconstruir el contenedor
docker-compose up --build backend
```

### Error: Frontend no carga

```bash
# Limpiar caché y reinstalar
docker-compose exec frontend rm -rf node_modules
docker-compose exec frontend npm install
docker-compose restart frontend
```

### Base de datos no inicializa

```bash
# Detener todo
docker-compose down

# Eliminar volumen de DB (⚠️ BORRA DATOS)
docker volume rm plataforma-estetica_postgres_data

# Levantar de nuevo
docker-compose up --build -d
docker-compose exec backend python manage.py migrate
```

---

## 🧪 Verificación de Setup

Ejecuta este script para verificar que todo funciona:

```bash
#!/bin/bash

echo "🔍 Verificando servicios..."

# Backend
if curl -s http://localhost:8000/admin/ > /dev/null; then
    echo "✅ Backend funcionando"
else
    echo "❌ Backend no responde"
fi

# Frontend
if curl -s http://localhost:5173 > /dev/null; then
    echo "✅ Frontend funcionando"
else
    echo "❌ Frontend no responde"
fi

# Base de datos
if docker-compose exec -T db psql -U estetica_user -d estetica_db -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Base de datos funcionando"
else
    echo "❌ Base de datos no responde"
fi

# Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis funcionando"
else
    echo "❌ Redis no responde"
fi

echo ""
echo "🎉 Verificación completada"
```

Guarda como `check-setup.sh`, dale permisos y ejecútalo:

```bash
chmod +x check-setup.sh
./check-setup.sh
```

---

## 📱 Próximos Pasos

Una vez que todo funciona:

1. ✅ Explora el **Admin Panel**: http://localhost:5173
2. ✅ Crea servicios, clientes, empleados
3. ✅ Prueba el calendario de turnos
4. ✅ Revisa el módulo de Finanzas
5. ✅ Configura Twilio para WhatsApp (opcional)

---

## 🆘 Ayuda

- **Documentación completa**: Ver `CLAUDE.md` y `README.md`
- **Problemas con Docker**: https://docs.docker.com/desktop/troubleshoot/
- **Issues del proyecto**: https://github.com/tu-usuario/Plataforma-Estetica/issues

---

**Última actualización**: 22 de Noviembre 2025
