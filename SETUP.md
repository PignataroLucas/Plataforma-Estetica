# Setup Rápido con Docker

Guía simple para levantar la plataforma completa (backend + frontend) usando Docker.

## Prerequisitos

- Docker Desktop instalado y corriendo
- Git

## Pasos

### 1. Clonar el repositorio (si aún no lo tienes)

```bash
git clone https://github.com/tu-usuario/Plataforma-Estetica.git
cd Plataforma-Estetica
```

### 2. Levantar todos los servicios

```bash
docker-compose up --build
```

Esto levantará automáticamente:
- PostgreSQL (base de datos)
- Redis (caché)
- Backend Django (API)
- Frontend React (interfaz)
- Celery Worker (tareas asíncronas)
- Celery Beat (tareas programadas)

**Espera** a que todos los servicios estén corriendo (verás logs en la consola).

### 3. Ejecutar las migraciones de la base de datos

Abre **otra terminal** y ejecuta:

```bash
docker-compose exec backend python manage.py migrate
```

### 4. Crear un usuario administrador

```bash
docker-compose exec backend python manage.py createsuperuser
```

Ingresa:
- Usuario
- Email
- Contraseña

### 5. Acceder a la aplicación

- **Frontend (Aplicación principal)**: http://localhost:5173
- **Backend API**: http://localhost:8000/api
- **Admin Django**: http://localhost:8000/admin

## Comandos Útiles

### Detener todos los servicios

```bash
docker-compose down
```

### Ver logs en tiempo real

```bash
# Todos los servicios
docker-compose logs -f

# Solo backend
docker-compose logs -f backend

# Solo frontend
docker-compose logs -f frontend
```

### Reiniciar un servicio específico

```bash
docker-compose restart backend
docker-compose restart frontend
```

### Ejecutar comandos dentro del contenedor

```bash
# Acceder a shell de Django
docker-compose exec backend python manage.py shell

# Crear nuevas migraciones
docker-compose exec backend python manage.py makemigrations

# Ejecutar tests
docker-compose exec backend pytest
```

## Solución de Problemas Comunes

### Error de conexión a la base de datos

```bash
# Reiniciar el servicio de base de datos
docker-compose restart db

# Verificar que PostgreSQL esté corriendo
docker-compose ps
```

### El frontend no carga

```bash
# Reconstruir el contenedor del frontend
docker-compose up --build frontend
```

### Limpiar todo y empezar de cero

```bash
# CUIDADO: Esto eliminará todos los datos
docker-compose down -v
docker-compose up --build
```

Luego vuelve a ejecutar las migraciones (paso 3) y crear el superusuario (paso 4).

## Estructura de Servicios

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| frontend | 5173 | Interfaz React |
| backend | 8000 | API Django REST |
| db | 5432 | PostgreSQL |
| redis | 6379 | Caché y broker de Celery |
| celery | - | Worker para tareas asíncronas |
| celery-beat | - | Programador de tareas |

---

Para más detalles técnicos, ver [README.md](./README.md)
