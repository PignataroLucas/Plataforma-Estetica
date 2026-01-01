# Especificación: Sistema de Registro y Onboarding

## Resumen Ejecutivo

Implementación de un flujo de registro público que permita a nuevos centros estéticos registrarse en la plataforma de forma autónoma, creando su centro, sucursal principal y usuario administrador, todo previo al inicio de sesión.

**⚠️ NOTA IMPORTANTE**: Este flujo de registro simplificado crea **una única sucursal** por centro estético. El backend ya soporta múltiples sucursales, pero la UI para gestionar múltiples ubicaciones es una **feature futura** documentada en `FEATURES_PENDIENTES.md`. Los centros que requieran múltiples sucursales pueden agregarlas posteriormente (requiere desarrollo de UI).

## Objetivo

Permitir que nuevos clientes puedan:
1. Registrar su centro estético en la plataforma
2. Configurar su sucursal principal
3. Crear su usuario administrador
4. Acceder inmediatamente al sistema

**Actualmente**: Se requiere creación manual de CentroEstetica y Usuario vía Django Admin o comandos.

**Nuevo flujo**: Proceso de autoregistro guiado en **3 pasos** con validación automática.

---

## Flujo de Usuario (UX)

### Pantalla de Bienvenida
**Ruta**: `/registro` o `/signup`

**Contenido**:
- Título: "Registra tu Centro Estético"
- Subtítulo: "Comienza a gestionar tu negocio en minutos"
- Beneficios clave (3-4 bullets)
- Botón: "Comenzar Registro"
- Link: "¿Ya tienes cuenta? Inicia sesión"

### Paso 1: Datos del Centro Estético

**Formulario**:
- **Nombre del Centro** (requerido)
  - Placeholder: "Ej: Belleza & Spa Deluxe"
  - Validación: 3-100 caracteres, único en la plataforma

- **Teléfono Principal** (requerido)
  - Format: +54 (código de área) número
  - Validación: formato argentino
  - Usado para contacto y notificaciones

- **Email del Centro** (requerido)
  - Validación: formato email válido, único
  - Usado para comunicaciones oficiales

- **Dirección Fiscal** (opcional)
  - Calle, número, ciudad, provincia, código postal
  - Puede completarse después

- **CUIT/CUIL** (opcional)
  - Para futuras integraciones con AFIP
  - Validación: formato argentino

**Botón**: "Siguiente: Configurar Sucursales"

### Paso 2: Datos de la Sucursal

**Título**: "Configura tu sucursal principal"

**Texto explicativo**:
"Ingresa los datos de la ubicación de tu centro. Si tienes múltiples locaciones, podrás agregarlas después desde el dashboard."

**Formulario**:
- **Nombre de la Sucursal** (requerido)
  - Default sugerido: "Principal" o mismo nombre que el centro
  - Placeholder: "Ej: Principal, Sede Central, Sucursal Palermo"
  - Validación: 3-100 caracteres

- **Dirección Completa** (requerido)
  - Placeholder: "Calle, número, barrio"
  - Validación: mínimo 10 caracteres

- **Ciudad** (requerido)
  - Validación: 3-100 caracteres

- **Provincia** (requerido)
  - Select con provincias argentinas pre-cargadas
  - Default: "Buenos Aires"

- **Código Postal** (opcional)
  - Placeholder: "Ej: 1425"

- **Teléfono** (opcional)
  - Default: usa el teléfono del centro
  - Se puede modificar si la sucursal tiene línea propia

**Info Box** (azul claro):
💡 **¿Tienes múltiples sucursales?** Por ahora crearemos solo la principal. Podrás agregar más ubicaciones próximamente desde la configuración del centro.

**Botón**: "Siguiente: Crear Usuario Administrador"

### Paso 3: Usuario Administrador

**Formulario**:
- **Nombre Completo** (requerido)
  - Validación: 3-100 caracteres

- **Email** (requerido)
  - Será el username para login
  - Validación: formato email, único en la plataforma
  - Confirmación: repetir email

