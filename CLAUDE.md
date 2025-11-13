# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Plataforma de Gestión para Centros de Estética** - A comprehensive SaaS platform for managing aesthetic centers and spas in Argentina and Latin America.

- **Business Model**: Multi-tenant SaaS platform where each aesthetic center operates independently with logically separated data
- **License**: MIT
- **Version**: 1.0 (November 2025)

## Core Value Proposition

Centralizes all operations for aesthetic centers that currently use disconnected tools (Excel, paper agendas, WhatsApp, basic invoicing). Reduces manual work by 60%, decreases no-shows by 40%, and provides data-driven insights for business decisions.

## Technology Stack

### Backend
- **Python 3.11+** with **Django 4.2+**
- **Django REST Framework** for RESTful API
- **PostgreSQL 15+** for transactional data (ACID compliance, complex queries)
- **Redis 7+** for caching sessions and frequent queries
- **Celery** with Redis broker for asynchronous tasks (notifications, reports)

### Frontend
- **React 18+** (Single Page Application)
- **React Spring** for smooth animations
- **Axios** for API communication
- **Zustand** or Context API for state management

### Infrastructure
- **Docker** + **Docker Compose** for containerization
- **Render** for initial hosting (MVP/early production)
- **AWS/DigitalOcean** for scaled deployment
- **S3/Cloudinary** for multimedia storage (before/after photos)
- **Sentry** for error tracking and monitoring

### Integrations
- **WhatsApp Business API** or **Twilio** for automated notifications
- **Google Analytics** for usage tracking
- Future: Stripe/MercadoPago for payments, AFIP for invoicing (Argentina)

## Architecture

**Three-tier architecture** with clear separation:
1. **Frontend (Client)**: React SPA
2. **Backend (Server)**: Django REST API
3. **Database**: PostgreSQL + Redis cache

**Multi-tenancy**: All entities include `tenant_id` (centro_estetica_id) for data isolation between clients.

## Database Schema

### Core Models

- **CentroEstetica**: Main tenant entity (each center is logically separated)
- **Sucursal**: Multiple locations per center (FK → CentroEstetica)
- **Usuario**: Authentication, roles, permissions (FK → Sucursal)
- **Cliente**: Customer data, contact info, preferences (FK → CentroEstetica)
- **Servicio**: Service catalog (name, duration, price) (FK → Sucursal)
- **Turno**: Appointments (FKs → Cliente, Servicio, Usuario[professional], Sucursal)
  - States: Confirmado, Pendiente, Completado, Cancelado, No-Show
  - Payment states: Pagado, Con Seña, Pendiente
- **Producto**: Inventory (stock, prices, categories) (FK → Sucursal)
- **Transaccion**: Financial records (income/expenses, categories) (FK → Sucursal)
- **Comision**: Commission tracking (FK → Usuario, Turno/Producto)
- **HistorialCliente**: Service history log (FK → Cliente, Servicio)
- **Notificacion**: WhatsApp message log (status, timestamps)

**Critical Indexes**: centro_estetica_id, sucursal_id, fecha_turno, cliente_id for query optimization.

## Key Features by Module

### 1. CRM (Client Management)
- Complete customer profiles with contact info, service history, before/after photos
- Notes, preferences, allergies, contraindications
- Client analytics: spending patterns, visit frequency, favorite services
- Advanced search with multiple filters

### 2. Appointment System
- Visual calendar (day/week/month views) with drag & drop
- **Double-booking prevention** using atomic transactions
- Service-specific durations with automatic availability calculation
- Resource assignment (professionals, equipment/machines)
- Appointment states and payment tracking
- Color-coded by service type

### 3. Inventory Management
- Product catalog with SKU/barcode, suppliers
- Stock control with min/max thresholds
- Automatic low-stock alerts
- Cost/price tracking with automatic margin calculation
- Movement history (entries, exits, adjustments)
- Rotation reports

### 4. Financial System (Admin-only access)
- Income tracking (services, product sales, other)
- Expense categorization (salaries, rent, supplies, services, marketing)
- Cash flow in real-time (income - expenses)
- Monthly profit calculations
- Projections based on historical trends
- Period comparisons (month-to-month, year-to-year)
- PDF and Excel export

### 5. Analytics & Reports
- Service and product sales analysis
- Employee performance tracking (revenue generated, services completed)
- Client analysis (frequency, lifetime value, retention rate)
- Occupancy percentage and peak hours
- No-show analysis by time, service, client
- Profitability analysis per service
- Seasonal trends and forecasting
- Customizable dashboards by role

### 6. Notifications (WhatsApp Integration)
- Appointment confirmation (immediate upon booking)
- Automatic reminders (24h and 2h before - configurable)
- Modification/cancellation notifications
- Post-treatment follow-up messages
- Targeted promotions
- Customizable message templates
- Communication history log
- Opt-out system

### 7. Employee & Commission Management
- Employee profiles (info, role, schedules, specialties)
- Flexible commission system (% per service, fixed amount, tiered)
- Real-time commission calculation per service/product sold
- Commission reports by employee, period, service type
- Historical commission records
- Monthly targets and performance dashboards
- Work schedule tracking

### 8. Multi-branch Support
- Multiple locations per center
- Independent inventory per branch
- Branch-specific calendars and employees
- Consolidated reports (all branches) for owners
- Individual branch analysis
- Inter-branch stock transfers
- Centralized configuration with branch-level customization

