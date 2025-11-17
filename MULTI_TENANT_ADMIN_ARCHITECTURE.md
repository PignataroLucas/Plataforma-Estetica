# Arquitectura Multi-Tenant para Admin App

## Estrategia: Subdominios por Centro de Estética

### Estructura de Dominios

```
# Plataforma principal (landing, marketing)
www.plataforma.com

# Super Admin de la plataforma (gestiona centros)
platform.plataforma.com

# Admin de cada centro (subdominios dinámicos)
centro1.plataforma.com → Admin de Centro Belleza Total
centro2.plataforma.com → Admin de Centro Spa Relax
micentro.plataforma.com → Admin de Mi Centro

# Client Apps (para clientes finales)
centro1-app.plataforma.com → Portal clientes de Centro 1
www.micentrobeleza.com → Dominio propio del centro
```

### Ventajas de Subdominios

✅ **UX mejorada**: URL clara y profesional por centro
✅ **Seguridad**: Aislamiento claro de tenants
✅ **Branding**: Cada centro tiene "su espacio"
✅ **Cookies**: Sesiones separadas por subdominio
✅ **Escalabilidad**: Fácil de escalar con DNS
✅ **Onboarding**: Email con link directo al panel del centro

---

## Flujo de Onboarding (Creación de Nuevo Centro)

### Paso 1: Super Admin crea Centro

```
Super Admin accede a: platform.plataforma.com
    ↓
Crea nuevo CentroEstetica:
    - Nombre: "Belleza Total"
    - Subdominio: "belleza-total" → belleza-total.plataforma.com
    - Datos de contacto, ubicación, etc.
    ↓
Sistema automáticamente:
    1. Crea CentroEstetica en BD
    2. Crea Sucursal principal
    3. Crea Usuario ADMIN del centro
    4. Genera contraseña temporal
    5. Envía email con credenciales
```

### Paso 2: Admin del Centro recibe email

```
Asunto: Bienvenido a Plataforma Estética

Hola,

Tu cuenta de administración ha sido creada.

Accede a tu panel en:
https://belleza-total.plataforma.com

Credenciales:
Usuario: admin@bellezatotal.com
Contraseña temporal: Xyz123!@#

Por seguridad, cambia tu contraseña en el primer acceso.

Equipo Plataforma Estética
```

### Paso 3: Primer Login del Admin

```
Admin accede a: belleza-total.plataforma.com
    ↓
Ingresa credenciales temporales
    ↓
Sistema detecta first_login=True
    ↓
Fuerza cambio de contraseña
    ↓
Redirige a panel de administración
```

### Paso 4: Admin crea sus empleados

```
Admin ahora puede:
    1. Crear usuarios MANAGER
    2. Crear usuarios EMPLEADO
    3. Asignar sucursales
    4. Configurar permisos
    ↓
Sistema genera credenciales para cada empleado
    ↓
Admin puede:
    - Enviar email automático con credenciales
    - Copiar credenciales para enviar por WhatsApp
    - Imprimir credenciales
```

---

## Implementación Backend

### 1. Modificar Modelo CentroEstetica

```python
# backend/apps/empleados/models.py

class CentroEstetica(models.Model):
    # ... campos existentes ...

    # Subdominio para admin
    subdominio_admin = models.CharField(
        max_length=50,
        unique=True,
        help_text="ej: belleza-total → belleza-total.plataforma.com"
    )

    # Estado de activación
    activo = models.BooleanField(default=True)
    fecha_activacion = models.DateTimeField(null=True, blank=True)

    # Plan/Suscripción (para futuro)
    plan = models.CharField(
        max_length=20,
        choices=[
            ('TRIAL', 'Trial (30 días)'),
            ('BASICO', 'Básico'),
            ('PROFESIONAL', 'Profesional'),
            ('ENTERPRISE', 'Enterprise'),
        ],
        default='TRIAL'
    )
    fecha_vencimiento = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Centro Estética'
        verbose_name_plural = 'Centros de Estética'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @property
    def url_admin(self):
        """URL del panel de administración"""
        return f"https://{self.subdominio_admin}.plataforma.com"

    @property
    def esta_activo(self):
        """Verifica si el centro está activo y no vencido"""
        if not self.activo:
            return False
        if self.fecha_vencimiento and self.fecha_vencimiento < timezone.now().date():
            return False
        return True
```

### 2. Modificar Modelo Usuario

