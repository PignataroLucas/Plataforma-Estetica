# SISTEMA FINANCIERO - Especificación Técnica y Funcional
**Plataforma de Gestión para Centros de Estética**

Versión: 1.0
Fecha: 17 de Noviembre de 2025
Estado: Pendiente de Implementación

---

## 📋 ÍNDICE

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura de Datos](#arquitectura-de-datos)
3. [Sistema de Categorización Inteligente](#sistema-de-categorización-inteligente)
4. [Integración con Inventario](#integración-con-inventario)
5. [Funcionalidades Principales](#funcionalidades-principales)
6. [Interfaz de Usuario](#interfaz-de-usuario)
7. [Flujos de Trabajo](#flujos-de-trabajo)
8. [Validaciones y Reglas de Negocio](#validaciones-y-reglas-de-negocio)
9. [Seguridad y Control de Acceso](#seguridad-y-control-de-acceso)
10. [Analytics y Reportes](#analytics-y-reportes)
11. [Plan de Implementación](#plan-de-implementación)

---

## 1. RESUMEN EJECUTIVO

El Sistema Financiero es el módulo crítico para la gestión contable y financiera del centro de estética. Proporciona control total sobre ingresos, gastos, flujo de caja, y análisis de rentabilidad.

### Objetivos Principales

- ✅ **Control Total de Finanzas**: Registro completo de ingresos y gastos con categorización flexible
- ✅ **Cero Duplicación de Trabajo**: Integración automática con inventario para compras
- ✅ **Visibilidad en Tiempo Real**: Dashboard con flujo de caja, profit mensual, tendencias
- ✅ **Seguridad Máxima**: Acceso restringido solo a roles administrativos
- ✅ **Auditoría Completa**: Trazabilidad de cada transacción y modificación
- ✅ **Insights Accionables**: Proyecciones, comparativas, análisis de rentabilidad

### Diferenciadores Clave

1. **Sistema de Categorización Jerárquica**: Categorías principales → Subcategorías (ej: Alquileres > Local, Máquina, Equipamiento)
2. **Auto-registro desde Inventario**: Las compras de productos generan automáticamente transacciones financieras
3. **Inteligencia en Categorización**: Sugerencias automáticas basadas en descripción y historial
4. **Exportación Completa**: PDF y Excel para contadores y análisis externo

---

## 2. ARQUITECTURA DE DATOS

### 2.1 Modelo de Base de Datos

#### **CategoriaTransaccion** (Mejorado)

```python
class CategoriaTransaccion(models.Model):
    """
    Sistema jerárquico de categorías para organizar transacciones financieras.
    Soporta 2 niveles: Categoría Principal → Subcategoría
    """
    # Relaciones
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    categoria_padre = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategorias'
    )

    # Tipo
    class TipoCategoria(models.TextChoices):
        INGRESO = 'INGRESO', 'Ingreso'
        GASTO = 'GASTO', 'Gasto'

    tipo = models.CharField(max_length=10, choices=TipoCategoria.choices)

    # Información
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#3B82F6")  # Hex color
    icono = models.CharField(max_length=50, blank=True)  # Para UI

    # Configuración
    activa = models.BooleanField(default=True)
    es_categoria_sistema = models.BooleanField(
        default=False,
        help_text="Las categorías del sistema no pueden ser eliminadas"
    )
    orden = models.IntegerField(default=0)  # Para ordenar en UI

    # Timestamps
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='categorias_creadas'
    )

    class Meta:
        verbose_name = 'Categoría de Transacción'
        verbose_name_plural = 'Categorías de Transacciones'
        ordering = ['tipo', 'orden', 'nombre']
        unique_together = [['sucursal', 'nombre', 'tipo', 'categoria_padre']]
        indexes = [
            models.Index(fields=['sucursal', 'tipo', 'activa']),
        ]

    def __str__(self):
        if self.categoria_padre:
            return f"{self.categoria_padre.nombre} > {self.nombre}"
        return self.nombre

    @property
    def es_subcategoria(self):
        return self.categoria_padre is not None

    @property
    def ruta_completa(self):
        """Retorna ruta completa: Categoría > Subcategoría"""
        if self.categoria_padre:
            return f"{self.categoria_padre.nombre} > {self.nombre}"
        return self.nombre
```

#### **Transaccion** (Mejorado)

```python
class Transaccion(models.Model):
    """
    Registro de todas las transacciones financieras (ingresos y gastos).
    Integrado con inventario para auto-generación de gastos por compras.
    """

    class TipoTransaccion(models.TextChoices):
        # INGRESOS
        INGRESO_SERVICIO = 'INGRESO_SERVICIO', 'Ingreso por Servicio'
        INGRESO_PRODUCTO = 'INGRESO_PRODUCTO', 'Ingreso por Venta de Producto'
        INGRESO_OTRO = 'INGRESO_OTRO', 'Otro Ingreso'

        # GASTOS - Más genérico que antes
        GASTO = 'GASTO', 'Gasto'

    class MetodoPago(models.TextChoices):
        EFECTIVO = 'EFECTIVO', 'Efectivo'
        TRANSFERENCIA = 'TRANSFERENCIA', 'Transferencia'
        TARJETA_DEBITO = 'TARJETA_DEBITO', 'Tarjeta de Débito'
        TARJETA_CREDITO = 'TARJETA_CREDITO', 'Tarjeta de Crédito'
        MERCADOPAGO = 'MERCADOPAGO', 'MercadoPago'
        OTRO = 'OTRO', 'Otro'

    # Relaciones
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)

    # NUEVA: Categoría jerárquica
    categoria = models.ForeignKey(
        CategoriaTransaccion,
        on_delete=models.PROTECT,  # No se puede borrar categoría con transacciones
        related_name='transacciones',
        help_text="Categoría o subcategoría de la transacción"
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones'
    )

    # Relación con entidades de origen
    turno = models.ForeignKey(
        'turnos.Turno',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones'
    )
    producto = models.ForeignKey(
        'inventario.Producto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones'
    )

    # NUEVA: Relación con movimiento de inventario (para trazabilidad)
    movimiento_inventario = models.OneToOneField(
        'inventario.MovimientoInventario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transaccion_financiera'
    )

    # Información de la transacción
    tipo = models.CharField(
        max_length=20,
        choices=TipoTransaccion.choices,
        db_index=True
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto de la transacción (siempre positivo)"
    )
    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        default=MetodoPago.EFECTIVO
    )
    fecha = models.DateField(db_index=True)
    descripcion = models.CharField(max_length=300)
    notas = models.TextField(blank=True)

    # Comprobante
    numero_comprobante = models.CharField(max_length=50, blank=True)
    archivo_comprobante = models.FileField(
        upload_to='comprobantes/%Y/%m/',
        null=True,
        blank=True
    )

    # NUEVO: Campo para indicar si es auto-generada
    auto_generada = models.BooleanField(
        default=False,
        help_text="Si fue creada automáticamente (ej: desde inventario)"
    )

    # Auditoría
    registrado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transacciones_registradas'
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    editado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transacciones_editadas'
    )

    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        ordering = ['-fecha', '-creado_en']
        indexes = [
            models.Index(fields=['sucursal', 'fecha']),
            models.Index(fields=['sucursal', 'tipo', 'fecha']),
            models.Index(fields=['sucursal', 'categoria', 'fecha']),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - ${self.monto} - {self.fecha.strftime('%d/%m/%Y')}"

    @property
    def es_ingreso(self):
        return self.tipo.startswith('INGRESO_')

    @property
    def es_gasto(self):
        return self.tipo == 'GASTO'

    @property
    def monto_con_signo(self):
        """Retorna monto con signo para cálculos de balance"""
        return self.monto if self.es_ingreso else -self.monto

    @property
    def puede_editarse(self):
        """Verifica si la transacción puede editarse (< 30 días)"""
        from django.utils import timezone
        dias_antiguedad = (timezone.now().date() - self.fecha).days
        return dias_antiguedad <= 30

    @property
    def puede_eliminarse(self):
        """Transacciones auto-generadas no pueden eliminarse directamente"""
        return not self.auto_generada
```

#### **CuentaPorCobrar** (Existente - mantener)

```python
# Ya existe en el código actual - mantener sin cambios
class CuentaPorCobrar(models.Model):
    # ... código existente ...
    pass
```

### 2.2 Categorías Predefinidas del Sistema

Al crear una nueva sucursal, se generan automáticamente estas categorías:

```python
CATEGORIAS_SISTEMA = {
    'GASTO': {
        'Alquileres': {
            'color': '#EF4444',
            'subcategorias': ['Alquiler Local', 'Alquiler Máquina', 'Alquiler Equipamiento']
        },
        'Salarios y Cargas Sociales': {
            'color': '#F59E0B',
            'subcategorias': ['Sueldos Personal', 'Comisiones', 'Cargas Sociales', 'Aguinaldo']
        },
        'Insumos y Productos': {
            'color': '#8B5CF6',
            'subcategorias': ['Productos Tratamiento', 'Material Descartable', 'Productos Limpieza']
        },
        'Servicios': {
            'color': '#3B82F6',
            'subcategorias': ['Luz', 'Agua', 'Gas', 'Internet', 'Teléfono']
        },
        'Marketing y Publicidad': {
            'color': '#EC4899',
            'subcategorias': ['Publicidad Digital', 'Publicidad Tradicional', 'Eventos y Promociones']
        },
        'Mantenimiento': {
            'color': '#6366F1',
            'subcategorias': ['Mantenimiento Local', 'Mantenimiento Equipos', 'Reparaciones']
        },
        'Impuestos y Tasas': {
            'color': '#EF4444',
            'subcategorias': ['Impuestos Nacionales', 'Impuestos Provinciales', 'Tasas Municipales']
        },
        'Otros Gastos': {
            'color': '#6B7280',
            'subcategorias': []
        }
    },
    'INGRESO': {
        'Servicios': {
            'color': '#10B981',
            'subcategorias': []  # Se generan dinámicamente desde servicios ofrecidos
        },
        'Venta de Productos': {
            'color': '#059669',
            'subcategorias': []
        },
        'Otros Ingresos': {
            'color': '#6B7280',
            'subcategorias': []
        }
    }
}
```

---

## 3. SISTEMA DE CATEGORIZACIÓN INTELIGENTE

### 3.1 Características

**Jerarquía de 2 Niveles**
- Categoría Principal (ej: "Alquileres")
- Subcategoría (ej: "Alquiler Local", "Alquiler Máquina")

**Categorías Predefinidas + Personalizables**
- Set inicial de categorías del sistema (no eliminables)
- Posibilidad de crear categorías custom por sucursal
- Activar/desactivar categorías sin perderlas

**Inteligencia en Selección**
- Últimas categorías usadas al tope
- Autocompletado al escribir
- Sugerencias basadas en descripción (ML simple)

### 3.2 Reglas de Negocio

1. **Una transacción debe tener categoría obligatoriamente**
2. **Se puede usar categoría principal O subcategoría** (flexible)
3. **Las categorías del sistema no se pueden eliminar** (solo desactivar)
4. **Las categorías custom se pueden eliminar** si no tienen transacciones asociadas
5. **Cada sucursal puede tener sus propias categorías custom**

---

## 4. INTEGRACIÓN CON INVENTARIO

### 4.1 Flujo Auto-generación de Transacciones

```
┌─────────────────────────────────────────────────────────┐
│  COMPRA DE PRODUCTOS (MovimientoInventario)            │
│  - Tipo: ENTRADA                                        │
│  - Cantidad: 10 unidades                                │
│  - Costo Unitario: $500                                 │
│  - Producto: Crema Facial XYZ                           │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ Django Signal: post_save
                      ▼
┌─────────────────────────────────────────────────────────┐
│  AUTO-CREACIÓN DE TRANSACCIÓN FINANCIERA                │
│  - Tipo: GASTO                                          │
│  - Categoría: "Insumos y Productos > Productos Trat."   │
│  - Monto: $5,000 (10 × $500)                           │
│  - Descripción: "Compra de 10 UN de Crema Facial XYZ"  │
│  - auto_generada: True                                  │
│  - movimiento_inventario: FK al movimiento             │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Implementación Técnica

**Signal Handler:**

```python
# apps/inventario/signals.py

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import MovimientoInventario
from apps.finanzas.models import Transaccion, CategoriaTransaccion

@receiver(post_save, sender=MovimientoInventario)
def auto_crear_transaccion_desde_compra(sender, instance, created, **kwargs):
    """
    Cuando se crea un MovimientoInventario tipo ENTRADA con costo,
    automáticamente crear una transacción financiera de gasto.
    """
    if not created:
        return

    # Solo para ENTRADAs (compras) con costo
    if instance.tipo != 'ENTRADA' or not instance.costo_unitario:
        return

    # Evitar duplicados
    if hasattr(instance, 'transaccion_financiera') and instance.transaccion_financiera:
        return

    # Calcular monto total
    monto_total = instance.cantidad * instance.costo_unitario

    # Obtener o crear categoría de Insumos
    categoria_insumos = CategoriaTransaccion.objects.filter(
        sucursal=instance.producto.sucursal,
        nombre='Insumos y Productos',
        tipo='GASTO',
        categoria_padre__isnull=True
    ).first()

    if not categoria_insumos:
        # Crear categoría si no existe
        categoria_insumos = CategoriaTransaccion.objects.create(
            sucursal=instance.producto.sucursal,
            nombre='Insumos y Productos',
            tipo='GASTO',
            es_categoria_sistema=True,
            color='#8B5CF6'
        )

    # Intentar obtener subcategoría según tipo de producto
    subcategoria = None
    if instance.producto.tipo == 'INSUMO':
        subcategoria = CategoriaTransaccion.objects.filter(
            categoria_padre=categoria_insumos,
            nombre='Productos Tratamiento'
        ).first()

    # Usar subcategoría si existe, sino categoría principal
    categoria_final = subcategoria if subcategoria else categoria_insumos

    # Crear transacción
    transaccion = Transaccion.objects.create(
        sucursal=instance.producto.sucursal,
        categoria=categoria_final,
        tipo='GASTO',
        monto=monto_total,
        fecha=instance.creado_en.date(),
        descripcion=f"Compra de {instance.cantidad} {instance.producto.unidad_medida} de {instance.producto.nombre}",
        notas=instance.notas,
        producto=instance.producto,
        metodo_pago='EFECTIVO',  # Default, se puede editar después
        auto_generada=True,
        registrado_por=instance.usuario,
        movimiento_inventario=instance
    )

    print(f"✅ Transacción financiera creada automáticamente: {transaccion}")


@receiver(pre_delete, sender=MovimientoInventario)
def eliminar_transaccion_asociada(sender, instance, **kwargs):
    """
    Si se elimina un movimiento de inventario, eliminar también
    su transacción financiera asociada (si fue auto-generada).
    """
    if hasattr(instance, 'transaccion_financiera') and instance.transaccion_financiera:
        transaccion = instance.transaccion_financiera
        if transaccion.auto_generada:
            print(f"🗑️ Eliminando transacción auto-generada: {transaccion}")
            transaccion.delete()
```

**Registrar Signals:**

```python
# apps/inventario/apps.py

from django.apps import AppConfig

class InventarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.inventario'

    def ready(self):
        import apps.inventario.signals  # Importar para registrar signals
```

### 4.3 Casos Especiales

**¿Qué pasa si edito el costo de una compra?**
- Opción A: Actualizar la transacción asociada automáticamente
- Opción B: Bloquear edición de costos si ya tiene transacción (recomendado para auditoría)

**¿Qué pasa con ajustes de inventario?**
- Los ajustes (correcciones de stock) NO generan transacción financiera
- Solo las ENTRADAs con costo generan transacciones

**¿Qué pasa con ventas de productos?**
- Las ventas ya generan ingresos desde el módulo de Turnos/Ventas
- No duplicar lógica aquí

---

## 5. FUNCIONALIDADES PRINCIPALES

### 5.1 Registro de Transacciones

**Registro Manual de Gastos**
- Formulario completo con todos los campos
- Selección de categoría/subcategoría jerárquica
- Upload de comprobante (PDF, JPG, PNG)
- Validación de montos y fechas
- Autocompletado de descripción basado en histórico

**Registro Manual de Ingresos**
- Similar a gastos pero para ingresos
- Asociación opcional con cliente
- Métodos de pago

**Auto-registro desde Inventario**
- Compras de productos generan gastos automáticamente
- Transparente para el usuario
- Trazabilidad completa

### 5.2 Visualización Temporal

**Filtros de Período**
- Hoy
- Esta semana
- Este mes
- Mes pasado
- Trimestre actual
- Año actual
- Rango personalizado

**Agrupaciones**
- Por día (para análisis detallado)
- Por semana
- Por mes (default)
- Por año

### 5.3 Flujo de Caja en Tiempo Real

**Cálculo Automático**
```
Flujo de Caja = Σ Ingresos - Σ Gastos
```

**Visualización**
- Dashboard principal: Tarjeta con monto y tendencia
- Gráfico de línea temporal (evolución mensual)
- Proyección para fin de mes basada en tendencia

### 5.4 Profit Mensual

**Cálculo**
```
Profit Mensual = (Ingresos del Mes) - (Gastos del Mes)
Margen de Ganancia = (Profit / Ingresos) × 100
```

**Comparación**
- vs. Mes anterior
- vs. Mismo mes año pasado
- Promedio de últimos 6 meses

### 5.5 Proyecciones

**Basadas en Tendencias Históricas**
- Regresión lineal simple para ingresos y gastos
- Proyección de próximos 3 meses
- Escenarios: Optimista / Base / Pesimista

**Alertas Automáticas**
- Si proyección de flujo de caja es negativa
- Si gastos superan ingresos 2 meses consecutivos
- Si gasto en categoría supera X% del total

### 5.6 Comparativas

**Mes a Mes**
- Comparar cualquier mes con cualquier otro
- Visualización lado a lado
- Deltas absolutos y porcentuales

**Año a Año**
- Comparar mismo mes de diferentes años
- Identificar tendencias de crecimiento/decrecimiento

**Por Categoría**
- Evolución de gastos por categoría en el tiempo
- Identificar categorías que crecen más rápido

### 5.7 Control de Caja

**Registro por Método de Pago**
- Efectivo
- Transferencias
- Tarjetas (débito/crédito)
- MercadoPago
- Otros

**Conciliación**
- Total esperado vs. total real en caja
- Reporte de diferencias
- Cierre de caja diario/semanal

### 5.8 Cuentas por Cobrar

Ya implementado en modelo existente:
- Tracking de deudas de clientes
- Monto total, pagado, pendiente
- Fecha de vencimiento
- Alertas de deudas vencidas

### 5.9 Exportación de Reportes

**Formatos**
- PDF (para imprimir, enviar)
- Excel (para análisis detallado)
- CSV (para importar a otros sistemas)

**Reportes Disponibles**
- Libro de ingresos y gastos (completo)
- Reporte de flujo de caja mensual
- Reporte por categoría
- Reporte de cuentas por cobrar
- Balance general

---

## 6. INTERFAZ DE USUARIO

### 6.1 Página Principal de Finanzas

```
┌────────────────────────────────────────────────────────────────┐
│ 💰 Finanzas                    Noviembre 2025    [+ Registrar] │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  📊 RESUMEN DEL MES                                           │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐   │
│  │  Ingresos   │   Gastos    │   Balance   │  vs. Mes    │   │
│  │             │             │             │  Anterior   │   │
│  │  $125,000   │  -$78,500   │  +$46,500   │   +12.3%    │   │
│  │  ↗ +8.5%    │  ↘ -3.2%    │             │             │   │
│  └─────────────┴─────────────┴─────────────┴─────────────┘   │
│                                                                │
│  📈 FLUJO DE CAJA - Últimos 6 Meses                           │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  [Gráfico de líneas: Ingresos vs Gastos vs Balance]  │     │
│  │                                                       │     │
│  │   $150K                           ╱─╲                │     │
│  │   $100K              ╱─╲      ╱──╯   ╲──             │     │
│  │   $ 50K         ╱───╯   ╲────╯                       │     │
│  │   $  0K  ──────╯                                      │     │
│  │          Jun  Jul  Aug  Sep  Oct  Nov               │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  🔍 FILTROS                                                   │
│  [Este Mes ▾] [Todos los Tipos ▾] [Todas Categorías ▾]       │
│  [Todos Métodos ▾] [Buscar...]                [⚙ Avanzado]  │
│                                                                │
│  📋 TRANSACCIONES RECIENTES                                   │
│  ┌──────────────────────────────────────────────────────┐     │
│  │ Fecha    Tipo  Categoría         Descripción    Monto│     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ 16/11 ⬇️ Alquileres>Local  Alquiler nov    -$45,000 │📄  │
│  │ 15/11 ⬆️ Servicios         Facial completo +$12,500 │    │
│  │ 15/11 ⬇️ Servicios>Luz     Edenor nov       -$3,200 │📄  │
│  │ 14/11 ⬇️ Insumos>Productos Crema XYZ (10u) -$5,000  │📄  │
│  │ 14/11 ⬆️ Venta Productos   Shampoo x2       +$3,800 │    │
│  │ 13/11 ⬇️ Marketing>Digital Instagram Ads    -$8,000 │    │
│  │ 12/11 ⬆️ Servicios         Masajes x3      +$18,000 │    │
│  └──────────────────────────────────────────────────────┘     │
│  [← Anterior]  Página 1 de 23  [Siguiente →]                 │
│                                                                │
│  📊 GASTOS POR CATEGORÍA                                      │
│  ┌──────────────────────────────────────────────────────┐     │
│  │  [Gráfico de Torta]                                   │     │
│  │                                                       │     │
│  │    Alquileres: 35% ($27,475)                         │     │
│  │    Salarios: 30% ($23,550)                           │     │
│  │    Insumos: 15% ($11,775)                            │     │
│  │    Marketing: 10% ($7,850)                           │     │
│  │    Servicios: 7% ($5,495)                            │     │
│  │    Otros: 3% ($2,355)                                │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  💾 EXPORTAR                                                  │
│  [📄 PDF] [📊 Excel] [📋 CSV]                                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 6.2 Modal de Registro de Transacción

**Versión: Todo-en-Uno (Recomendado)**

```
┌─────────────────────────────────────────────────────────┐
│ ➕ Registrar Transacción                          [✕]  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ TIPO DE TRANSACCIÓN *                                   │
│ ◉ Gasto      ○ Ingreso                                 │
│                                                         │
│ ┌─────────────────────────────────────────────────┐    │
│ │ CATEGORÍA *                                      │    │
│ │ [Alquileres                               ▾]    │    │
│ │                                                  │    │
│ │ 🔍 Últimas usadas:                              │    │
│ │   • Alquileres > Local                          │    │
│ │   • Servicios > Luz                             │    │
│ │   • Insumos > Productos Tratamiento             │    │
│ └─────────────────────────────────────────────────┘    │
│                                                         │
│ SUBCATEGORÍA                                            │
│ [Alquiler Local                            ▾]          │
│                                                         │
│ MONTO *                                                 │
│ $ [45000.00]                                           │
│                                                         │
│ FECHA *                   MÉTODO DE PAGO *              │
│ [15/11/2025]             [Transferencia        ▾]     │
│                                                         │
│ DESCRIPCIÓN *                                           │
│ [Alquiler del local - Mes noviembre 2025]              │
│   💡 Sugerencia: "Alquiler Local Noviembre"            │
│                                                         │
│ NOTAS ADICIONALES                                       │
│ [_____________________________________________]         │
│                                                         │
│ 📎 COMPROBANTE (Opcional)                              │
│ [Subir archivo]  o  [📷 Tomar foto]                   │
│ Formatos: PDF, JPG, PNG (máx 5MB)                      │
│                                                         │
│ NÚMERO DE COMPROBANTE                                   │
│ [00001-00012345]                                       │
│                                                         │
│                                                         │
│                   [Cancelar]  [💾 Guardar]            │
└─────────────────────────────────────────────────────────┘
```

**Features de UX:**

1. **Autocompletado Inteligente**
   - Al escribir en descripción, sugiere categorías
   - Ejemplo: "luz" → sugiere "Servicios > Luz"
   - "alquiler maq" → sugiere "Alquileres > Alquiler Máquina"

2. **Últimas Categorías Usadas**
   - Top 5 categorías más usadas en los últimos 30 días
   - Acceso rápido con un click

3. **Validación en Tiempo Real**
   - Monto debe ser > 0
   - Fecha no puede ser > hoy (warning, no error)
   - Categoría obligatoria

4. **Drag & Drop para Comprobantes**
   - Arrastrar archivo directamente
   - Preview del archivo subido

### 6.3 Vista de Detalle de Transacción

```
┌─────────────────────────────────────────────────────────┐
│ 📄 Detalle de Transacción                         [✕]  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ TIPO                                                    │
│ ⬇️ GASTO                                                │
│                                                         │
│ CATEGORÍA                                               │
│ Alquileres > Alquiler Local                            │
│                                                         │
│ MONTO                                                   │
│ -$45,000.00                                            │
│                                                         │
│ MÉTODO DE PAGO                                          │
│ Transferencia                                           │
│                                                         │
│ FECHA                                                   │
│ 15 de Noviembre de 2025                                │
│                                                         │
│ DESCRIPCIÓN                                             │
│ Alquiler del local - Mes noviembre 2025               │
│                                                         │
│ NOTAS                                                   │
│ (sin notas)                                            │
│                                                         │
│ COMPROBANTE                                             │
│ 📄 recibo_alquiler_nov_2025.pdf                       │
│ [👁️ Ver] [⬇️ Descargar]                              │
│                                                         │
│ NÚMERO DE COMPROBANTE                                   │
│ 00001-00012345                                         │
│                                                         │
│ ─────────────────────────────────────────────────      │
│                                                         │
│ AUDITORÍA                                               │
│ Registrado por: Juan Pérez                             │
│ Fecha de registro: 15/11/2025 14:23                   │
│ Última edición: -                                      │
│ Auto-generada: No                                      │
│                                                         │
│                                                         │
│        [✏️ Editar]  [🗑️ Eliminar]  [Cerrar]          │
└─────────────────────────────────────────────────────────┘
```

### 6.4 Gestión de Categorías

```
┌─────────────────────────────────────────────────────────┐
│ 🏷️ Gestión de Categorías                          [✕]  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ [GASTOS] [INGRESOS]                    [+ Nueva]       │
│                                                         │
│ CATEGORÍAS DE GASTOS                                    │
│                                                         │
│ ▼ 📁 Alquileres                    [✏️] [🔄]          │
│   ├─ Alquiler Local                                    │
│   ├─ Alquiler Máquina                                  │
│   └─ Alquiler Equipamiento                             │
│                                                         │
│ ▼ 💰 Salarios y Cargas Sociales    [✏️] [🔄]          │
│   ├─ Sueldos Personal                                  │
│   ├─ Comisiones                                        │
│   ├─ Cargas Sociales                                   │
│   └─ Aguinaldo                                         │
│                                                         │
│ ▼ 📦 Insumos y Productos           [✏️] [🔄]          │
│   ├─ Productos Tratamiento                             │
│   ├─ Material Descartable                              │
│   └─ Productos Limpieza                                │
│                                                         │
│ ▶ 💡 Servicios                     [✏️] [🔄]          │
│                                                         │
│ ▶ 📣 Marketing y Publicidad        [✏️] [🔄]          │
│                                                         │
│ ▶ 🔧 Mantenimiento                 [✏️] [🔄]          │
│                                                         │
│ ▶ 📋 Impuestos y Tasas             [✏️] [🔄]          │
│                                                         │
│ ▶ 📌 Otros Gastos                  [✏️] [🔄]          │
│                                                         │
│ CATEGORÍAS PERSONALIZADAS                               │
│                                                         │
│ 🏷️ Uniformes Personal              [✏️] [🗑️]         │
│                                                         │
│                                                         │
│                              [Cerrar]                   │
└─────────────────────────────────────────────────────────┘
```

---

## 7. FLUJOS DE TRABAJO

### 7.1 Flujo: Registrar Gasto Manual

```
1. Usuario (Admin/Manager) hace click en "+ Registrar"
2. Se abre modal de registro
3. Selecciona tipo: GASTO
4. Selecciona categoría (ej: "Servicios")
5. Selecciona subcategoría (ej: "Luz")
   - O escribe en descripción y sistema sugiere
6. Ingresa monto: $3,200
7. Selecciona método de pago: Transferencia
8. Ingresa descripción: "Edenor - Noviembre 2025"
9. (Opcional) Sube comprobante PDF
10. Hace click en "Guardar"
11. Sistema valida datos
12. Se crea transacción en BD
13. Se cierra modal
14. Se actualiza lista de transacciones
15. Se recalcula dashboard (ingresos, gastos, balance)
```

### 7.2 Flujo: Compra de Producto (Auto-generación)

```
1. Usuario registra compra en Inventario:
   - Producto: Crema Facial XYZ
   - Cantidad: 10 unidades
   - Costo Unitario: $500
   - Proveedor: DistribuidorABC

2. Sistema guarda MovimientoInventario (tipo: ENTRADA)

3. Signal post_save se dispara automáticamente

4. Signal crea Transacción:
   - Tipo: GASTO
   - Categoría: "Insumos > Productos Tratamiento"
   - Monto: $5,000
   - Descripción: "Compra de 10 UN de Crema Facial XYZ"
   - auto_generada: True
   - movimiento_inventario: FK al movimiento

5. Usuario ve la transacción en Finanzas automáticamente
   - Puede ver el detalle
   - NO puede eliminarla (está vinculada a inventario)
   - Puede ver el enlace al movimiento de inventario

6. Si usuario elimina el MovimientoInventario:
   - Se elimina también la Transacción asociada (signal pre_delete)
```

### 7.3 Flujo: Ver Reportes y Exportar

```
1. Usuario (Admin) accede a página de Finanzas
2. Selecciona período: "Noviembre 2025"
3. Ve dashboard con resumen del mes
4. Hace click en "Exportar > PDF"
5. Sistema genera reporte en background (Celery task)
6. Se descarga PDF con:
   - Resumen ejecutivo
   - Listado completo de transacciones
   - Gráficos de categorías
   - Balance y flujo de caja
7. Puede compartir PDF con contador
```

### 7.4 Flujo: Crear Categoría Personalizada

```
1. Usuario (Admin) hace click en "⚙ Categorías"
2. Se abre modal de gestión de categorías
3. Hace click en "+ Nueva"
4. Completa:
   - Nombre: "Uniformes Personal"
   - Tipo: GASTO
   - Categoría padre: (ninguna) - es categoría principal
   - Color: #FF6B6B
5. Hace click en "Crear"
6. Nueva categoría aparece en la lista
7. Ahora está disponible al registrar transacciones
```

---

## 8. VALIDACIONES Y REGLAS DE NEGOCIO

### 8.1 Validaciones de Entrada

**Monto**
- ✅ Debe ser > 0
- ✅ Máximo 2 decimales
- ✅ Máximo $9,999,999.99

**Fecha**
- ⚠️ Warning si es futura (no bloquear - puede ser por adelantado)
- ⚠️ Warning si es > 30 días en el pasado (posible error)
- ✅ No puede ser anterior a fecha de apertura de la sucursal

**Categoría**
- ✅ Obligatoria para gastos
- ✅ Debe pertenecer a la misma sucursal
- ✅ Debe estar activa
- ✅ Tipo de categoría debe coincidir con tipo de transacción

**Descripción**
- ✅ Mínimo 5 caracteres
- ✅ Máximo 300 caracteres

**Comprobante**
- ✅ Formatos permitidos: PDF, JPG, JPEG, PNG
- ✅ Tamaño máximo: 5MB
- ✅ Sanitización de nombre de archivo

### 8.2 Reglas de Edición

**Transacciones Recientes (< 30 días)**
- ✅ Se pueden editar todos los campos
- ⚠️ Warning: "Estás editando una transacción del [fecha]"
- ✅ Se registra quién editó y cuándo

**Transacciones Antiguas (> 30 días)**
- ❌ NO se pueden editar
- ℹ️ Mensaje: "Esta transacción es antigua y no puede editarse. Contacte al administrador."
- ✅ Admin puede override con confirmación especial

**Transacciones Auto-generadas**
- ❌ NO se pueden editar directamente
- ❌ NO se pueden eliminar directamente
- ℹ️ Mensaje: "Esta transacción fue generada automáticamente. Edite el movimiento de inventario asociado."
- ✅ Se puede ver el enlace al movimiento de inventario

### 8.3 Reglas de Eliminación

**Transacciones Manuales**
- ✅ Se pueden eliminar si < 7 días
- ⚠️ Confirmación: "¿Está seguro de eliminar esta transacción?"
- ✅ Se registra en log de auditoría

**Transacciones Auto-generadas**
- ❌ NO se pueden eliminar
- ℹ️ Debe eliminarse el MovimientoInventario asociado

**Categorías**
- ❌ NO se pueden eliminar si tienen transacciones asociadas
- ✅ Se pueden desactivar
- ❌ Categorías del sistema NO se pueden eliminar (solo desactivar)

### 8.4 Reglas de Seguridad

**Acceso a Finanzas**
- ✅ Solo roles: Admin, Dueño
- ❌ Empleado Básico NO puede acceder
- ❌ Manager puede ver solo de su sucursal (sin editar)

**Modificación de Montos**
- ⚠️ Alerta en Slack/Email si se modifica transacción > $10,000
- ✅ Log de auditoría obligatorio

**Exportación**
- ✅ Solo Admin/Dueño
- ✅ Se registra cada exportación (quién, cuándo, qué período)

---

## 9. SEGURIDAD Y CONTROL DE ACCESO

### 9.1 Permisos por Rol

| Acción | Empleado Básico | Manager | Admin/Dueño |
|--------|----------------|---------|-------------|
| Ver Finanzas | ❌ | ⚠️ Solo lectura (su sucursal) | ✅ Completo |
| Registrar Transacción | ❌ | ❌ | ✅ |
| Editar Transacción | ❌ | ❌ | ✅ |
| Eliminar Transacción | ❌ | ❌ | ✅ |
| Ver Reportes | ❌ | ⚠️ Básicos | ✅ Completos |
| Exportar Datos | ❌ | ❌ | ✅ |
| Gestionar Categorías | ❌ | ❌ | ✅ |

### 9.2 Auditoría

**Log de Acciones Críticas**
- Creación de transacción
- Edición de transacción (campo modificado, valor anterior, valor nuevo)
- Eliminación de transacción
- Exportación de datos
- Acceso a página de finanzas

**Modelo de Auditoría:**

```python
class AuditoriaFinanzas(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    accion = models.CharField(max_length=50)  # CREATE, UPDATE, DELETE, EXPORT, ACCESS
    modelo = models.CharField(max_length=50)  # Transaccion, CategoriaTransaccion
    objeto_id = models.IntegerField(null=True)
    detalles = models.JSONField()  # Información detallada del cambio
    ip_address = models.GenericIPAddressField()
    fecha = models.DateTimeField(auto_now_add=True)
```

### 9.3 Alertas de Seguridad

**Notificar Admin si:**
- Se edita transacción > 30 días
- Se elimina transacción > $5,000
- Se accede a finanzas desde IP desconocida
- Se exportan datos fuera del horario laboral

---

## 10. ANALYTICS Y REPORTES

### 10.1 Dashboard Principal

**Métricas Clave (KPIs)**
1. **Ingresos del Mes**: Total + % vs mes anterior
2. **Gastos del Mes**: Total + % vs mes anterior
3. **Balance del Mes**: Total + % vs mes anterior
4. **Margen de Ganancia**: (Profit / Ingresos) × 100

**Gráficos**
1. **Flujo de Caja Temporal**: Línea de ingresos, gastos, balance (últimos 6 meses)
2. **Gastos por Categoría**: Torta con % y montos
3. **Ingresos por Fuente**: Torta (servicios vs productos vs otros)
4. **Evolución Mensual**: Barras comparativas

### 10.2 Reportes Predefinidos

**1. Libro de Ingresos y Gastos**
- Listado completo de transacciones del período
- Subtotales por categoría
- Total general

**2. Estado de Resultados (P&L)**
```
INGRESOS
  Servicios                    $85,000
  Venta de Productos           $40,000
  Otros Ingresos               $5,000
  ─────────────────────────────────────
  TOTAL INGRESOS               $130,000

GASTOS
  Alquileres                   -$27,475
  Salarios y Cargas Sociales   -$23,550
  Insumos y Productos          -$11,775
  Marketing y Publicidad       -$7,850
  Servicios                    -$5,495
  Otros                        -$2,355
  ─────────────────────────────────────
  TOTAL GASTOS                 -$78,500

GANANCIA NETA                  $51,500
MARGEN DE GANANCIA             39.62%
```

**3. Flujo de Caja Proyectado**
- Basado en tendencias históricas
- Próximos 3 meses
- Escenarios: Base, Optimista, Pesimista

**4. Análisis por Categoría**
- Evolución de cada categoría en el tiempo
- Top 5 categorías de gasto
- Categorías con mayor crecimiento

**5. Cuentas por Cobrar**
- Listado de clientes con deudas
- Montos pendientes
- Deudas vencidas

### 10.3 Exportación

**Formatos:**
- **PDF**: Diseño profesional con logo, gráficos, tablas
- **Excel**: Múltiples hojas (resumen, detalle, gráficos)
- **CSV**: Datos crudos para análisis

**Personalización:**
- Seleccionar período
- Filtrar por categorías
- Incluir/excluir gráficos
- Agregar notas personalizadas

---

## 11. PLAN DE IMPLEMENTACIÓN

### Fase 1: Modelos y Migración (2-3 días)

**Tareas:**
1. ✅ Crear modelo `CategoriaTransaccion` mejorado
2. ✅ Actualizar modelo `Transaccion` con nuevos campos
3. ✅ Crear función para generar categorías predefinidas
4. ✅ Crear migración de datos (si hay datos existentes)
5. ✅ Ejecutar migraciones
6. ✅ Poblar categorías del sistema

**Archivos:**
- `backend/apps/finanzas/models.py`
- `backend/apps/finanzas/migrations/000X_categorias_jerarquicas.py`
- `backend/apps/finanzas/management/commands/poblar_categorias.py`

### Fase 2: Integración con Inventario (2 días)

**Tareas:**
1. ✅ Actualizar modelo `MovimientoInventario`
2. ✅ Crear signals para auto-generación
3. ✅ Implementar lógica de vinculación
4. ✅ Testing de integración
5. ✅ Registrar signals en apps.py

**Archivos:**
- `backend/apps/inventario/models.py`
- `backend/apps/inventario/signals.py`
- `backend/apps/inventario/apps.py`
- `backend/apps/inventario/tests/test_signals.py`

### Fase 3: API Backend (3-4 días)

**Tareas:**
1. ✅ Serializers para modelos
2. ✅ ViewSets con permisos
3. ✅ Filtros avanzados (fecha, categoría, tipo, método pago)
4. ✅ Endpoints de estadísticas
5. ✅ Endpoint de exportación
6. ✅ Validaciones custom
7. ✅ Testing de API

**Endpoints:**
```
GET    /api/finanzas/transacciones/
POST   /api/finanzas/transacciones/
GET    /api/finanzas/transacciones/{id}/
PUT    /api/finanzas/transacciones/{id}/
DELETE /api/finanzas/transacciones/{id}/

GET    /api/finanzas/categorias/
POST   /api/finanzas/categorias/
GET    /api/finanzas/categorias/arbol/  # Vista jerárquica

GET    /api/finanzas/dashboard/         # KPIs y métricas
GET    /api/finanzas/flujo-caja/        # Temporal
GET    /api/finanzas/gastos-categoria/  # Breakdown
GET    /api/finanzas/proyecciones/      # Forecast

POST   /api/finanzas/exportar/          # PDF/Excel/CSV
```

**Archivos:**
- `backend/apps/finanzas/serializers.py`
- `backend/apps/finanzas/views.py`
- `backend/apps/finanzas/filters.py`
- `backend/apps/finanzas/permissions.py`
- `backend/apps/finanzas/urls.py`

### Fase 4: Frontend - Componentes Base (3 días)

**Tareas:**
1. ✅ Componente de selector de categorías jerárquico
2. ✅ Formulario de registro de transacción
3. ✅ Tabla de transacciones con filtros
4. ✅ Card de KPIs
5. ✅ Componente de gráficos (Chart.js)

**Archivos:**
- `frontend/src/components/finanzas/CategoriasSelector.tsx`
- `frontend/src/components/finanzas/TransaccionForm.tsx`
- `frontend/src/components/finanzas/TransaccionTable.tsx`
- `frontend/src/components/finanzas/KPICard.tsx`
- `frontend/src/components/finanzas/FlujoCajaChart.tsx`

### Fase 5: Frontend - Página Principal (3 días)

**Tareas:**
1. ✅ Página principal de Finanzas
2. ✅ Dashboard con KPIs
3. ✅ Gráficos de flujo de caja
4. ✅ Gráfico de gastos por categoría
5. ✅ Listado de transacciones con paginación
6. ✅ Filtros avanzados
7. ✅ Integración con API

**Archivos:**
- `frontend/src/pages/FinanzasPage.tsx`
- `frontend/src/services/finanzasService.ts`
- `frontend/src/hooks/useFinanzas.ts`

### Fase 6: Frontend - Exportación y Reportes (2 días)

**Tareas:**
1. ✅ Modal de configuración de exportación
2. ✅ Generación de PDF en backend (WeasyPrint)
3. ✅ Generación de Excel (openpyxl)
4. ✅ Download handler en frontend

**Archivos:**
- `frontend/src/components/finanzas/ExportModal.tsx`
- `backend/apps/finanzas/export/pdf_generator.py`
- `backend/apps/finanzas/export/excel_generator.py`

### Fase 7: Testing y Pulido (2 días)

**Tareas:**
1. ✅ Testing unitario backend (pytest)
2. ✅ Testing integración signals
3. ✅ Testing frontend (Jest)
4. ✅ Testing E2E (Cypress - opcional)
5. ✅ Refinamiento UI/UX
6. ✅ Optimización de queries
7. ✅ Documentación

### Fase 8: Deployment (1 día)

**Tareas:**
1. ✅ Migración a producción
2. ✅ Poblar categorías en todas las sucursales
3. ✅ Testing en producción
4. ✅ Capacitación a usuarios
5. ✅ Monitoreo post-deployment

---

## 📦 ENTREGABLES

### Backend
- ✅ Modelos actualizados con migraciones
- ✅ Signals de integración con inventario
- ✅ API RESTful completa
- ✅ Sistema de permisos
- ✅ Generadores de PDF/Excel
- ✅ Tests unitarios e integración

### Frontend
- ✅ Página principal de Finanzas
- ✅ Formularios de registro/edición
- ✅ Dashboards y gráficos
- ✅ Sistema de exportación
- ✅ Componentes reutilizables

### Documentación
- ✅ Este documento de especificación
- ✅ Documentación de API (Swagger/ReDoc)
- ✅ Manual de usuario
- ✅ Guía de troubleshooting

---

## 🚀 PRÓXIMOS PASOS

1. **Revisar y Aprobar** este documento
2. **Crear tareas** en sistema de gestión (GitHub Issues, Jira, etc.)
3. **Asignar prioridades** a cada fase
4. **Comenzar implementación** por Fase 1
5. **Iteraciones semanales** con demos

---

## 📝 NOTAS IMPORTANTES

### Decisiones de Diseño

1. **¿Por qué 2 niveles de categorías y no más?**
   - Balance entre flexibilidad y simplicidad
   - Más niveles complican UX
   - 2 niveles cubre 95% de casos de uso

2. **¿Por qué auto-generar desde inventario?**
   - Elimina duplicación de trabajo
   - Garantiza consistencia de datos
   - Reduce errores humanos

3. **¿Por qué no permitir editar transacciones antiguas?**
   - Auditoría y cumplimiento normativo
   - Evitar manipulación de históricos
   - Mantener integridad de reportes

### Puntos de Atención

⚠️ **Multi-tenancy**: Todas las queries deben filtrar por `sucursal_id`
⚠️ **Performance**: Índices críticos en fecha, categoría, sucursal
⚠️ **Seguridad**: Endpoints de finanzas con permisos estrictos
⚠️ **Backups**: Backup diario de transacciones financieras

---

**Documento creado por:** Claude AI
**Fecha:** 17 de Noviembre de 2025
**Versión:** 1.0
**Estado:** ✅ Listo para implementación
