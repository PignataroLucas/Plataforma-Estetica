# Arquitectura de White-Labeling y Personalización

## Estrategia General

**Filosofía:** La **Admin App** es una herramienta interna genérica (como Shopify Admin), mientras que la **Client App** es 100% personalizable y representa la identidad visual de cada centro de estética.

---

## Admin App (Panel de Gestión Interna)

### Personalización Mínima

**Solo 2 elementos personalizables:**

1. **Logo del centro**
   - Se muestra en el header
   - Reemplaza logo genérico de la plataforma

2. **Dominio/Subdominio**
   - Para acceso personalizado (ej: `micentro.admin.plataforma.com`)
   - Opcional: puede usar dominio compartido

**Todo lo demás es genérico:**
- ✅ Colores: Paleta azul estándar (fija para todos)
- ✅ Fuentes: Inter (fija para todos)
- ✅ Layout: Idéntico para todos los centros
- ✅ Componentes UI: Mismos estilos
- ✅ Branding: Logo de la plataforma en login

### Razones

- **Mantenibilidad:** Un solo diseño para mantener
- **Consistencia:** Updates uniformes para todos
- **Velocidad:** No hay overhead de theming
- **Foco:** La admin es herramienta, no cara pública
- **Ejemplos exitosos:** Shopify, Tiendanube, Square usan este modelo

### Implementación Admin

```python
# backend/apps/empleados/models.py
class CentroEstetica(models.Model):
    # ... campos existentes ...

    # Personalización Admin (mínima)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)  # ✅ Ya existe
    subdominio_admin = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        help_text="ej: micentro → micentro.admin.plataforma.com"
    )
```

```typescript
// frontend/src/components/Header.tsx
export default function Header() {
  const { user } = useAuthStore()
  const centro = user?.centro_estetica

  return (
    <header>
      {/* Logo del centro o logo genérico */}
      {centro?.logo ? (
        <img src={centro.logo} alt={centro.nombre} />
      ) : (
        <img src="/logo-plataforma.svg" alt="Plataforma Estética" />
      )}

      <span>{centro?.nombre}</span>
      {/* Resto del header genérico */}
    </header>
  )
}
```

---

## Client App (Portal de Clientes) - 100% White-Label

### Personalización Completa

**Todo es personalizable:**

1. **Identidad Visual**
   - Paleta de colores completa
   - Logos (principal, dark mode, favicon)
   - Fuentes/tipografías
   - Estilos (border radius, sombras, etc.)

2. **Contenido**
   - Textos y copys
   - Imágenes y banners
   - Mensajes de WhatsApp
   - Políticas y términos

3. **Dominio**
   - Dominio propio (`www.micentro.com`)
   - O subdominio (`micentro.plataforma.com`)

4. **Integraciones**
   - Google Analytics propio
   - Facebook Pixel
   - Chatbots
   - Scripts custom

5. **SEO**
   - Meta tags personalizados
   - Open Graph images
   - Sitemap propio

### Modelo de Datos

