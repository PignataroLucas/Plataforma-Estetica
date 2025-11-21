# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
