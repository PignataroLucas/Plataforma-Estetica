# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

### Essential Commands
```bash
# Start development environment
docker-compose up

# Run database migrations
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate

# Access Django shell
docker-compose exec backend python manage.py shell

# Run tests
docker-compose exec backend pytest

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Project Access
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api
- Django Admin: http://localhost:8000/admin
- API Docs (Swagger): http://localhost:8000/api/docs/
- API Docs (ReDoc): http://localhost:8000/api/redoc/

### Key File Locations
- **Backend Entry**: `backend/manage.py`
- **Backend Settings**: `backend/config/settings.py`
- **API Routes**: `backend/config/urls.py`
- **Frontend Entry**: `frontend/src/App.tsx`
- **API Client**: `frontend/src/services/api.ts`
- **Type Definitions**: `frontend/src/types/models.ts`

### Django Apps (Backend Modules)
- `apps/empleados/` - Users, auth, centers, branches, employees, roles
- `apps/clientes/` - Customer/client management (CRM)
- `apps/servicios/` - Services catalog, rented equipment, rental scheduling
- `apps/turnos/` - Appointment system and calendar
- `apps/inventario/` - Product inventory and stock management
- `apps/finanzas/` - Financial system (transactions, categories, offers)
- `apps/mi_caja/` - Point of sale system for employees
- `apps/notificaciones/` - WhatsApp notifications
- `apps/analytics/` - Reports and analytics

## Project Overview

**Plataforma de Gestión para Centros de Estética** - A comprehensive SaaS platform for managing aesthetic centers and spas in Argentina and Latin America.

- **Business Model**: Multi-tenant SaaS platform where each aesthetic center operates independently with logically separated data
- **License**: MIT
- **Version**: 1.0 (November 2025)
- **Current Status**: Phase 2+ completed with advanced financial system, rented equipment management, automatic transaction generation, and sales/offers system

### Key Differentiators
- **Automatic Financial Tracking**: Transactions auto-generated from appointments, product sales, and equipment rentals
- **Rented Equipment Management**: Complete workflow for managing daily equipment rentals with smart expense generation
- **Hierarchical Category System**: 2-level category structure with protected system categories
- **Reconciliation System**: Automatic detection and alerts for appointments without confirmed rentals
- **Salary Processing**: Bulk salary payment system with automatic expense creation
- **Real-time Profit Analysis**: Consider all costs including equipment rentals across daily appointments

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
- **React 18+ with TypeScript** (Single Page Application)
- **React Spring** for smooth animations
- **Axios** for API communication
- **Zustand** for state management

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
1. **Frontend (Client)**: React SPA with TypeScript
2. **Backend (Server)**: Django REST API
3. **Database**: PostgreSQL + Redis cache

**Multi-tenancy**: All entities include `tenant_id` (centro_estetica_id) for data isolation between clients.

### Backend Architecture Patterns

**Django App Structure:**
Each Django app follows this pattern:
```
apps/<app_name>/
├── models.py           # Database models (Django ORM)
├── serializers.py      # DRF serializers for API request/response
├── views.py            # ViewSets and APIViews for endpoints
├── urls.py             # URL routing for the app
├── admin.py            # Django admin configuration
├── signals.py          # Django signals (e.g., auto-generate transactions)
├── tasks.py            # Celery async tasks (if needed)
├── tests/              # Pytest test files
│   ├── test_models.py
│   ├── test_views.py
│   └── test_serializers.py
└── migrations/         # Database migration files
```

**Key Backend Patterns:**
- **ViewSets over APIViews**: Use `ModelViewSet` for standard CRUD, custom actions with `@action` decorator
- **Serializer Composition**: Nested serializers for related data (e.g., `TurnoSerializer` includes `ClienteSerializer`)
- **Signal-based Automation**: `apps/turnos/signals.py` auto-generates transactions when appointments complete
- **Permission Classes**: Custom permission classes for role-based access (Admin, Manager, Empleado)
- **Querysets Filtering**: Always filter by `sucursal_id` or `centro_estetica_id` for multi-tenancy
- **Atomic Transactions**: Use `@transaction.atomic` for operations that modify multiple records (prevent double-booking)

**API Endpoints Pattern:**
```
/api/<resource>/          # List & Create (GET, POST)
/api/<resource>/<id>/     # Retrieve, Update, Delete (GET, PUT, PATCH, DELETE)
/api/<resource>/<id>/<action>/  # Custom actions (POST)
```

**Authentication Flow:**
1. Login: `POST /api/auth/login/` → Returns `access` and `refresh` tokens
2. Include `Authorization: Bearer <access_token>` in all requests
3. Refresh: `POST /api/auth/refresh/` with `refresh` token when access expires

### Frontend Architecture Patterns

**Component Organization (SOLID principles):**
- **UI Components** (`components/ui/`): Reusable, generic components (Button, Input, Modal, Card)
- **Feature Components** (`components/<feature>/`): Domain-specific components (ClienteForm, TurnoCalendar)
- **Pages** (`pages/`): Route-level components that compose features
- **Custom Hooks** (`hooks/`): Reusable logic abstraction (useClientes, useTurnos, useAuth)
- **Services** (`services/api.ts`): Centralized API communication with Axios
- **Stores** (`stores/`): Zustand state management for global state (auth, user, selected branch)
- **Types** (`types/models.ts`): TypeScript interfaces matching Django models

**Key Frontend Patterns:**
- **Container/Presenter Pattern**: Separate data fetching (container) from UI rendering (presenter)
- **Composition over Inheritance**: Build complex UIs by composing simple components
- **Custom Hooks for Data**: All API calls abstracted into hooks (e.g., `useClientes()`)
- **React Query (TanStack Query)**: For server state management, caching, and automatic refetching
- **Form Handling**: React Hook Form for complex forms with validation
- **Toast Notifications**: React Hot Toast for user feedback
- **Date Handling**: date-fns for date manipulation (appointments, reports)

**State Management Strategy:**
- **Server State**: React Query (API data, caching)
- **Global State**: Zustand (auth, user, selected branch)
- **Local State**: React useState (component-specific UI state)
- **Form State**: React Hook Form (form inputs and validation)

**API Integration Pattern:**
```typescript
// services/api.ts - Axios instance with JWT
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor adds JWT token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