```python
# backend/apps/branding/models.py

from django.db import models
from apps.empleados.models import CentroEstetica


class ConfiguracionVisual(models.Model):
    """
    Configuración visual completa para Client App
    100% white-label - cada centro tiene su identidad única
    """
    centro_estetica = models.OneToOneField(
        CentroEstetica,
        on_delete=models.CASCADE,
        related_name='config_visual'
    )

    # === COLORES ===
    # Paleta principal
    color_primario = models.CharField(
        max_length=7,
        default='#0ea5e9',
        help_text="Color principal de la marca (botones, links, highlights)"
    )
    color_secundario = models.CharField(
        max_length=7,
        default='#64748b',
        help_text="Color secundario complementario"
    )
    color_acento = models.CharField(
        max_length=7,
        default='#f59e0b',
        help_text="Color de acento para CTAs importantes"
    )

    # Colores de fondo
    color_fondo = models.CharField(
        max_length=7,
        default='#ffffff',
        help_text="Color de fondo principal"
    )
    color_fondo_secundario = models.CharField(
        max_length=7,
        default='#f9fafb',
        help_text="Color de fondo para secciones alternadas"
    )

    # Colores de texto
    color_texto_principal = models.CharField(
        max_length=7,
        default='#1f2937',
        help_text="Color de texto principal"
    )
    color_texto_secundario = models.CharField(
        max_length=7,
        default='#6b7280',
        help_text="Color de texto secundario/descripción"
    )

    # Estados
    color_success = models.CharField(max_length=7, default='#10b981')
    color_warning = models.CharField(max_length=7, default='#f59e0b')
    color_error = models.CharField(max_length=7, default='#ef4444')
    color_info = models.CharField(max_length=7, default='#3b82f6')

    # === TIPOGRAFÍA ===
    fuente_principal = models.CharField(
        max_length=50,
        default='Inter',
        choices=[
            ('Inter', 'Inter'),
            ('Poppins', 'Poppins'),
            ('Roboto', 'Roboto'),
            ('Montserrat', 'Montserrat'),
            ('Open Sans', 'Open Sans'),
            ('Lato', 'Lato'),
            ('Raleway', 'Raleway'),
            ('Nunito', 'Nunito'),
        ],
        help_text="Fuente para textos generales"
    )
    fuente_headings = models.CharField(
        max_length=50,
        default='Inter',
        choices=[
            ('Inter', 'Inter'),
            ('Poppins', 'Poppins'),
            ('Roboto', 'Roboto'),
            ('Montserrat', 'Montserrat'),
            ('Playfair Display', 'Playfair Display'),
            ('Merriweather', 'Merriweather'),
        ],
        help_text="Fuente para títulos y headings"
    )

    # === LOGOS E IMÁGENES ===
    logo_principal = models.ImageField(
        upload_to='branding/logos/',
        help_text="Logo principal (para fondo claro)"
    )
    logo_dark = models.ImageField(
        upload_to='branding/logos/',
        null=True,
        blank=True,
        help_text="Logo para modo oscuro (opcional)"
    )
    logo_favicon = models.ImageField(
        upload_to='branding/favicons/',
        null=True,
        blank=True,
        help_text="Favicon 32x32 o 64x64"
    )
    logo_og_image = models.ImageField(
        upload_to='branding/og-images/',
        null=True,
        blank=True,
        help_text="Imagen para compartir en redes (1200x630)"
    )

    # Hero/Banner
    banner_hero = models.ImageField(
        upload_to='branding/banners/',
        null=True,
        blank=True,
        help_text="Imagen hero de la homepage"
    )

    # === ESTILOS ===
    border_radius = models.CharField(
        max_length=20,
        default='0.5rem',
        choices=[
            ('0', 'Cuadrado (0px)'),
            ('0.25rem', 'Sutilmente redondeado (4px)'),
            ('0.5rem', 'Redondeado (8px)'),
            ('0.75rem', 'Muy redondeado (12px)'),
            ('1rem', 'Extra redondeado (16px)'),
            ('9999px', 'Píldora (completamente redondeado)'),
        ],
        help_text="Radio de borde para botones, cards, etc."
    )

    estilo_sombras = models.CharField(
        max_length=20,
        default='medium',
        choices=[
            ('none', 'Sin sombras'),
            ('subtle', 'Sombras sutiles'),
            ('medium', 'Sombras medias'),
            ('strong', 'Sombras pronunciadas'),
        ]
    )

    # === CONTENIDO TEXTUAL ===
    nombre_comercial = models.CharField(
        max_length=100,
        help_text="Nombre que aparece en el sitio web"
    )
    eslogan = models.CharField(
        max_length=200,
        blank=True,
        help_text="Tagline o eslogan del centro"
    )
    descripcion_corta = models.TextField(
        max_length=300,
        blank=True,
        help_text="Descripción breve del centro (para homepage)"
    )
    descripcion_larga = models.TextField(
        blank=True,
        help_text="Descripción extendida (sobre nosotros)"
    )

    # === DOMINIO Y SEO ===
    dominio_personalizado = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        help_text="ej: www.micentro.com o reservas.micentro.com"
    )
    subdominio = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        help_text="ej: micentro → micentro.plataforma.com"
    )

    # SEO
    meta_titulo = models.CharField(
        max_length=60,
        blank=True,
        help_text="Título SEO (aparece en Google)"
    )
    meta_descripcion = models.TextField(
        max_length=160,
        blank=True,
        help_text="Descripción SEO"
    )
    meta_keywords = models.CharField(
        max_length=200,
        blank=True,
        help_text="Keywords separadas por comas"
    )

    # === INTEGRACIONES ===
    google_analytics_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="ej: G-XXXXXXXXXX"
    )
    facebook_pixel_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="ID de Facebook Pixel"
    )
    google_tag_manager_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="ej: GTM-XXXXXXX"
    )

    # Widgets
    whatsapp_widget_activo = models.BooleanField(
        default=True,
        help_text="Mostrar botón flotante de WhatsApp"
    )
    whatsapp_numero = models.CharField(
        max_length=20,
        blank=True,
        help_text="Número para el widget (sin + ni espacios)"
    )
    whatsapp_mensaje_default = models.CharField(
        max_length=200,
        default="Hola! Quisiera consultar sobre...",
        help_text="Mensaje predefinido al abrir WhatsApp"
    )

    # === PERSONALIZACIÓN AVANZADA ===
    css_custom = models.TextField(
        blank=True,
        help_text="CSS personalizado adicional (para usuarios avanzados)"
    )

    head_scripts = models.TextField(
        blank=True,
        help_text="Scripts para <head> (analytics, etc.)"
    )
    body_scripts = models.TextField(
        blank=True,
        help_text="Scripts antes de </body> (chatbots, etc.)"
    )

    # === CONFIGURACIÓN DE FUNCIONALIDADES ===
    mostrar_precios = models.BooleanField(
        default=True,
        help_text="Mostrar precios de servicios públicamente"
    )
    permitir_reservas_online = models.BooleanField(
        default=True,
        help_text="Permitir que clientes reserven turnos online"
    )
    permitir_compra_productos = models.BooleanField(
        default=True,
        help_text="Activar e-commerce de productos"
    )
    mostrar_profesionales = models.BooleanField(
        default=True,
        help_text="Mostrar fotos y perfiles de profesionales"
    )

    # === HORARIOS Y CONTACTO (para footer) ===
    horario_atencion = models.TextField(
        blank=True,
        help_text="ej: Lun-Vie: 9-20hs, Sáb: 9-14hs"
    )
    email_contacto = models.EmailField(blank=True)
    telefono_contacto = models.CharField(max_length=20, blank=True)
    direccion_completa = models.TextField(blank=True)
    mapa_embed_url = models.URLField(
        blank=True,
        help_text="URL de embed de Google Maps"
    )

    # === REDES SOCIALES ===
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)

    # === POLÍTICAS Y LEGALES ===
    terminos_condiciones = models.TextField(
        blank=True,
        help_text="Términos y condiciones del servicio"
    )
    politica_privacidad = models.TextField(
        blank=True,
        help_text="Política de privacidad y tratamiento de datos"
    )
    politica_cancelacion = models.TextField(
        blank=True,
        help_text="Política de cancelación de turnos"
    )

    # === METADATA ===
    activo = models.BooleanField(
        default=True,
        help_text="Si está inactivo, el sitio cliente no se muestra"
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración Visual'
        verbose_name_plural = 'Configuraciones Visuales'

    def __str__(self):
        return f"Config Visual - {self.centro_estetica.nombre}"

    @property
    def url_sitio(self):
        """URL completa del sitio cliente"""
        if self.dominio_personalizado:
            return f"https://{self.dominio_personalizado}"
        elif self.subdominio:
            return f"https://{self.subdominio}.plataforma.com"
        return None

    def generar_paleta_colores(self):
        """
        Genera tonos derivados del color primario
        (50, 100, 200, ..., 900) para usar en Tailwind
        """
        # Implementar con librería de color manipulation
        # O precalcular en el admin
        pass


class PlantillaEmail(models.Model):
    """
    Plantillas de emails personalizadas por centro
    """
    centro_estetica = models.ForeignKey(
        CentroEstetica,
        on_delete=models.CASCADE,
        related_name='plantillas_email'
    )

    tipo = models.CharField(
        max_length=50,
        choices=[
            ('CONFIRMACION_TURNO', 'Confirmación de Turno'),
            ('RECORDATORIO_TURNO', 'Recordatorio de Turno'),
            ('CANCELACION_TURNO', 'Cancelación de Turno'),
            ('CONFIRMACION_PEDIDO', 'Confirmación de Pedido'),
            ('BIENVENIDA', 'Email de Bienvenida'),
            ('RECUPERAR_PASSWORD', 'Recuperar Contraseña'),
        ]
    )

    asunto = models.CharField(max_length=200)
    cuerpo_html = models.TextField(
        help_text="Contenido HTML del email (puede usar variables como {{nombre_cliente}})"
    )
    cuerpo_texto = models.TextField(
        blank=True,
        help_text="Versión texto plano (fallback)"
    )

    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = [['centro_estetica', 'tipo']]
        verbose_name = 'Plantilla de Email'
        verbose_name_plural = 'Plantillas de Emails'
```