## Role-Based Access Control (RBAC)

### Empleado Básico (Therapist/Esthetician)
- View own schedule
- Book appointments
- View clients
- Register completed services
- View own commissions

### Manager (Branch Manager)
- All Empleado permissions +
- View complete branch schedule
- Manage branch employees
- View inventory and alerts
- Branch-specific reports
- Approve cancellations

### Administrador/Dueño (Owner)
- Full access to all features
- Complete financial management
- System configuration
- Consolidated multi-branch reports
- Strategic analytics

**Security Features**: Optional 2FA, audit logs for critical actions, session timeout, encrypted sensitive data, granular configurable permissions.

## Development Phases

### Phase 1: MVP (3-4 weeks)
- Basic authentication (login/logout)
- Client CRUD
- Service CRUD
- Appointment system with double-booking prevention
- Visual calendar (day/week views)
- Basic appointment states (confirmed/cancelled)
- Responsive React frontend
- Deploy to Render

### Phase 2: Core Features (4-6 weeks)
- Complete multi-tenancy (django-tenants)
- Granular role and permission system
- Full inventory with alerts
- WhatsApp integration (Twilio/Meta)
- Commission system
- Financial management (income/expenses)
- Basic analytics with charts (Chart.js)
- Multi-branch support
- Celery for async tasks
- S3/Cloudinary for images

### Phase 3: Polish & Scale (2-4 weeks)
- Query and performance optimization
- Complete testing (pytest, Jest)
- UI/UX refinements and animations (React Spring)
- Advanced dashboards with multiple metrics
- Exportable reports (PDF, Excel)
- In-app notification system
- Monitoring and alerts (Sentry)
- API documentation
- Client onboarding process
- Migration to AWS/DigitalOcean if needed

## Common Development Commands

### Backend (Django)
```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run tests
pytest

# Start Celery worker
celery -A config worker -l info

# Start Celery beat (for scheduled tasks)
celery -A config beat -l info
```

### Frontend (React)
```bash
# Install dependencies
npm install

# Run development server
npm start

# Run tests
npm test

# Build for production
npm run build

# Lint code
npm run lint
```

### Docker
```bash
# Build and start all services
docker-compose up --build

# Start services in background
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Run migrations in container
docker-compose exec backend python manage.py migrate
```

## Security Considerations

- **Authentication**: JWT tokens with expiration and refresh tokens
- **Encryption**: bcrypt for passwords, encrypted sensitive fields in DB
- **HTTPS**: All traffic encrypted with SSL/TLS
- **CORS**: Restrictive Cross-Origin Resource Sharing configuration
- **Rate Limiting**: Brute-force attack prevention
- **SQL Injection**: Protected via Django ORM
- **XSS Prevention**: Input sanitization on frontend and backend
- **Audit Logs**: Critical actions logged (financial access, permission changes)
- **Automatic Backups**: Daily database backups with 30-day retention
- **GDPR Compliance**: Right to erasure, data export, consent management

## Scalability Strategy

### Database
- Read replicas for heavy analytics queries
- Table partitioning for large tables (turnos, transacciones) by date
- Optimized indexes on frequently queried columns
- Connection pooling
- Archiving historical data (>2 years)

### Application
- Stateless architecture allows multiple backend instances
- Load balancer (AWS ALB, Nginx) for traffic distribution
- Distributed Redis cache shared between instances
- CDN for frontend static assets
- Independently scalable Celery workers
- Optional microservices for specific modules (analytics, notifications)

### Capacity Projection
- Initial Render setup: comfortably handles 100+ centers (1000+ active users)
- For 500+ centers: migrate to AWS with multiple instances and additional optimizations

## Project Structure (To Be Created)

```
backend/
  ├── config/           # Django project settings
  ├── apps/
  │   ├── clientes/     # Customer management
  │   ├── turnos/       # Appointment system
  │   ├── servicios/    # Service catalog
  │   ├── inventario/   # Product inventory
  │   ├── finanzas/     # Financial system
  │   ├── empleados/    # Employee & commission management
  │   ├── notificaciones/ # WhatsApp integration
  │   └── analytics/    # Reports and analytics
  ├── manage.py
  └── requirements.txt

frontend/
  ├── src/
  │   ├── components/   # Reusable React components
  │   ├── pages/        # Main application pages
  │   ├── services/     # API communication layer
  │   ├── hooks/        # Custom React hooks
  │   ├── utils/        # Utility functions
  │   └── App.js
  ├── public/
  └── package.json

docker-compose.yml
.env.example
README.md
```

## Important Notes

- **Double-booking prevention is critical**: Use database-level locking or atomic transactions when creating appointments
- **Multi-tenancy isolation**: Every query must filter by centro_estetica_id to prevent data leaks between clients
- **WhatsApp rate limits**: Implement proper queuing and retry logic for message sending
- **Financial data access**: Strictly enforce role-based access - only Admin/Owner roles
- **Image storage**: Use cloud storage (S3/Cloudinary) from the start, not local filesystem
- **Time zones**: Handle properly for multi-region deployments (use UTC in DB, convert in frontend)
- **Commission calculations**: Must be transactional and auditable - no manual adjustments without logs