```python
# backend/apps/empleados/models.py

class Usuario(AbstractUser):
    # ... campos existentes ...

    # Control de primer acceso
    requiere_cambio_password = models.BooleanField(
        default=False,
        help_text="Usuario debe cambiar contraseña en primer login"
    )
    ultimo_cambio_password = models.DateTimeField(null=True, blank=True)

    # Metadata
    creado_por = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_creados',
        help_text="Usuario que creó esta cuenta"
    )
```

### 3. Middleware de Tenant (Detectar por subdominio)

```python
# backend/middleware/tenant_middleware.py

from django.http import JsonResponse
from django.utils import timezone
from apps.empleados.models import CentroEstetica

class TenantMiddleware:
    """
    Detecta el tenant (CentroEstetica) basado en el subdominio
    y valida que esté activo
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        hostname = request.get_host().split(':')[0]

        # Super admin platform (gestiona todos los centros)
        if hostname == 'platform.plataforma.com' or hostname == 'localhost':
            request.tenant = None
            request.is_platform_admin = True
            return self.get_response(request)

        # Extraer subdominio
        # belleza-total.plataforma.com → belleza-total
        parts = hostname.split('.')

        if len(parts) < 2:
            return JsonResponse(
                {'error': 'Dominio inválido'},
                status=400
            )

        subdominio = parts[0]

        # Buscar centro por subdominio
        try:
            centro = CentroEstetica.objects.get(
                subdominio_admin=subdominio
            )
        except CentroEstetica.DoesNotExist:
            return JsonResponse(
                {
                    'error': 'Centro no encontrado',
                    'message': f'El centro "{subdominio}" no existe.'
                },
                status=404
            )

        # Verificar que esté activo
        if not centro.esta_activo:
            return JsonResponse(
                {
                    'error': 'Centro inactivo',
                    'message': 'Este centro está temporalmente inactivo. Contacta a soporte.',
                    'contact': 'soporte@plataforma.com'
                },
                status=403
            )

        # Adjuntar tenant al request
        request.tenant = centro
        request.is_platform_admin = False

        return self.get_response(request)


# backend/config/settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'middleware.tenant_middleware.TenantMiddleware',  # ← Agregar aquí
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

### 4. Modificar Login para validar tenant

```python
# backend/apps/empleados/serializers.py

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado que valida tenant y retorna datos del usuario
    """

    def validate(self, attrs):
        # Autenticación estándar
        data = super().validate(attrs)

        # Obtener tenant del request (inyectado por middleware)
        request = self.context.get('request')
        tenant = getattr(request, 'tenant', None)
        is_platform_admin = getattr(request, 'is_platform_admin', False)

        # Si es platform admin, permitir acceso sin validación de tenant
        if is_platform_admin:
            user_serializer = UsuarioSerializer(self.user)
            data['user'] = user_serializer.data
            data['is_platform_admin'] = True
            return data

        # Validar que el usuario pertenezca al centro del subdominio
        if not tenant:
            raise serializers.ValidationError(
                "No se pudo determinar el centro de estética"
            )

        if self.user.centro_estetica_id != tenant.id:
            raise serializers.ValidationError(
                "Este usuario no tiene acceso a este centro"
            )

        # Verificar si requiere cambio de contraseña
        if self.user.requiere_cambio_password:
            data['requires_password_change'] = True

        # Agregar datos del usuario y centro
        user_serializer = UsuarioSerializer(self.user)
        data['user'] = user_serializer.data
        data['centro'] = {
            'id': tenant.id,
            'nombre': tenant.nombre,
            'logo': tenant.logo.url if tenant.logo else None,
            'subdominio': tenant.subdominio_admin
        }

        return data
```

### 5. App para Super Admin (Platform Admin)

```python
# backend/apps/platform_admin/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from apps.empleados.models import CentroEstetica, Usuario, Sucursal
from .serializers import CentroOnboardingSerializer

class CentroOnboardingViewSet(viewsets.ViewSet):
    """
    ViewSet para el proceso de onboarding de nuevos centros
    Solo accesible desde platform.plataforma.com por super admins
    """
    permission_classes = [IsAuthenticated]

    def create(self, request):
        """
        Crear un nuevo centro con su admin inicial
        """
        # Verificar que sea platform admin
        if not getattr(request, 'is_platform_admin', False):
            return Response(
                {'error': 'Solo super admins pueden crear centros'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CentroOnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Datos del centro
        nombre = serializer.validated_data['nombre']
        subdominio = serializer.validated_data['subdominio_admin']
        email_admin = serializer.validated_data['email_admin']
        nombre_admin = serializer.validated_data.get('nombre_admin', 'Admin')

        # Crear centro
        centro = CentroEstetica.objects.create(
            nombre=nombre,
            subdominio_admin=subdominio,
            email=email_admin,
            activo=True,
            plan='TRIAL',
            # ... otros campos
        )

        # Crear sucursal principal
        sucursal = Sucursal.objects.create(
            centro_estetica=centro,
            nombre='Principal',
            es_principal=True,
            direccion=serializer.validated_data.get('direccion', ''),
            ciudad=serializer.validated_data.get('ciudad', ''),
            provincia=serializer.validated_data.get('provincia', ''),
            telefono=serializer.validated_data.get('telefono', ''),
        )

        # Generar contraseña temporal
        password_temporal = get_random_string(12)

        # Crear usuario admin del centro
        admin = Usuario.objects.create_user(
            username=email_admin,
            email=email_admin,
            password=password_temporal,
            first_name=nombre_admin,
            centro_estetica=centro,
            sucursal=sucursal,
            rol='ADMIN',
            activo=True,
            requiere_cambio_password=True,  # Forzar cambio
            creado_por=request.user
        )

        # Enviar email con credenciales
        self._enviar_email_bienvenida(
            centro=centro,
            admin=admin,
            password_temporal=password_temporal
        )

        return Response({
            'message': 'Centro creado exitosamente',
            'centro': {
                'id': centro.id,
                'nombre': centro.nombre,
                'url_admin': centro.url_admin,
            },
            'admin': {
                'email': admin.email,
                'username': admin.username,
            },
            'credenciales_enviadas': True
        }, status=status.HTTP_201_CREATED)

    def _enviar_email_bienvenida(self, centro, admin, password_temporal):
        """Enviar email de bienvenida con credenciales"""
        subject = f'Bienvenido a Plataforma Estética - {centro.nombre}'

        message = f"""