---

## Arquitectura Frontend - Client App

### Sistema de Theming Dinámico

#### 1. Cargar Configuración al Iniciar

```typescript
// client-app/src/hooks/useBranding.ts
import { useEffect, useState } from 'react'
import { api } from '@/services/api'

interface BrandingConfig {
  colorPrimario: string
  colorSecundario: string
  colorAcento: string
  colorFondo: string
  colorTexto: string
  fuentePrincipal: string
  fuenteHeadings: string
  borderRadius: string
  logo: string
  nombreComercial: string
  eslogan: string
  // ... todos los campos
}

export const useBranding = () => {
  const [branding, setBranding] = useState<BrandingConfig | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadBranding = async () => {
      try {
        // Detectar tenant por dominio o parámetro
        const hostname = window.location.hostname

        const { data } = await api.get(`/api/public/branding/?domain=${hostname}`)

        // Aplicar theme globalmente
        applyTheme(data)
        setBranding(data)

        // Actualizar metadata del documento
        document.title = data.meta_titulo || data.nombre_comercial
        updateMetaTags(data)

        // Cargar fuentes de Google Fonts
        loadGoogleFonts(data.fuente_principal, data.fuente_headings)

      } catch (error) {
        console.error('Error cargando branding:', error)
      } finally {
        setLoading(false)
      }
    }

    loadBranding()
  }, [])

  return { branding, loading }
}

function applyTheme(config: BrandingConfig) {
  const root = document.documentElement

  // Aplicar CSS variables
  root.style.setProperty('--color-primary', config.colorPrimario)
  root.style.setProperty('--color-secondary', config.colorSecundario)
  root.style.setProperty('--color-accent', config.colorAcento)
  root.style.setProperty('--color-background', config.colorFondo)
  root.style.setProperty('--color-text', config.colorTexto)
  root.style.setProperty('--font-main', config.fuentePrincipal)
  root.style.setProperty('--font-heading', config.fuenteHeadings)
  root.style.setProperty('--border-radius', config.borderRadius)

  // Generar paleta de colores (tonos 50-900)
  const palette = generateColorPalette(config.colorPrimario)
  palette.forEach((color, index) => {
    const shade = (index + 1) * 100
    root.style.setProperty(`--color-primary-${shade}`, color)
  })
}

function updateMetaTags(config: BrandingConfig) {
  // Title
  document.title = config.meta_titulo || config.nombre_comercial

  // Meta description
  let metaDesc = document.querySelector('meta[name="description"]')
  if (!metaDesc) {
    metaDesc = document.createElement('meta')
    metaDesc.setAttribute('name', 'description')
    document.head.appendChild(metaDesc)
  }
  metaDesc.setAttribute('content', config.meta_descripcion)

  // Favicon
  let favicon = document.querySelector('link[rel="icon"]') as HTMLLinkElement
  if (!favicon) {
    favicon = document.createElement('link')
    favicon.rel = 'icon'
    document.head.appendChild(favicon)
  }
  favicon.href = config.logo_favicon || config.logo

  // Open Graph
  setMetaTag('og:title', config.meta_titulo)
  setMetaTag('og:description', config.meta_descripcion)
  setMetaTag('og:image', config.logo_og_image)

  // Twitter Card
  setMetaTag('twitter:card', 'summary_large_image')
  setMetaTag('twitter:title', config.meta_titulo)
  setMetaTag('twitter:description', config.meta_descripcion)
  setMetaTag('twitter:image', config.logo_og_image)
}

function setMetaTag(property: string, content: string) {
  if (!content) return

  let meta = document.querySelector(`meta[property="${property}"]`)
  if (!meta) {
    meta = document.createElement('meta')
    meta.setAttribute('property', property)
    document.head.appendChild(meta)
  }
  meta.setAttribute('content', content)
}

function loadGoogleFonts(...fonts: string[]) {
  const uniqueFonts = [...new Set(fonts)]
  const fontUrls = uniqueFonts.map(font =>
    `family=${font.replace(' ', '+')}:wght@300;400;500;600;700`
  ).join('&')

  const link = document.createElement('link')
  link.rel = 'stylesheet'
  link.href = `https://fonts.googleapis.com/css2?${fontUrls}&display=swap`
  document.head.appendChild(link)
}