- **Teléfono Personal** (requerido)
  - Para recuperación de cuenta

- **Contraseña** (requerido)
  - Mínimo 8 caracteres
  - Debe incluir: mayúscula, minúscula, número
  - Indicador visual de fortaleza (débil/media/fuerte)

- **Confirmar Contraseña** (requerido)
  - Validación: debe coincidir

**Checkbox**:
☐ Acepto los [Términos y Condiciones] y la [Política de Privacidad]

**Botón**: "Crear mi Cuenta"

### Paso 4: Confirmación y Redirección

**Pantalla de éxito**:
- ✓ "¡Tu cuenta ha sido creada!"
- "Centro: [Nombre del Centro]"
- "Sucursal: [Nombre de la Sucursal]"
- "Ya puedes comenzar a usar la plataforma"

**Opciones**:
- Botón principal: "Ir al Dashboard"
- Link secundario: "Ver tutorial de inicio rápido"

**Redirección automática**: Después de 5 segundos al dashboard con login automático (token JWT generado).

---

## Modelos de Datos

### CentroEstetica (ya existe, extensión mínima)

```python
class CentroEstetica(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(unique=True)

    # Opcionales (pueden completarse después)
    direccion_fiscal = models.TextField(blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    provincia = models.CharField(max_length=100, blank=True)
    codigo_postal = models.CharField(max_length=10, blank=True)
    cuit = models.CharField(max_length=13, blank=True, unique=True, null=True)

    # Estado de onboarding
    onboarding_completado = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    # Configuración inicial
    zona_horaria = models.CharField(max_length=50, default='America/Argentina/Buenos_Aires')

    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Centro Estético'
        verbose_name_plural = 'Centros Estéticos'
```

### Sucursal (ya existe, sin cambios necesarios)

```python
class Sucursal(models.Model):
    centro_estetica = models.ForeignKey(CentroEstetica, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    direccion = models.TextField()
    telefono = models.CharField(max_length=20, blank=True)
    es_principal = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
```

### Usuario (ya existe, sin cambios necesarios)

```python
class Usuario(AbstractUser):
    centro_estetica = models.ForeignKey(CentroEstetica, on_delete=models.CASCADE)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.SET_NULL, null=True)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES)
    telefono = models.CharField(max_length=20)
    # ... otros campos existentes
```

---

## Endpoints de API

### 1. Validar disponibilidad de nombre de centro

```
GET /api/registro/validar-nombre-centro/?nombre={nombre}

Response:
{
  "disponible": true/false,
  "mensaje": "El nombre está disponible" | "Este nombre ya está en uso"
}
```

### 2. Validar email único

```
GET /api/registro/validar-email/?email={email}

Response:
{
  "disponible": true/false,
  "mensaje": "Email disponible" | "Este email ya está registrado"
}
```

### 3. Crear registro completo (transacción atómica)

```
POST /api/registro/crear-cuenta/

Request Body:
{
  "centro": {
    "nombre": "Belleza & Spa Deluxe",
    "telefono": "+54 11 1234-5678",
    "email": "contacto@bellezadeluxe.com",
    "direccion_fiscal": "Av. Santa Fe 1234",
    "ciudad": "Buenos Aires",
    "provincia": "Buenos Aires",
    "codigo_postal": "1425",
    "cuit": "20-12345678-9"
  },
  "sucursal": {
    "nombre": "Principal",
    "direccion": "Av. Santa Fe 1234",
    "ciudad": "Buenos Aires",
    "provincia": "Buenos Aires",
    "codigo_postal": "1425",
    "telefono": "+54 11 1234-5678"
  },
  "admin": {
    "username": "admin@bellezadeluxe.com",
    "email": "admin@bellezadeluxe.com",
    "password": "SecurePassword123!",
    "first_name": "María",
    "last_name": "González",
    "telefono": "+54 9 11 1234-5678"
  },
  "acepta_terminos": true
}

Response (éxito - 201 Created):
{
  "success": true,
  "mensaje": "Cuenta creada exitosamente",
  "centro": {
    "id": 123,
    "nombre": "Belleza & Spa Deluxe"
  },
  "sucursal": {
    "id": 1,
    "nombre": "Principal"
  },
  "admin": {
    "id": 456,
    "email": "admin@bellezadeluxe.com",
    "nombre_completo": "María González"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}

Response (error - 400 Bad Request):
{
  "success": false,
  "errores": {
    "centro.nombre": ["Este nombre ya está en uso"],
    "admin.email": ["Este email ya está registrado"],
    "sucursal.direccion": ["La dirección es requerida"]
  }
}
```