## Database Schema

### Core Models

- **CentroEstetica**: Main tenant entity (each center is logically separated)
- **Sucursal**: Multiple locations per center (FK → CentroEstetica)
- **Usuario**: Authentication, roles, permissions (FK → Sucursal)
- **Cliente**: Customer data, contact info, preferences (FK → CentroEstetica)
- **Servicio**: Service catalog (name, duration, price, optional rented machine) (FK → Sucursal, MaquinaAlquilada)
- **MaquinaAlquilada**: Rented equipment/machines with daily costs (FK → Sucursal)
- **AlquilerMaquina**: Rental scheduling and tracking (FK → Sucursal, MaquinaAlquilada, Transaction)
  - States: PROGRAMADO (scheduled but not confirmed), CONFIRMADO (confirmed, will generate expense), COBRADO (expense already created), CANCELADO (cancelled)
  - Links to Transaction when expense is auto-generated
- **Turno**: Appointments (FKs → Cliente, Servicio, Usuario[professional], Sucursal)
  - States: Confirmado, Pendiente, Completado, Cancelado, No-Show
  - Payment states: Pagado, Con Seña, Pendiente
  - Automatically creates income transactions when completed
  - Automatically creates machine rental expense if service uses rented equipment (only once per day per machine)
- **Producto**: Inventory (stock, prices, categories) (FK → Sucursal)
- **TransactionCategory**: Hierarchical categories for financial transactions (2 levels max) (FK → Sucursal, parent_category)
  - Types: INCOME, EXPENSE
  - System categories (protected): Servicios, Productos, Salarios, Alquileres de Equipos
- **Transaction**: Financial records with automatic generation from appointments and sales (FK → Sucursal, TransactionCategory, Cliente)
  - Types: INCOME_SERVICE, INCOME_PRODUCT, INCOME_OTHER, EXPENSE
  - Auto-generated transactions are marked and linked to source (Turno, AlquilerMaquina)
  - Supports multiple payment methods (CASH, BANK_TRANSFER, DEBIT_CARD, CREDIT_CARD, MERCADOPAGO, OTHER)