function generateColorPalette(baseColor: string): string[] {
  // Usar librería como tinycolor2 o chroma.js
  // Para generar tonos 50, 100, 200, ..., 900
  // Placeholder:
  return [baseColor] // Implementar generación real
}
```

#### 2. Tailwind Config Dinámico

```typescript
// client-app/tailwind.config.ts
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'var(--color-primary)',
          50: 'var(--color-primary-50)',
          100: 'var(--color-primary-100)',
          200: 'var(--color-primary-200)',
          300: 'var(--color-primary-300)',
          400: 'var(--color-primary-400)',
          500: 'var(--color-primary)',
          600: 'var(--color-primary-600)',
          700: 'var(--color-primary-700)',
          800: 'var(--color-primary-800)',
          900: 'var(--color-primary-900)',
        },
        secondary: 'var(--color-secondary)',
        accent: 'var(--color-accent)',
        background: 'var(--color-background)',
        text: 'var(--color-text)',
      },
      fontFamily: {
        sans: ['var(--font-main)', 'system-ui', 'sans-serif'],
        heading: ['var(--font-heading)', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: 'var(--border-radius)',
        theme: 'var(--border-radius)',
      },
    },
  },
  plugins: [],
} satisfies Config
```

#### 3. App Principal

```typescript
// client-app/src/App.tsx
import { useBranding } from '@/hooks/useBranding'
import { BrandingProvider } from '@/contexts/BrandingContext'
import LoadingScreen from '@/components/LoadingScreen'