---

## Validaciones del Backend

### Validaciones del Centro

1. **Nombre único**: Query a CentroEstetica para verificar unicidad (case-insensitive)
2. **Email único**: Verificar que no exista en CentroEstetica
3. **Teléfono formato válido**: Regex para formato argentino
4. **CUIT formato válido** (si se proporciona): Validar formato y dígito verificador

### Validaciones de Sucursal

1. **Campos requeridos**: nombre, dirección, ciudad, provincia
2. **Dirección válida**: Mínimo 10 caracteres
3. **Provincia válida**: Debe estar en lista de provincias argentinas
4. **Teléfono opcional**: Si no se proporciona, usa el del centro
5. **Sucursal marcada como principal**: `es_principal=True` por default (es la única)

### Validaciones de Usuario Admin

1. **Email único global**: Query a Usuario (AbstractUser) para verificar
2. **Username = email**: Asegurar consistencia
3. **Contraseña segura**:
   - Mínimo 8 caracteres
   - Al menos 1 mayúscula
   - Al menos 1 minúscula
   - Al menos 1 número
   - Opcionalmente: 1 carácter especial
4. **Términos aceptados**: `acepta_terminos` debe ser `true`

### Transacción Atómica

TODO el proceso de registro debe ser una transacción atómica:

```python
from django.db import transaction

@transaction.atomic
def crear_cuenta_completa(data):
    # 1. Crear CentroEstetica
    centro = CentroEstetica.objects.create(**data['centro'])

    # 2. Crear Sucursal Principal
    sucursal = Sucursal.objects.create(
        centro_estetica=centro,
        es_principal=True,  # Siempre es principal (es la única)
        activa=True,
        **data['sucursal']
    )

    # 3. Crear Usuario Admin
    admin = Usuario.objects.create_user(
        username=data['admin']['email'],
        email=data['admin']['email'],
        password=data['admin']['password'],
        centro_estetica=centro,
        sucursal=sucursal,
        rol='ADMIN',
        first_name=data['admin']['first_name'],
        last_name=data['admin']['last_name'],
        telefono=data['admin']['telefono']
    )

    # 4. Crear categorías financieras del sistema (auto-generadas)
    from apps.finanzas.utils import crear_categorias_sistema
    crear_categorias_sistema(sucursal)

    # 5. Generar tokens JWT
    refresh = RefreshToken.for_user(admin)

    return {
        'centro': centro,
        'sucursal': sucursal,
        'admin': admin,
        'tokens': {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
    }
```

**Rollback automático**: Si cualquier paso falla, se revierte TODO.

---

## Componentes Frontend

### Estructura de Carpetas

```
frontend/src/
├── pages/
│   ├── RegistroPage.tsx          # Página principal de registro
│   └── LoginPage.tsx              # Página de login (ya existe)
├── components/
│   └── registro/
│       ├── PasoUno.tsx            # Datos del Centro
│       ├── PasoDos.tsx            # Datos de la Sucursal
│       ├── PasoTres.tsx           # Usuario Admin
│       ├── Confirmacion.tsx       # Pantalla de éxito
│       └── ProgressIndicator.tsx  # Indicador de pasos (1/3, 2/3, 3/3)
└── services/
    └── registro.ts                # API calls para registro
```