- **Oferta**: Sales offers with discount percentages and validity periods (FK → Sucursal)
- **VentaOferta**: Sales with applied offers tracking (FK → Oferta, Cliente, Transaction)
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
- **Hierarchical Category System**: 2-level category structure (parent → subcategories) for INCOME and EXPENSE
- **System-Protected Categories**: Servicios, Productos, Salarios, Alquileres de Equipos (auto-created, cannot be deleted)
- **Automatic Transaction Generation**:
  - Income from completed appointments (full payment or remaining balance after deposit)
  - Deposit tracking when appointment payment state changes to "Con Seña"
  - Machine rental expenses when appointments with rented equipment are completed
  - Product sales with automatic inventory updates
- **Manual Transaction Entry**: For expenses like salaries, rent, marketing, supplies, services
- **Real-time Cash Flow**: Live income - expenses calculation with balance tracking
- **Multiple Payment Methods**: Cash, bank transfer, debit/credit cards, MercadoPago, other
- **Transaction Linking**: Auto-generated transactions link to source (appointment, product sale, rental)
- **Monthly Salary Processing**: Bulk salary payment registration for all employees
- **Financial Dashboard**: Summary metrics, charts by category, payment method breakdown
- **Period Comparisons**: Month-to-month, year-to-year analysis
- **Profit Margin Calculations**: Automatic profit percentage tracking
- **PDF and Excel Export**: Download financial reports in multiple formats

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

### 7. Rented Equipment Management
- **Machine/Equipment Catalog**: Track rented equipment (lasers, machines, specialized tools)
- **Daily Cost Tracking**: Record cost per day for each rented machine
- **Service Association**: Link services to rented equipment for automatic cost calculation
- **Rental Scheduling System**:
  - Schedule rentals in advance (state: PROGRAMADO)
  - Confirm rentals to enable automatic expense generation (state: CONFIRMADO)
  - Track when expense is created (state: COBRADO)
  - Cancel rentals if not needed (state: CANCELADO)
- **Reconciliation View**: Automatic detection of appointments using rented equipment without confirmed rentals
- **Smart Expense Generation**:
  - Only creates ONE expense per day per machine (not per appointment)
  - Requires confirmed rental before generating expense
  - Automatically links expense to rental record
  - Updates expense notes with all appointments using the machine that day
- **Profit Analysis**: Calculate real profit considering machine rental costs across all daily appointments
- **Provider Tracking**: Record supplier/provider information for each machine

### 8. Sales & Offers System
- **Offer Creation**: Define offers with discount percentages and validity periods
- **Active Offer Management**: Track offer status (active/inactive) and expiration
- **Sales with Offers**: Apply offers to product/service sales with automatic discount calculation
- **Sales Tracking**: Record all sales with linked offers, clients, and financial transactions
- **Offer Analytics**: Track offer performance, usage, and revenue impact

### 9. Employee & Commission Management
- **Employee Profiles**: Complete info including role, schedules, specialties, and monthly salary
- **Salary Management**:
  - Record monthly salary for each employee
  - Bulk salary processing for all employees at once
  - Automatic expense transactions when salaries are paid
- **Flexible Commission System**: Percentage per service, fixed amount, tiered structures
- **Real-time Commission Calculation**: Automatic calculation per service/product sold
- **Commission Reports**: By employee, period, service type with historical records
- **Performance Dashboards**: Monthly targets, revenue generated, services completed
- **Work Schedule Tracking**: Availability and schedule management

### 10. Multi-branch Support
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

### Docker (Primary Development Method)

The project is designed to run with Docker Compose. All services (PostgreSQL, Redis, Backend, Frontend, Celery) are orchestrated together.

```bash
# Build and start all services (first time or after dependency changes)
docker-compose up --build

# Start services (subsequent runs)
docker-compose up

# Start in background (detached mode)
docker-compose up -d

# Stop all services (preserves data)
docker-compose down

# Stop and remove volumes (CAUTION: deletes database data)
docker-compose down -v

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery

# Restart a specific service
docker-compose restart backend
docker-compose restart frontend

# Execute commands in backend container
docker-compose exec backend python manage.py <command>

# Access Django shell
docker-compose exec backend python manage.py shell

# Run tests in backend
docker-compose exec backend pytest

# Check service status
docker-compose ps
```