function App() {
  const { branding, loading } = useBranding()

  if (loading) {
    return <LoadingScreen />
  }

  if (!branding) {
    return <ErrorScreen message="Centro no encontrado" />
  }

  return (
    <BrandingProvider value={branding}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/servicios" element={<ServiciosPage />} />
        <Route path="/reservar" element={<ReservarPage />} />
        <Route path="/productos" element={<ProductosPage />} />
        <Route path="/contacto" element={<ContactoPage />} />
        {/* ... más rutas */}
      </Routes>

      {/* Widgets condicionales */}
      {branding.whatsapp_widget_activo && (
        <WhatsAppWidget
          numero={branding.whatsapp_numero}
          mensaje={branding.whatsapp_mensaje_default}
        />
      )}

      {/* Scripts de terceros */}
      <ThirdPartyScripts branding={branding} />
    </BrandingProvider>
  )
}
```

#### 4. Context para acceder al branding en cualquier componente

```typescript
// client-app/src/contexts/BrandingContext.tsx
import { createContext, useContext } from 'react'
import type { BrandingConfig } from '@/types/branding'

const BrandingContext = createContext<BrandingConfig | null>(null)

export const BrandingProvider = BrandingContext.Provider

export const useBrandingContext = () => {
  const context = useContext(BrandingContext)
  if (!context) {
    throw new Error('useBrandingContext must be used within BrandingProvider')
  }
  return context
}
```

---

## Multi-Tenant Routing (Backend)

### Middleware para detectar tenant por dominio

```python
# backend/middleware/tenant_middleware.py
from django.http import Http404
from apps.empleados.models import CentroEstetica