### Estado del Formulario

**Manejo de estado**: React Hook Form para validación y control

```typescript
interface RegistroFormData {
  centro: {
    nombre: string;
    telefono: string;
    email: string;
    direccion_fiscal?: string;
    ciudad?: string;
    provincia?: string;
    codigo_postal?: string;
    cuit?: string;
  };
  sucursal: {
    nombre: string;
    direccion: string;
    ciudad: string;
    provincia: string;
    codigo_postal?: string;
    telefono?: string;
  };
  admin: {
    username: string; // será igual a email
    email: string;
    password: string;
    confirmar_password: string;
    first_name: string;
    last_name: string;
    telefono: string;
  };
  acepta_terminos: boolean;
}
```

### Navegación entre Pasos

- **URL routing**: `/registro/paso-1`, `/registro/paso-2`, `/registro/paso-3`
- **Validación progresiva**: No permite avanzar si el paso actual tiene errores
- **Guardar progreso**: localStorage para no perder datos al recargar
- **Volver atrás**: Permitido sin pérdida de datos

---

## Consideraciones de Seguridad

### Durante el Registro

1. **Rate Limiting**: Máximo 5 intentos de registro por IP por hora
2. **CAPTCHA**: Implementar reCAPTCHA v3 en el paso final para prevenir bots
3. **Validación de email**: Opcional - Enviar email de verificación (puede implementarse después)
4. **Contraseñas hasheadas**: Usar bcrypt (Django default) antes de guardar
5. **HTTPS obligatorio**: Todo el flujo sobre SSL/TLS

### Prevención de Fraude

1. **Validación de email corporativo**: Advertencia si usa email gratuito (gmail, hotmail)
2. **Verificación telefónica**: Opcional - SMS con código de verificación
3. **Blacklist de nombres**: Prevenir nombres ofensivos o de spam
4. **Límite de centros por IP**: Máximo 3 centros desde la misma IP en 24 horas

### Logs de Auditoría

Registrar TODO intento de registro (exitoso o fallido):
- IP del solicitante
- Timestamp
- Datos enviados (sin contraseñas)
- Resultado (éxito/error)
- Errores de validación

---

## Implementación Técnica

### Backend (Django)

**Ubicación**: `backend/apps/empleados/` (contiene Usuario y autenticación)

**Nuevos archivos**:
```
apps/empleados/
├── views_registro.py           # ViewSet para registro
├── serializers_registro.py     # Serializers específicos
├── validators.py               # Validadores custom
└── urls_registro.py            # Rutas de registro
```

**Serializers necesarios**:

```python
# serializers_registro.py
from rest_framework import serializers
from apps.empleados.models import Usuario, CentroEstetica, Sucursal

class RegistroCentroSerializer(serializers.ModelSerializer):
    class Meta:
        model = CentroEstetica
        fields = [
            'nombre', 'telefono', 'email', 'direccion_fiscal',
            'ciudad', 'provincia', 'codigo_postal', 'cuit'
        ]

    def validate_nombre(self, value):
        if CentroEstetica.objects.filter(nombre__iexact=value).exists():
            raise serializers.ValidationError("Este nombre ya está en uso")
        return value

class RegistroSucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = ['nombre', 'direccion', 'ciudad', 'provincia', 'codigo_postal', 'telefono']

    def validate_direccion(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("La dirección debe tener al menos 10 caracteres")
        return value

class RegistroAdminSerializer(serializers.ModelSerializer):
    confirmar_password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'password', 'confirmar_password',
            'first_name', 'last_name', 'telefono'
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        if data['password'] != data['confirmar_password']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data

class RegistroCompletoSerializer(serializers.Serializer):
    centro = RegistroCentroSerializer()
    sucursal = RegistroSucursalSerializer()
    admin = RegistroAdminSerializer()
    acepta_terminos = serializers.BooleanField()

    def validate_acepta_terminos(self, value):
        if not value:
            raise serializers.ValidationError("Debe aceptar los términos y condiciones")
        return value
```