### Backend Django Commands (via Docker)

```bash
# Database operations
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py showmigrations

# User management
docker-compose exec backend python manage.py createsuperuser

# Data management
docker-compose exec backend python manage.py loaddata <fixture>
docker-compose exec backend python manage.py dumpdata <app> > fixture.json

# Testing
docker-compose exec backend pytest
docker-compose exec backend pytest --cov=apps
docker-compose exec backend pytest apps/turnos/tests/test_models.py::TestTurno

# Code quality (if configured)
docker-compose exec backend black .
docker-compose exec backend flake8 .
docker-compose exec backend isort .

# Database shell
docker-compose exec backend python manage.py dbshell
```

### Frontend React Commands (via Docker)

```bash
# Build TypeScript and check for errors
docker-compose exec frontend npm run build

# Lint code
docker-compose exec frontend npm run lint

# Run tests (if configured)
docker-compose exec frontend npm test
```

### Local Development (Without Docker)

If you need to run without Docker (not recommended for consistency):

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables in .env or export them
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/plataforma_estetica
# REDIS_URL=redis://localhost:6379/0

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# In separate terminals:
celery -A config worker -l info
celery -A config beat -l info
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev  # NOT 'npm start' - this project uses Vite
```

### Useful Docker Debugging Commands

```bash
# View container resource usage
docker stats

# Inspect a container
docker inspect plataforma_backend

# View container logs since specific time
docker-compose logs --since 30m backend

# Execute bash in container
docker-compose exec backend bash
docker-compose exec frontend sh

# Remove dangling images and free space
docker system prune

# Rebuild a single service
docker-compose up --build backend
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

## Recently Implemented Features (November 2025)

### Financial System Enhancements
- **Hierarchical Transaction Categories**: 2-level category structure with parent-child relationships
- **System-Protected Categories**: Auto-created categories that cannot be deleted (Servicios, Productos, Salarios, Alquileres)
- **Category CRUD UI**: Full create, edit, delete interface with subcategory management
- **Automatic Transaction Generation**: From appointments (deposits and full payments), machine rentals, and product sales
- **Monthly Salary Processing**: Bulk salary payment system with automatic expense creation

### Rented Equipment System (Complete Implementation)
- **Machine Catalog Management**: CRUD for rented equipment with daily cost tracking
- **Service-Machine Association**: Link services to rented equipment for cost analysis
- **Rental Scheduling**: 4-state workflow (PROGRAMADO → CONFIRMADO → COBRADO or CANCELADO)
- **Smart Expense Generation**: One expense per day per machine, only if rental is confirmed
- **Reconciliation Dashboard**: Alerts for appointments using equipment without confirmed rentals
- **Rental History**: Track all rentals with linked transactions and appointment details

### Sales & Offers System
- **Offer Management**: Create offers with discount percentages and validity periods
- **Sales with Offers**: Apply offers to sales with automatic discount calculation
- **Sales Tracking**: Complete history of sales with offer details and financial links

### Appointment System Improvements
- **Automatic Income Generation**: Creates transactions when appointments are completed
- **Deposit Tracking**: Automatic transaction when payment state changes to "Con Seña"
- **Machine Rental Integration**: Checks for confirmed rentals before creating expenses
- **Payment State Automation**: Automatically updates to PAGADO when appointment is completed

### Data Integrity Enhancements
- **Soft Delete for Services**: Prevents deletion of services with appointments, marks as inactive instead
- **Transaction Source Linking**: All auto-generated transactions link back to their source entity
- **Audit Trail**: `auto_generated` flag on transactions for transparency
- **Protected Categories**: System categories cannot be deleted or modified

### UI/UX Improvements
- **Rental Management Interface**: Three tabs (Services, Machines, Scheduled Rentals)
- **Reconciliation Alerts**: Visual warnings for pending rental confirmations
- **State Indicators**: Color-coded badges for rental states
- **Quick Actions**: Confirm/cancel buttons directly in rental list
- **Contextual Help**: Explanatory messages for each rental state

## Project Structure (Current Implementation)