Hola {admin.first_name},

Tu cuenta de administración ha sido creada exitosamente.

DATOS DE ACCESO:
-----------------
URL: {centro.url_admin}
Usuario: {admin.username}
Contraseña temporal: {password_temporal}

IMPORTANTE: Por seguridad, deberás cambiar tu contraseña en el primer acceso.

¿Qué puedes hacer ahora?
• Configurar tu centro (servicios, profesionales, horarios)
• Crear cuentas para tus empleados
• Comenzar a gestionar turnos y clientes

Si tienes dudas, visita nuestra documentación o contacta a soporte.

¡Bienvenido a Plataforma Estética!

Equipo Plataforma Estética
soporte@plataforma.com
        """

        send_mail(
            subject=subject,
            message=message,
            from_email='noreply@plataforma.com',
            recipient_list=[admin.email],
            fail_silently=False,
        )
```

### 6. Endpoint para cambio de contraseña

```python
# backend/apps/empleados/views.py

class UsuarioViewSet(viewsets.ModelViewSet):
    # ... código existente ...

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def cambiar_password(self, request):
        """
        Cambiar contraseña del usuario actual
        """
        usuario = request.user
        password_actual = request.data.get('password_actual')
        password_nueva = request.data.get('password_nueva')
        password_confirmacion = request.data.get('password_confirmacion')

        # Validaciones
        if not password_nueva or not password_confirmacion:
            return Response(
                {'error': 'Faltan campos requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if password_nueva != password_confirmacion:
            return Response(
                {'error': 'Las contraseñas no coinciden'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Si NO es primer cambio, validar contraseña actual
        if not usuario.requiere_cambio_password:
            if not password_actual or not usuario.check_password(password_actual):
                return Response(
                    {'error': 'Contraseña actual incorrecta'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Cambiar contraseña
        usuario.set_password(password_nueva)
        usuario.requiere_cambio_password = False
        usuario.ultimo_cambio_password = timezone.now()
        usuario.save()

        return Response({
            'message': 'Contraseña actualizada exitosamente'
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def generar_credenciales(self, request, pk=None):
        """
        Generar nuevas credenciales para un empleado
        (Resetear contraseña)
        """
        empleado = self.get_object()

        # Verificar que pertenece al mismo centro
        if empleado.centro_estetica_id != request.user.centro_estetica_id:
            return Response(
                {'error': 'No tienes permiso para modificar este usuario'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generar nueva contraseña
        nueva_password = get_random_string(12)
        empleado.set_password(nueva_password)
        empleado.requiere_cambio_password = True
        empleado.save()

        # Retornar credenciales para que admin las comunique
        return Response({
            'message': 'Credenciales generadas',
            'username': empleado.username,
            'password_temporal': nueva_password,
            'info': 'Comunica estas credenciales al empleado de forma segura'
        })
```

---

## Implementación Frontend

### 1. Detectar tenant y redirigir

```typescript
// frontend/src/App.tsx
import { useEffect } from 'react'
import { useAuthStore } from '@/stores/authStore'

function App() {
  const { isAuthenticated } = useAuthStore()

  useEffect(() => {
    // Detectar si estamos en el subdominio correcto
    const hostname = window.location.hostname

    // Si está en localhost, no hacer nada (desarrollo)
    if (hostname === 'localhost') return

    // Si no tiene subdominio, redirigir a www
    if (!hostname.includes('.plataforma.com')) {
      window.location.href = 'https://www.plataforma.com'
      return
    }

    // Validar que sea un subdominio válido
    // (el backend ya valida, pero podemos mostrar mensaje más amigable)
  }, [])

  return (
    // ... resto del App
  )
}
```

### 2. Login con validación de tenant

```typescript
// frontend/src/pages/LoginPage.tsx
export default function LoginPage() {
  // ... código existente ...

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (!validateForm()) return

    setLoading(true)

    try {
      const response = await api.post<LoginResponse>('/auth/login/', formData)
      const { access, refresh, user, requires_password_change, centro } = response.data

      setAuth(user, access, refresh, centro)

      // Si requiere cambio de contraseña, redirigir
      if (requires_password_change) {
        toast.info('Por seguridad, debes cambiar tu contraseña')
        navigate('/cambiar-password')
      } else {
        toast.success('Inicio de sesión exitoso')
        navigate('/')
      }

    } catch (error: any) {
      // Manejar errores específicos
      if (error.response?.status === 404) {
        toast.error('Centro no encontrado. Verifica la URL.')
      } else if (error.response?.status === 403) {
        toast.error('Este centro está inactivo. Contacta a soporte.')
      } else {
        toast.error('Usuario o contraseña incorrectos')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <Card>
        {/* Mostrar logo del centro si está disponible */}
        <CentroLogo />

        <h1>Iniciar Sesión</h1>
        <form onSubmit={handleSubmit}>
          {/* ... campos ... */}
        </form>
      </Card>
    </div>
  )
}
```

### 3. Página de cambio de contraseña obligatorio

```typescript
// frontend/src/pages/CambiarPasswordPage.tsx
export default function CambiarPasswordPage() {
  const [formData, setFormData] = useState({
    password_actual: '',
    password_nueva: '',
    password_confirmacion: ''
  })
  const navigate = useNavigate()
  const user = useAuthStore(state => state.user)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()

    try {
      await api.post('/api/empleados/cambiar_password/', formData)
      toast.success('Contraseña actualizada exitosamente')
      navigate('/')
    } catch (error) {
      toast.error('Error al cambiar contraseña')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <Card>
        <h1>Cambiar Contraseña</h1>
        <p className="text-gray-600 mb-6">
          Por seguridad, debes cambiar tu contraseña temporal
        </p>

        <form onSubmit={handleSubmit}>
          {!user?.requiere_cambio_password && (
            <Input
              label="Contraseña Actual"
              type="password"
              name="password_actual"
              value={formData.password_actual}
              onChange={handleChange}
              required
            />
          )}

          <Input
            label="Nueva Contraseña"
            type="password"
            name="password_nueva"
            value={formData.password_nueva}
            onChange={handleChange}
            required
          />

          <Input
            label="Confirmar Contraseña"
            type="password"
            name="password_confirmacion"
            value={formData.password_confirmacion}
            onChange={handleChange}
            required
          />

          <Button type="submit" fullWidth>
            Cambiar Contraseña
          </Button>
        </form>
      </Card>
    </div>
  )
}
```

### 4. Panel de Super Admin para crear centros

```typescript
// platform-admin/src/pages/CrearCentroPage.tsx
export default function CrearCentroPage() {
  const [formData, setFormData] = useState({
    nombre: '',
    subdominio_admin: '',
    email_admin: '',
    nombre_admin: '',
    telefono: '',
    direccion: '',
    ciudad: '',
    provincia: ''
  })

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()

    try {
      const response = await api.post('/api/platform/onboarding/', formData)

      toast.success(`Centro "${response.data.centro.nombre}" creado exitosamente`)

      // Mostrar modal con credenciales
      setModalCredenciales({
        url: response.data.centro.url_admin,
        username: response.data.admin.username,
        mensaje: 'Se ha enviado un email al administrador con sus credenciales'
      })

    } catch (error) {
      toast.error('Error al crear centro')
    }
  }

  return (
    <div>
      <h1>Crear Nuevo Centro de Estética</h1>

      <form onSubmit={handleSubmit}>
        <Input
          label="Nombre del Centro"
          name="nombre"
          value={formData.nombre}
          onChange={handleChange}
          required
        />

        <Input
          label="Subdominio Admin"
          name="subdominio_admin"
          value={formData.subdominio_admin}
          onChange={handleChange}
          helperText="Solo letras minúsculas y guiones. Ej: belleza-total"
          required
        />
        <span className="text-sm text-gray-500">
          → {formData.subdominio_admin || 'subdominio'}.plataforma.com
        </span>

        <Input
          label="Email del Administrador"
          type="email"
          name="email_admin"
          value={formData.email_admin}
          onChange={handleChange}
          required
        />

        <Input
          label="Nombre del Administrador"
          name="nombre_admin"
          value={formData.nombre_admin}
          onChange={handleChange}
        />

        {/* Más campos... */}

        <Button type="submit">
          Crear Centro
        </Button>
      </form>
    </div>
  )
}
```

---

## Configuración DNS

### Wildcard DNS para subdominios

```
# Configuración DNS en tu proveedor (Cloudflare, Route53, etc.)

Tipo    Nombre              Valor                       TTL
A       plataforma.com      123.45.67.89               Auto
A       www                 123.45.67.89               Auto
A       platform            123.45.67.89               Auto
A       *                   123.45.67.89               Auto  ← Wildcard para subdominios
```

El wildcard `*` permite que cualquier subdominio apunte al mismo servidor:
- `centro1.plataforma.com` ✅
- `centro2.plataforma.com` ✅
- `cualquier-cosa.plataforma.com` ✅ (validado por backend)

---

## Resumen del Flujo Completo

### 1. Creación de Centro (Super Admin)
```
Super Admin → platform.plataforma.com
    ↓
Crea Centro "Belleza Total"
    ↓
Sistema crea:
    - CentroEstetica (subdominio: belleza-total)
    - Sucursal principal
    - Usuario ADMIN (email: admin@bellezatotal.com)
    ↓
Email enviado con:
    - URL: belleza-total.plataforma.com
    - Usuario: admin@bellezatotal.com
    - Password temporal: Xyz123!@#
```

### 2. Primer Login (Admin del Centro)
```
Admin → belleza-total.plataforma.com
    ↓
Ingresa credenciales temporales
    ↓
Backend valida:
    - Subdominio existe ✅
    - Centro activo ✅
    - Usuario pertenece a ese centro ✅
    ↓
Requiere cambio de contraseña
    ↓
Admin define nueva contraseña
    ↓
Redirige a Dashboard
```

### 3. Admin crea Empleados
```
Admin → Empleados → Crear Nuevo
    ↓
Ingresa datos del empleado
    ↓
Sistema:
    - Crea usuario con centro_estetica_id = centro actual
    - Genera contraseña temporal
    - Marca requiere_cambio_password = True
    ↓
Admin ve modal con credenciales
    ↓
Admin envía credenciales al empleado (email/WhatsApp)
```

### 4. Empleado hace Login
```
Empleado → belleza-total.plataforma.com
    ↓
Ingresa credenciales recibidas
    ↓
Obligado a cambiar contraseña
    ↓
Accede a su panel (con permisos según rol)
```

---

## Seguridad

### ✅ Protecciones Implementadas

1. **No hay registro público** - Solo admins crean usuarios
2. **Validación de tenant** - Usuario solo accede a su centro
3. **Contraseñas temporales** - Primer login fuerza cambio
4. **Subdominios únicos** - Un centro = un subdominio
5. **Centros activos** - Middleware valida activación
6. **Permisos por rol** - ADMIN/MANAGER crean, EMPLEADO solo consulta
7. **Audit trail** - `creado_por` registra quién creó cada usuario

### 🔐 Mejoras Futuras

- 2FA obligatorio para admins
- Expiración de passwords (90 días)
- Lockout tras N intentos fallidos
- Logs de acceso por usuario
- Notificación de logins desde IPs nuevas

---

**Última actualización:** 17 de Noviembre 2025
**Estado:** Arquitectura definida - Pendiente implementación
