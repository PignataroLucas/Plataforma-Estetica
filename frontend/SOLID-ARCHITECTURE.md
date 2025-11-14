# Arquitectura SOLID en React Funcional

## Principios SOLID Aplicados

### 1️⃣ Single Responsibility Principle (SRP)
**"Un componente debe tener una sola razón para cambiar"**

```typescript
// ❌ MAL - Componente con múltiples responsabilidades
const UserDashboard = () => {
  // Lógica de autenticación
  // Lógica de fetching de datos
  // Lógica de UI
  // Lógica de navegación
}

// ✅ BIEN - Separado en responsabilidades únicas
const UserDashboard = () => {
  return (
    <DashboardLayout>
      <UserProfile />
      <UserStatistics />
      <UserActions />
    </DashboardLayout>
  )
}
```

### 2️⃣ Open/Closed Principle (OCP)
**"Abierto a extensión, cerrado a modificación"**

```typescript
// ✅ Componente extensible via props y composition
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  onClick?: () => void
  children: React.ReactNode
}

const Button = ({ variant = 'primary', size = 'md', ...props }: ButtonProps) => {
  // Extendible sin modificar el código base
}
```

### 3️⃣ Liskov Substitution Principle (LSP)
**"Los componentes con la misma interfaz deben ser intercambiables"**

```typescript
// Interfaz común para todos los inputs
interface InputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  error?: string
}

// Todos implementan la misma interfaz = intercambiables
const TextInput = (props: InputProps) => { ... }
const EmailInput = (props: InputProps) => { ... }
const PhoneInput = (props: InputProps) => { ... }
```

### 4️⃣ Interface Segregation Principle (ISP)
**"No depender de props que no usas"**

```typescript
// ❌ MAL - Interfaz grande que obliga a pasar muchos props
interface UserCardProps {
  id: number
  name: string
  email: string
  phone: string
  address: string
  avatar: string
  bio: string
  // ... 20+ props más
}

// ✅ BIEN - Interfaces específicas
interface UserAvatarProps {
  avatar: string
  name: string
}

interface UserContactProps {
  email: string
  phone: string
}
```

### 5️⃣ Dependency Inversion Principle (DIP)
**"Depender de abstracciones, no de implementaciones concretas"**

```typescript
// ✅ Custom Hook como abstracción
const useClientes = () => {
  // Abstracción del data fetching
  // El componente no sabe si viene de API, localStorage, etc.
}

// Componente depende de la abstracción
const ClientesList = () => {
  const { clientes, loading, error } = useClientes()
  // ...
}
```

## 📁 Estructura de Carpetas Recomendada

```
src/
├── components/          # Componentes reutilizables (SRP)
│   ├── ui/             # Componentes UI básicos
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.types.ts
│   │   │   └── index.ts
│   │   ├── Input/
│   │   ├── Card/
│   │   └── Modal/
│   ├── layout/         # Componentes de layout
│   │   ├── Sidebar/
│   │   ├── Header/
│   │   └── Layout/
│   └── features/       # Componentes específicos de features
│       ├── ClienteCard/
│       ├── TurnoCalendar/
│       └── InventoryTable/
├── pages/              # Páginas (composers)
│   ├── ClientesPage/
│   ├── TurnosPage/
│   └── DashboardPage/
├── hooks/              # Custom hooks (DIP)
│   ├── useClientes.ts
│   ├── useTurnos.ts
│   └── useAuth.ts
├── services/           # Servicios (abstracciones)
│   ├── api/
│   │   ├── clientesApi.ts
│   │   ├── turnosApi.ts
│   │   └── index.ts
│   └── storage/
├── stores/             # Estado global
│   └── authStore.ts
├── types/              # TypeScript types
│   └── models.ts
└── utils/              # Utilidades
    ├── validation.ts
    └── formatters.ts
```

## 🎯 Patrones Recomendados

### Container/Presenter Pattern

```typescript
// Container: Lógica y estado
const ClientesPageContainer = () => {
  const { clientes, loading, error } = useClientes()
  const handleCreate = () => { ... }
  const handleEdit = () => { ... }

  return (
    <ClientesPagePresenter
      clientes={clientes}
      loading={loading}
      onCreateCliente={handleCreate}
      onEditCliente={handleEdit}
    />
  )
}

// Presenter: Solo UI
const ClientesPagePresenter = ({ clientes, loading, onCreateCliente }) => {
  return (
    <div>
      {loading ? <Spinner /> : <ClientesList clientes={clientes} />}
      <Button onClick={onCreateCliente}>Nuevo Cliente</Button>
    </div>
  )
}
```

### Composition over Inheritance

```typescript
// ✅ Composición
const Modal = ({ children, ...props }) => (
  <ModalWrapper {...props}>
    {children}
  </ModalWrapper>
)

// Uso
<Modal>
  <ModalHeader>Título</ModalHeader>
  <ModalBody>Contenido</ModalBody>
  <ModalFooter>Acciones</ModalFooter>
</Modal>
```

### Custom Hooks para Lógica Reutilizable

```typescript
// Hook reutilizable (DIP)
const useForm = <T>(initialValues: T) => {
  const [values, setValues] = useState(initialValues)
  const [errors, setErrors] = useState({})

  const handleChange = (field: keyof T, value: any) => {
    setValues(prev => ({ ...prev, [field]: value }))
  }

  return { values, errors, handleChange }
}

// Uso en múltiples componentes
const ClienteForm = () => {
  const { values, handleChange } = useForm({ nombre: '', email: '' })
}
```

## 📝 Convenciones de Código

1. **Un archivo, un componente principal**
2. **Props con TypeScript interfaces**
3. **Export named por defecto, export default al final**
4. **Hooks al principio del componente**
5. **Funciones auxiliares fuera del componente**
6. **Comentarios solo para lógica compleja**

## 🧪 Testing

```typescript
// Componentes pequeños = fáciles de testear
describe('Button', () => {
  it('should call onClick when clicked', () => {
    const onClick = jest.fn()
    render(<Button onClick={onClick}>Click me</Button>)
    fireEvent.click(screen.getByText('Click me'))
    expect(onClick).toHaveBeenCalled()
  })
})
```