```
backend/
  ├── config/                    # Django project settings, CORS, JWT config
  ├── apps/
  │   ├── clientes/              # Customer management (Cliente model)
  │   ├── turnos/                # Appointment system (Turno model)
  │   │   └── signals.py         # Auto-generate transactions from appointments
  │   ├── servicios/             # Service catalog with rented equipment
  │   │   ├── models.py          # Servicio, MaquinaAlquilada, AlquilerMaquina
  │   │   ├── views.py           # Service CRUD, rental scheduling, reconciliation
  │   │   └── serializers.py     # API serializers with profit calculations
  │   ├── inventario/            # Product inventory (Producto, MovimientoInventario)
  │   ├── finanzas/              # Financial system (Transaction, TransactionCategory, Oferta, VentaOferta)
  │   │   ├── models.py          # Hierarchical categories, auto-generated transactions
  │   │   ├── views.py           # Financial CRUD, salary processing, analytics
  │   │   └── serializers.py     # Transaction serializers with category relationships
  │   ├── empleados/             # Employee & commission management (Usuario, Comision)
  │   │   ├── models.py          # Employee with salary field
  │   │   └── views.py           # Salary processing endpoint
  │   └── notificaciones/        # WhatsApp integration (Notificacion model)
  ├── manage.py
  └── requirements.txt

frontend/
  ├── src/
  │   ├── components/
  │   │   ├── clientes/          # Client management components
  │   │   ├── empleados/         # Employee forms and lists
  │   │   ├── finanzas/          # Financial transactions, categories, salary processing
  │   │   ├── servicios/         # Services, machines, rental scheduling
  │   │   │   ├── ServicioForm.tsx
  │   │   │   ├── MaquinaForm.tsx
  │   │   │   ├── MaquinasList.tsx
  │   │   │   ├── AlquilerForm.tsx
  │   │   │   ├── AlquileresList.tsx
  │   │   │   └── AlquilerPendientes.tsx  # Reconciliation alerts
  │   │   ├── turnos/            # Appointment calendar and forms
  │   │   ├── productos/         # Product inventory
  │   │   └── ui/                # Reusable UI components (Button, Input, Select, Modal, etc.)
  │   ├── pages/                 # Main application pages
  │   │   ├── ServiciosPage.tsx  # Services with machines and rentals tabs
  │   │   ├── FinanzasPage.tsx   # Financial dashboard
  │   │   └── ...
  │   ├── services/
  │   │   └── api.ts             # Axios instance with JWT auth
  │   ├── hooks/                 # Custom React hooks
  │   ├── types/
  │   │   └── models.ts          # TypeScript interfaces matching Django models
  │   ├── utils/                 # Utility functions
  │   └── App.tsx
  ├── public/
  └── package.json

docker-compose.yml               # PostgreSQL, Redis, Backend, Frontend
.env.example
README.md
CLAUDE.md                        # This file
SISTEMA_FINANCIERO_SPEC.md       # Financial system technical spec
```

## Critical Business Logic & Workflows

### Appointment Creation Workflow
1. **Validation**: Check professional availability for the requested time slot
2. **Double-booking Prevention**: Use `@transaction.atomic` and query with `select_for_update()` to lock overlapping appointments
3. **Resource Assignment**: Assign professional (Usuario) and optionally rented equipment (MaquinaAlquilada)
4. **State Management**: Create appointment with initial state (Confirmado/Pendiente)
5. **Notifications**: Trigger WhatsApp confirmation (async via Celery)

**Location**: `apps/turnos/views.py` - `TurnoViewSet.create()`

### Appointment Completion & Payment Workflow (UPDATED Dec 2025)

**IMPORTANT CHANGE**: Automatic transaction generation on appointment completion is **DISABLED**.

**New Two-Step Process:**

#### Step 1: Mark Service as Completed (Turnos view - Green button)
- Changes `estado` to "COMPLETADO"
- **Does NOT create transaction**
- **Does NOT change payment status**
- Only registers that the service was performed
- Turno appears in Mi Caja for payment collection