**ViewSet**:

```python
# views_registro.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

class RegistroViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]  # Acceso público

    @action(detail=False, methods=['get'])
    def validar_nombre_centro(self, request):
        """Valida si el nombre del centro está disponible"""
        nombre = request.query_params.get('nombre')
        if not nombre:
            return Response({'error': 'Nombre requerido'}, status=400)

        existe = CentroEstetica.objects.filter(nombre__iexact=nombre).exists()
        return Response({
            'disponible': not existe,
            'mensaje': 'Nombre disponible' if not existe else 'Este nombre ya está en uso'
        })

    @action(detail=False, methods=['get'])
    def validar_email(self, request):
        """Valida si el email está disponible"""
        email = request.query_params.get('email')
        if not email:
            return Response({'error': 'Email requerido'}, status=400)

        existe = Usuario.objects.filter(email__iexact=email).exists()
        return Response({
            'disponible': not existe,
            'mensaje': 'Email disponible' if not existe else 'Este email ya está registrado'
        })

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def crear_cuenta(self, request):
        """Crea el centro, sucursal principal y usuario admin en una transacción"""
        serializer = RegistroCompletoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                'success': False,
                'errores': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # 1. Crear Centro
        centro = CentroEstetica.objects.create(**data['centro'])

        # 2. Crear Sucursal Principal
        sucursal_data = data['sucursal']
        # Si no se proporciona teléfono, usar el del centro
        if not sucursal_data.get('telefono'):
            sucursal_data['telefono'] = data['centro']['telefono']

        sucursal = Sucursal.objects.create(
            centro_estetica=centro,
            es_principal=True,  # Siempre es principal (única sucursal)
            activa=True,
            **sucursal_data
        )

        # 3. Crear Usuario Admin
        admin_data = data['admin']

        admin = Usuario.objects.create_user(
            username=admin_data['email'],
            email=admin_data['email'],
            password=admin_data['password'],
            first_name=admin_data['first_name'],
            last_name=admin_data['last_name'],
            telefono=admin_data['telefono'],
            centro_estetica=centro,
            sucursal=sucursal,
            rol='ADMIN'
        )

        # 4. Crear categorías del sistema
        from apps.finanzas.utils import crear_categorias_sistema
        crear_categorias_sistema(sucursal)

        # 5. Generar tokens JWT
        refresh = RefreshToken.for_user(admin)

        return Response({
            'success': True,
            'mensaje': 'Cuenta creada exitosamente',
            'centro': {
                'id': centro.id,
                'nombre': centro.nombre
            },
            'sucursal': {
                'id': sucursal.id,
                'nombre': sucursal.nombre
            },
            'admin': {
                'id': admin.id,
                'email': admin.email,
                'nombre_completo': admin.get_full_name()
            },
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)
```

**Routing**:

```python
# apps/empleados/urls_registro.py
from rest_framework.routers import DefaultRouter
from .views_registro import RegistroViewSet

router = DefaultRouter()
router.register(r'registro', RegistroViewSet, basename='registro')

urlpatterns = router.urls
```

**Incluir en URLs principales**:

```python
# backend/config/urls.py
urlpatterns = [
    # ... otras rutas
    path('api/', include('apps.empleados.urls_registro')),
]
```

### Frontend (React + TypeScript)

**Servicio de API**:

```typescript
// frontend/src/services/registro.ts
import { api } from './api';

export interface CentroData {
  nombre: string;
  telefono: string;
  email: string;
  direccion_fiscal?: string;
  ciudad?: string;
  provincia?: string;
  codigo_postal?: string;
  cuit?: string;
}

export interface SucursalData {
  nombre: string;
  direccion: string;
  ciudad: string;
  provincia: string;
  codigo_postal?: string;
  telefono?: string;
}

export interface AdminData {
  username: string;
  email: string;
  password: string;
  confirmar_password: string;
  first_name: string;
  last_name: string;
  telefono: string;
}

export interface RegistroCompleto {
  centro: CentroData;
  sucursal: SucursalData;
  admin: AdminData;
  acepta_terminos: boolean;
}

export const registroService = {
  validarNombreCentro: async (nombre: string) => {
    const response = await api.get('/registro/validar_nombre_centro/', {
      params: { nombre }
    });
    return response.data;
  },

  validarEmail: async (email: string) => {
    const response = await api.get('/registro/validar_email/', {
      params: { email }
    });
    return response.data;
  },

  crearCuenta: async (data: RegistroCompleto) => {
    const response = await api.post('/registro/crear_cuenta/', data);
    return response.data;
  }
};
```

**Página principal de registro**:

```typescript
// frontend/src/pages/RegistroPage.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PasoUno from '../components/registro/PasoUno';
import PasoDos from '../components/registro/PasoDos';
import PasoTres from '../components/registro/PasoTres';
import Confirmacion from '../components/registro/Confirmacion';
import ProgressIndicator from '../components/registro/ProgressIndicator';
import { RegistroCompleto } from '../services/registro';

const RegistroPage: React.FC = () => {
  const [paso, setPaso] = useState(1);
  const [formData, setFormData] = useState<Partial<RegistroCompleto>>({});
  const [registroExitoso, setRegistroExitoso] = useState(false);
  const navigate = useNavigate();

  const avanzarPaso = (data: Partial<RegistroCompleto>) => {
    setFormData({ ...formData, ...data });
    setPaso(paso + 1);
  };

  const retrocederPaso = () => {
    setPaso(paso - 1);
  };

  const completarRegistro = async (tokens: { access: string; refresh: string }) => {
    // Guardar tokens en localStorage
    localStorage.setItem('access_token', tokens.access);
    localStorage.setItem('refresh_token', tokens.refresh);

    setRegistroExitoso(true);

    // Redireccionar al dashboard después de 5 segundos
    setTimeout(() => {
      navigate('/dashboard');
    }, 5000);
  };

  if (registroExitoso) {
    return <Confirmacion centro={formData.centro!} />;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8">
          Registra tu Centro Estético
        </h1>

        <ProgressIndicator pasoActual={paso} totalPasos={3} />

        <div className="bg-white shadow-lg rounded-lg p-8 mt-8">
          {paso === 1 && (
            <PasoUno
              initialData={formData.centro}
              onNext={(data) => avanzarPaso({ centro: data })}
            />
          )}

          {paso === 2 && (
            <PasoDos
              initialData={formData.sucursal}
              onNext={(data) => avanzarPaso({ sucursal: data })}
              onBack={retrocederPaso}
            />
          )}

          {paso === 3 && (
            <PasoTres
              formData={formData as RegistroCompleto}
              onComplete={completarRegistro}
              onBack={retrocederPaso}
            />
          )}
        </div>

        <div className="text-center mt-6">
          <a href="/login" className="text-blue-600 hover:underline">
            ¿Ya tienes cuenta? Inicia sesión
          </a>
        </div>
      </div>
    </div>
  );
};

export default RegistroPage;
```

---

## Mejoras Futuras (Post-MVP)

### Fase 1: Verificación de Email
- Enviar email de confirmación con link de activación
- Cuenta en estado "pendiente" hasta verificar email
- Reenvío de email de verificación

### Fase 2: Verificación Telefónica (SMS)
- Código de verificación vía SMS
- Requerido para cuentas de alto valor

### Fase 3: Onboarding Guiado
- Tour interactivo del dashboard
- Tooltips y hints contextuales
- Checklist de primeros pasos:
  - [ ] Agregar primer servicio
  - [ ] Crear primer empleado
  - [ ] Registrar primer cliente
  - [ ] Agendar primer turno

### Fase 4: Importación de Datos
- Importar clientes desde Excel/CSV
- Importar servicios y precios
- Migración desde otras plataformas

