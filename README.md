# Plataforma de Gestión para Centros de Estética

Plataforma SaaS integral para la gestión completa de centros de estética y spa. Centraliza todas las operaciones críticas: gestión de clientes, agendamiento de turnos, control de inventario, finanzas, analytics y comunicación automatizada.

## Características Principales

- **Gestión de Clientes (CRM)**: Base de datos completa con historial de servicios, fotos antes/después, preferencias y analytics
- **Sistema de Turnos**: Agenda inteligente con prevención de double-booking, múltiples vistas y recordatorios automatizados
- **Gestión de Inventario**: Control de stock con alertas automáticas y seguimiento de productos
- **Sistema Financiero**: Control completo de ingresos, gastos y reportes en tiempo real
- **Analytics**: Dashboards interactivos para toma de decisiones basada en datos
- **Notificaciones WhatsApp**: Integración para recordatorios y comunicación automatizada
- **Gestión de Empleados**: Sistema de comisiones y seguimiento de performance
- **Multi-sucursal**: Soporte para centros con múltiples locaciones

## Stack Tecnológico

### Backend
- Python 3.11+ / Django 4.2+
- Django REST Framework
- PostgreSQL 15+
- Redis (caché y broker para Celery)
- Celery (tareas asíncronas)

### Frontend
- React 18+ with TypeScript
- Vite
- TailwindCSS
- React Router
- Zustand (state management)
- React Query

### Infrastructure
- Docker & Docker Compose
- Render (hosting inicial)
- AWS/DigitalOcean (escalado)

## Prerequisitos

- Docker Desktop instalado
- Git

## Instalación y Setup

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/Plataforma-Estetica.git
cd Plataforma-Estetica
```

### 2. Configurar variables de entorno

```bash
# Backend
cp .env.example .env
# Edita el archivo .env con tus configuraciones

# Frontend
cd frontend
cp .env.example .env
cd ..
```

### 3. Levantar el proyecto con Docker

```bash
# Construir y levantar todos los servicios
docker-compose up --build

# O en segundo plano
docker-compose up -d
```

Esto levantará:
- PostgreSQL (puerto 5432)
- Redis (puerto 6379)
- Backend Django (puerto 8000)
- Celery Worker
- Celery Beat
- Frontend React (puerto 5173)

### 4. Ejecutar migraciones iniciales

```bash
# En una nueva terminal
docker-compose exec backend python manage.py migrate
```

### 5. Crear un superusuario

```bash
docker-compose exec backend python manage.py createsuperuser
```

### 6. Acceder a la aplicación

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api
- **Admin Django**: http://localhost:8000/admin
- **API Docs (Swagger)**: http://localhost:8000/api/docs/
- **API Docs (ReDoc)**: http://localhost:8000/api/redoc/

## Desarrollo Local (sin Docker)

### Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar PostgreSQL y Redis localmente
# Editar DATABASE_URL y REDIS_URL en .env

# Migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```

### Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Ejecutar servidor de desarrollo
npm run dev
```

## Comandos Útiles

### Docker

```bash
# Ver logs
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f backend

# Detener servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v

# Ejecutar comando en contenedor
docker-compose exec backend python manage.py shell
```

### Django

```bash
# Crear nueva migración
docker-compose exec backend python manage.py makemigrations

# Aplicar migraciones
docker-compose exec backend python manage.py migrate

# Crear superusuario
docker-compose exec backend python manage.py createsuperuser

# Acceder a shell de Django
docker-compose exec backend python manage.py shell

# Ejecutar tests
docker-compose exec backend pytest
```

### Celery

```bash
# Ver workers activos
docker-compose exec celery celery -A config inspect active

# Ver tareas programadas
docker-compose exec celery-beat celery -A config inspect scheduled
```

## Estructura del Proyecto

```
Plataforma-Estetica/
├── backend/
│   ├── config/              # Configuración de Django
│   ├── apps/
│   │   ├── clientes/        # Gestión de clientes (CRM)
│   │   ├── turnos/          # Sistema de turnos y agenda
│   │   ├── servicios/       # Catálogo de servicios
│   │   ├── inventario/      # Gestión de inventario
│   │   ├── finanzas/        # Sistema financiero
│   │   ├── empleados/       # Gestión de empleados y comisiones
│   │   ├── notificaciones/  # WhatsApp integration
│   │   └── analytics/       # Reportes y analytics
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/      # Componentes React reutilizables
│   │   ├── pages/           # Páginas principales
│   │   ├── services/        # Servicios API
│   │   ├── stores/          # Zustand stores
│   │   └── utils/           # Funciones utilitarias
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── CLAUDE.md               # Guía para Claude Code
└── README.md
```

## Fases de Desarrollo

### Fase 1: MVP (3-4 semanas) ✅ En progreso
- Sistema de autenticación básico
- CRUD de clientes
- CRUD de servicios
- Sistema de turnos con prevención de double-booking
- Agenda visual
- Estados básicos de turno
- Frontend responsivo
- Deploy en Render

### Fase 2: Features Core (4-6 semanas)
- Multi-tenancy completo
- Sistema de roles y permisos granular
- Inventario completo con alertas
- WhatsApp integration
- Sistema de comisiones
- Gestión financiera completa
- Analytics básicos con gráficos
- Múltiples sucursales
- S3/Cloudinary para imágenes

### Fase 3: Polish & Escala (2-4 semanas)
- Optimización de queries y performance
- Testing completo
- UI/UX refinements y animaciones
- Dashboards avanzados
- Reportes exportables (PDF, Excel)
- Monitoring y alertas
- Documentación completa
- Migración a AWS/DigitalOcean

## API Endpoints

La API REST completa está disponible en:
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/

### Autenticación

```bash
# Login
POST /api/auth/login/
{
  "username": "usuario",
  "password": "contraseña"
}

# Refresh token
POST /api/auth/refresh/
{
  "refresh": "refresh_token"
}
```

## Seguridad

- Autenticación JWT con tokens de acceso y refresh
- Passwords encriptados con bcrypt
- HTTPS en producción
- CORS configurado
- Rate limiting para prevenir ataques de fuerza bruta
- SQL Injection protegido mediante Django ORM
- XSS Prevention mediante sanitización de inputs
- Audit logs para acciones críticas

## Testing

```bash
# Backend
docker-compose exec backend pytest

# Con coverage
docker-compose exec backend pytest --cov=apps

# Frontend
cd frontend
npm test
```

## Deployment

Ver documentación detallada en [CLAUDE.md](./CLAUDE.md)

## Licencia

MIT License - ver [LICENSE](./LICENSE)

## Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Soporte

Para preguntas y soporte, por favor abre un issue en GitHub.

---

**Plataforma Estética** - Gestión integral para centros de estética © 2025