class TenantMiddleware:
    """
    Detecta el tenant (centro de estética) basado en el dominio/subdominio
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        hostname = request.get_host().split(':')[0]  # Remover puerto

        # Admin app - no requiere tenant
        if hostname.startswith('admin.') or hostname == 'localhost':
            request.tenant = None
            return self.get_response(request)

        # Buscar por dominio personalizado
        try:
            centro = CentroEstetica.objects.select_related('config_visual').get(
                config_visual__dominio_personalizado=hostname
            )
        except CentroEstetica.DoesNotExist:
            # Buscar por subdominio
            subdominio = hostname.split('.')[0]
            try:
                centro = CentroEstetica.objects.select_related('config_visual').get(
                    config_visual__subdominio=subdominio
                )
            except CentroEstetica.DoesNotExist:
                raise Http404("Centro de estética no encontrado")

        # Verificar que esté activo
        if not centro.activo or not centro.config_visual.activo:
            raise Http404("Este sitio no está disponible")

        # Adjuntar tenant al request
        request.tenant = centro

        return self.get_response(request)


# Agregar al settings.py
MIDDLEWARE = [
    # ...
    'middleware.tenant_middleware.TenantMiddleware',  # Después de SecurityMiddleware
    # ...
]
```

### API Endpoint para Client App

```python
# backend/apps/public_api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.branding.serializers import ConfiguracionVisualSerializer

class BrandingPublicView(APIView):
    """
    Endpoint público para obtener configuración visual
    No requiere autenticación
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # El tenant ya fue detectado por el middleware
        centro = request.tenant

        if not centro or not hasattr(centro, 'config_visual'):
            return Response(
                {"error": "Configuración no encontrada"},
                status=404
            )

        serializer = ConfiguracionVisualSerializer(centro.config_visual)
        return Response(serializer.data)
```

---

## Ejemplo de Uso en Componentes

```typescript
// client-app/src/components/Hero.tsx
import { useBrandingContext } from '@/contexts/BrandingContext'

export default function Hero() {
  const branding = useBrandingContext()

  return (
    <section
      className="relative h-screen bg-cover bg-center"
      style={{ backgroundImage: `url(${branding.banner_hero})` }}
    >
      <div className="absolute inset-0 bg-black/40" />

      <div className="relative z-10 flex flex-col items-center justify-center h-full text-white">
        <img
          src={branding.logo_principal}
          alt={branding.nombre_comercial}
          className="h-32 mb-6"
        />

        <h1 className="text-5xl font-heading font-bold mb-4">
          {branding.nombre_comercial}
        </h1>

        <p className="text-2xl mb-8 font-light">
          {branding.eslogan}
        </p>

        <button
          className="px-8 py-4 bg-primary text-white rounded-theme font-semibold
                     hover:opacity-90 transition-opacity"
        >
          Reservar Turno
        </button>
      </div>
    </section>
  )
}
```

---

## Deployment Multi-Dominio

### Nginx Configuration

```nginx
# Servidor para admin
server {
    server_name admin.plataforma.com;

    location / {
        proxy_pass http://frontend-admin:5173;
        proxy_set_header Host $host;
    }

    location /api/ {
        proxy_pass http://backend:8000;
    }
}

# Servidor para client apps (wildcard)
server {
    server_name *.plataforma.com;

    location / {
        proxy_pass http://client-app:5174;
        proxy_set_header Host $host;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
    }
}

# Dominios personalizados (se configuran dinámicamente)
server {
    server_name www.centrobelleza.com;

    location / {
        proxy_pass http://client-app:5174;
        proxy_set_header Host $host;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
    }
}
```

---

## Resumen

### Admin App
- ✅ Logo personalizado en header
- ✅ Subdominio opcional
- ❌ Colores/fuentes/estilos genéricos (fijos)
- 🎯 **Objetivo:** Herramienta interna eficiente y fácil de mantener

### Client App
- ✅ 100% white-label completo
- ✅ Paleta de colores personalizada
- ✅ Tipografías custom
- ✅ Logos, favicons, imágenes
- ✅ Dominio propio o subdominio
- ✅ SEO personalizado
- ✅ Integraciones de terceros
- ✅ CSS/Scripts custom
- 🎯 **Objetivo:** Cada centro tiene su identidad visual única

### Beneficios
1. **Escalabilidad:** Agregar nuevos centros es trivial
2. **Mantenibilidad:** Admin única, clients temáticos
3. **Competitividad:** Diferenciador clave vs competencia
4. **Adopción:** Centros ven "su marca", no una plataforma genérica
5. **Revenue:** Posibilidad de cobrar extra por diseño/branding premium

---

**Última actualización:** 17 de Noviembre 2025
**Estado:** Arquitectura definida - Pendiente implementación