### Fase 5: Configuración Avanzada
- Personalización de horarios por sucursal
- Configuración de notificaciones
- Temas y branding personalizado

---

## Casos de Uso y Ejemplos

### Caso 1: Centro con una sola ubicación

**Usuario**: María, dueña de "Spa Relax" en Palermo

**Flujo**:
1. **Paso 1**: Ingresa nombre "Spa Relax", teléfono +54 11 1234-5678, email contacto@sparelax.com
2. **Paso 2**: Configura sucursal "Principal" en Av. Santa Fe 1234, Palermo, Buenos Aires
3. **Paso 3**: Crea su usuario admin con email maria@sparelax.com
4. Acepta términos y completa registro
5. Accede directamente al dashboard

**Resultado**:
- 1 CentroEstetica creado ("Spa Relax")
- 1 Sucursal creada ("Principal", marcada como es_principal=True)
- 1 Usuario Admin creado (María)
- Listo para agregar servicios y empleados

### Caso 2: Centro que planea expandirse

**Usuario**: Carlos, dueño de "Beauty Center" que planea abrir más locales

**Flujo**:
1. **Paso 1**: Ingresa "Beauty Center", teléfono, email
2. **Paso 2**: Configura sucursal "Belgrano" (su ubicación actual)
3. Ve el mensaje: "¿Tienes múltiples sucursales? Por ahora crearemos solo la principal..."
4. Completa registro normalmente
5. **En el futuro**: Cuando agregue más sucursales, usará la UI multi-sucursal (feature pendiente)

**Resultado**:
- 1 CentroEstetica creado
- 1 Sucursal creada (puede agregar más después)
- Sistema preparado para escalar cuando se implemente UI multi-sucursal

### Caso 3: Error en registro (validación)

**Usuario**: Ana intenta registrarse con nombre ya existente

**Flujo**:
1. Ingresa nombre "Belleza Total" (ya existe en DB)
2. Sistema valida en tiempo real y muestra error
3. Ana cambia a "Belleza Total Spa"
4. Validación pasa, puede continuar

**Prevención**: Validación asíncrona al perder foco del campo nombre.

---

## Checklist de Implementación

### Backend
- [ ] Crear `apps/empleados/views_registro.py`
- [ ] Crear `apps/empleados/serializers_registro.py`
- [ ] Crear `apps/empleados/validators.py`
- [ ] Agregar endpoint `/api/registro/validar-nombre-centro/`
- [ ] Agregar endpoint `/api/registro/validar-email/`
- [ ] Agregar endpoint `/api/registro/crear-cuenta/` (transacción atómica)
- [ ] Implementar creación automática de categorías financieras del sistema
- [ ] Agregar rate limiting (5 intentos/hora por IP)
- [ ] Tests unitarios para validaciones
- [ ] Tests de integración para flujo completo
- [ ] Documentación de API (Swagger/OpenAPI)

### Frontend
- [ ] Crear `pages/RegistroPage.tsx`
- [ ] Crear `components/registro/PasoUno.tsx`
- [ ] Crear `components/registro/PasoDos.tsx`
- [ ] Crear `components/registro/PasoTres.tsx`
- [ ] Crear `components/registro/Confirmacion.tsx`
- [ ] Crear `components/registro/ProgressIndicator.tsx`
- [ ] Crear `components/registro/SucursalForm.tsx`
- [ ] Crear `services/registro.ts`
- [ ] Implementar validación en tiempo real (debounced)
- [ ] Implementar guardado en localStorage (no perder progreso)
- [ ] Agregar ruta `/registro` en React Router
- [ ] Agregar link "Registrarse" en página de login
- [ ] Tests con React Testing Library

### UI/UX
- [ ] Diseño de wireframes para 3 pasos
- [ ] Diseño de pantalla de confirmación
- [ ] Iconografía y assets visuales
- [ ] Mensajes de error amigables
- [ ] Animaciones de transición entre pasos
- [ ] Indicador de fortaleza de contraseña
- [ ] Responsive design (mobile, tablet, desktop)