#### Step 2: Register Payment (Mi Caja - Required)
- Employee navigates to **Mi Caja → Nueva Venta → Servicio**
- Selects the completed appointment from the list
- **Chooses correct payment method** (Cash, Card, Transfer, MercadoPago, etc.)
- Registers the payment amount
- **System automatically**:
  - Creates financial transaction (`Transaction`)
  - Marks appointment as COMPLETADO (if not already)
  - Marks payment status as PAGADO
  - Links transaction to appointment

**Why this workflow?**
- ✅ Full control over payment method selection
- ✅ Prevents incorrect default payment methods (old: always CASH)
- ✅ Conscious payment registration by employee
- ✅ Clear separation between service delivery and payment collection

**What STILL generates transactions automatically:**
- ✅ **Deposits (Señas)**: When `estado_pago` changes to "CON_SENA" → Auto-creates deposit transaction
- ❌ **Service completion**: NO longer auto-creates transaction

**Code Location**: `apps/turnos/signals.py` - SCENARIO 2 is disabled (commented out)

### Machine Rental Expense Generation
**States Flow**: PROGRAMADO → CONFIRMADO → COBRADO (or CANCELADO)

- **PROGRAMADO**: Rental scheduled but NOT confirmed (no expense generated)
- **CONFIRMADO**: Rental confirmed, ready for expense generation when appointment completes
- **COBRADO**: Expense already created (prevents duplicate expenses)
- **CANCELADO**: Rental cancelled, no expense

**Logic Location**: `apps/servicios/views.py` - `confirmar_alquiler()` action

### Financial Transaction Rules
1. **Auto-generated transactions** (from signals):
   - Appointment income: Type = INCOME_SERVICE, Category = "Servicios"
   - Product sale: Type = INCOME_PRODUCT, Category = "Productos"
   - Machine rental: Type = EXPENSE, Category = "Alquileres de Equipos"
   - Salary payment: Type = EXPENSE, Category = "Salarios"
2. **Manual transactions** (user-created):
   - Can use any category
   - Must have description, amount, date, payment method
3. **Protected Categories**: System categories cannot be deleted or modified
4. **Audit Trail**: All auto-generated transactions link to source entity for traceability

### Multi-tenancy Data Isolation
**EVERY database query MUST filter by tenant:**
```python
# Always filter by sucursal or centro_estetica
queryset = Turno.objects.filter(sucursal=request.user.sucursal)
# OR
queryset = Cliente.objects.filter(centro_estetica=request.user.centro_estetica)
```

**Serializer Context**: Pass user's branch/center in serializer context to enforce filtering in nested relationships.

### Permission & Access Control
**Role Hierarchy:**
1. **Empleado Básico**: Read-only for own appointments, clients
2. **Manager**: Full access to branch data, cannot access finances
3. **Administrador/Dueño**: Full access including financial module

**Implementation**: Custom permission classes in `apps/<module>/permissions.py`

**Financial Module Access**: ONLY Admin/Owner roles. Middleware blocks access for other roles.

## Important Notes

- **Double-booking prevention is critical**: Use database-level locking or atomic transactions when creating appointments
- **Multi-tenancy isolation**: Every query must filter by centro_estetica_id to prevent data leaks between clients
- **WhatsApp rate limits**: Implement proper queuing and retry logic for message sending
- **Financial data access**: Strictly enforce role-based access - only Admin/Owner roles
- **Image storage**: Use cloud storage (S3/Cloudinary) from the start, not local filesystem
- **Time zones**: Handle properly for multi-region deployments (use UTC in DB, convert in frontend)
- **Commission calculations**: Must be transactional and auditable - no manual adjustments without logs
- **Machine rental expenses**: CRITICAL - Only create ONE expense per day per machine, regardless of number of appointments. Check for confirmed rental (AlquilerMaquina.estado = CONFIRMADO or COBRADO) before generating expense.
- **Automatic transactions**: All auto-generated transactions must be marked with `auto_generated=True` and linked to source entity (Turno, AlquilerMaquina, VentaOferta) for audit trail
- **Soft delete for services**: Services with associated appointments cannot be hard-deleted. Use `activo=False` to preserve historical data integrity
- **Category protection**: System categories (Servicios, Productos, Salarios, Alquileres de Equipos) cannot be deleted or have their type changed
- **Rental reconciliation**: Always show alerts for appointments using rented equipment without confirmed rentals to prevent missing expenses
