# Frontend - Plataforma Estética

Frontend moderno construido con **React 18 + TypeScript + Vite** para la Plataforma de Gestión de Centros de Estética.

## Stack Tecnológico

- **React 18** - UI Framework
- **TypeScript** - Type Safety
- **Vite** - Build tool (ultra rápido)
- **TailwindCSS** - Utility-first CSS
- **React Router** - Routing
- **Zustand** - State Management (más simple que Redux)
- **React Query** - Server State Management
- **Axios** - HTTP Client
- **React Hook Form** - Formularios
- **Lucide React** - Iconos
- **React Hot Toast** - Notificaciones

## Estructura de Carpetas

```
src/
├── components/      # Componentes reutilizables
│   └── Layout.tsx   # Layout principal con sidebar
├── pages/           # Páginas/rutas
│   ├── LoginPage.tsx
│   ├── DashboardPage.tsx
│   ├── ClientesPage.tsx
│   ├── TurnosPage.tsx
│   └── ...
├── services/        # Servicios API
│   └── api.ts       # Axios instance configurada
├── stores/          # Zustand stores
│   └── authStore.ts # Estado de autenticación
├── types/           # Tipos TypeScript
│   └── models.ts    # Tipos de modelos Django
├── hooks/           # Custom React hooks
├── utils/           # Funciones utilitarias
├── App.tsx          # Componente principal
├── main.tsx         # Entry point
└── index.css        # Estilos globales

```

## Características de TypeScript

### Tipos de Modelos Django

Todos los modelos de Django tienen sus tipos TypeScript correspondientes en `src/types/models.ts`:

```typescript
import { Cliente, Turno, EstadoTurno } from '@/types/models'

// Autocomplete completo!
const cliente: Cliente = {
  id: 1,
  nombre: 'Juan',
  apellido: 'Pérez',
  // ... TypeScript te sugiere todos los campos
}
```

### Axios con Tipos

```typescript
import api from '@/services/api'
import { Cliente, PaginatedResponse } from '@/types/models'

// TypeScript sabe exactamente qué devuelve
const response = await api.get<PaginatedResponse<Cliente>>('/clientes/')
const clientes = response.data.results // Type: Cliente[]
```

### Zustand Store Tipado

```typescript
import { useAuthStore } from '@/stores/authStore'

// Autocompletado de todo el estado
const { user, isAuthenticated, logout } = useAuthStore()
```

## Path Aliases

El proyecto usa path aliases para imports más limpios:

```typescript
// ❌ Antes
import { useAuthStore } from '../../../stores/authStore'

// ✅ Ahora
import { useAuthStore } from '@/stores/authStore'
```

## Desarrollo

### Instalación

```bash
npm install
```

### Servidor de Desarrollo

```bash
npm run dev
```

El servidor arranca en `http://localhost:5173`

### Build para Producción

```bash
npm run build
```

Esto ejecuta el type-check de TypeScript y luego construye la aplicación.

### Linting

```bash
npm run lint
```

### Preview del Build

```bash
npm run preview
```

## Autenticación

El sistema de autenticación usa JWT con refresh tokens:

1. Login → recibe `access` y `refresh` tokens
2. Axios interceptor agrega el token a cada request
3. Si el token expira (401), automáticamente usa el refresh token
4. Si el refresh falla, redirige al login

Todo tipado con TypeScript!

## Agregar Nuevas Páginas

1. Crear el componente en `src/pages/MiPagina.tsx`
2. Agregar la ruta en `src/App.tsx`
3. Agregar al sidebar en `src/components/Layout.tsx`

## Agregar Nuevos Tipos

Cuando agregues modelos en Django:

1. Agrega la interfaz en `src/types/models.ts`
2. TypeScript te avisará automáticamente dónde falta actualizar

## Variables de Entorno

Crea un archivo `.env` basado en `.env.example`:

```env
VITE_API_URL=http://localhost:8000/api
```

Acceso en código:

```typescript
const apiUrl = import.meta.env.VITE_API_URL
```

## Ventajas de TypeScript en este Proyecto

✅ **Autocomplete**: El editor te sugiere campos, métodos, etc.
✅ **Catch de Errores**: Errores antes de ejecutar el código
✅ **Refactoring Seguro**: Cambios sin miedo a romper algo
✅ **Documentación Viva**: Los tipos son la documentación
✅ **Menos Bugs**: Type safety previene errores comunes
✅ **Mejor DX**: Developer Experience increíble con VSCode

## Tips de TypeScript

### Tipos opcionales vs obligatorios

```typescript
interface Usuario {
  nombre: string      // Obligatorio
  apellido: string    // Obligatorio
  email?: string      // Opcional (puede ser undefined)
  foto: string | null // Puede ser string o null
}
```

### Type vs Interface

```typescript
// Interface - para objetos
interface Cliente {
  id: number
  nombre: string
}

// Type - para uniones, aliases, etc
type EstadoTurno = 'PENDIENTE' | 'CONFIRMADO' | 'CANCELADO'
```

### Enum vs Union Type

```typescript
// Enum (usado en models.ts para coincidir con Django)
enum Rol {
  ADMIN = 'ADMIN',
  MANAGER = 'MANAGER',
}

// Union Type (más simple)
type Rol = 'ADMIN' | 'MANAGER'
```

## Recursos

- [React Docs](https://react.dev/)
- [TypeScript Docs](https://www.typescriptlang.org/docs/)
- [Vite Docs](https://vitejs.dev/)
- [TailwindCSS Docs](https://tailwindcss.com/docs)
- [Zustand](https://github.com/pmndrs/zustand)
- [React Query](https://tanstack.com/query/latest)

---

Para más información sobre el proyecto completo, ver [README principal](../README.md)