### Seguridad
- [ ] Implementar reCAPTCHA v3
- [ ] Rate limiting en endpoints de registro
- [ ] Validación de CUIT (dígito verificador)
- [ ] Logs de auditoría para intentos de registro
- [ ] Blacklist de palabras ofensivas en nombres
- [ ] Sanitización de inputs (prevenir XSS)

### Documentación
- [ ] Documentar flujo de registro en README
- [ ] Guía para usuarios: "Cómo registrarse"
- [ ] Documentación técnica de API
- [ ] Diagrama de flujo (UX)
- [ ] Diagrama de arquitectura (BD)

---

## Métricas de Éxito

**KPIs a medir después del lanzamiento**:

1. **Tasa de Conversión de Registro**
   - Objetivo: >60% de usuarios que inician el registro lo completan
   - Medir: visitantes en `/registro` vs cuentas creadas

2. **Tiempo Promedio de Registro**
   - Objetivo: <5 minutos desde inicio hasta dashboard
   - Medir: timestamp inicio vs timestamp de cuenta creada

3. **Tasa de Abandono por Paso**
   - Identificar en qué paso los usuarios abandonan
   - Paso 1 (Centro): <10% abandono
   - Paso 2 (Sucursales): <15% abandono
   - Paso 3 (Admin): <5% abandono

4. **Errores de Validación**
   - Objetivo: <2 errores promedio por registro
   - Identificar campos problemáticos

5. **Registros por Día**
   - Objetivo inicial: 5-10 registros/día (primeros meses)
   - Crecimiento objetivo: 20% mensual

6. **Calidad de Datos**
   - % de registros con datos completos (incluyendo opcionales)
   - % de emails verificados (si se implementa)

---

## Términos y Condiciones / Política de Privacidad

### Contenido Mínimo Requerido

**Términos y Condiciones** deben incluir:
- Definición del servicio SaaS ofrecido
- Responsabilidades del usuario (datos de clientes, cumplimiento legal)
- Responsabilidades de la plataforma (uptime, soporte, seguridad)
- Política de pagos y facturación (cuando se implemente)
- Derecho a suspender cuentas (uso indebido, no pago)
- Limitación de responsabilidad
- Jurisdicción aplicable (Argentina)

**Política de Privacidad** debe incluir:
- Tipos de datos recopilados (centro, sucursales, admin, clientes finales)
- Uso de datos (operación del servicio, mejoras, analytics)
- Compartir datos con terceros (solo para WhatsApp API, procesadores de pago)
- Seguridad de datos (encriptación, backups)
- Derechos del usuario (acceso, rectificación, eliminación - GDPR/PDPA)
- Cookies y tracking (Google Analytics)
- Contacto para consultas de privacidad

**Ubicación**:
- Backend: `backend/static/legal/terminos.md` y `privacidad.md`
- Frontend: Páginas `/terminos` y `/privacidad` con markdown renderizado

---

## Notas Finales

Este sistema de registro es la **puerta de entrada** a la plataforma. Debe ser:

✅ **Rápido**: <5 minutos para completar
✅ **Claro**: Sin ambigüedades, instrucciones simples
✅ **Confiable**: Validaciones robustas, transacciones atómicas
✅ **Seguro**: Rate limiting, CAPTCHA, encriptación
✅ **Amigable**: Errores claros, ayuda contextual

**Prioridad de implementación**: ALTA - Bloqueante para lanzamiento público.

**Estimación de desarrollo**:
- Backend: 2-3 días (validaciones, endpoints, tests)
- Frontend: 3-4 días (3 pasos, validaciones, UX)
- Integración y testing: 1-2 días
- **Total**: 6-9 días de desarrollo (simplificado vs. original)

**Dependencias**:
- Ninguna - puede implementarse independientemente de otras features

**Siguiente paso después de implementar**:
- Tutorial de onboarding guiado para nuevos usuarios
- Importación de datos desde Excel (clientes, servicios)
