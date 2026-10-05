from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import Turno


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    """
    Ventana de diagnóstico del circuito de aprobación, **en solo lectura**.

    Existe porque `vence_en` no se ve desde ningún otro lado: se calcula al
    reservar y se guarda, pero los serializers del CRM tienen lista explícita de
    campos y no lo exponen. Sin esto, el plazo de cada pedido es invisible y el
    vencimiento automático no se puede diagnosticar cuando algo sale raro.

    **No se edita acá, y es deliberado.** Crear o mover un turno desde el admin
    saltea `reservar_turno`, que es donde vive el lock que evita la doble reserva
    (apps/turnos/services.py). Un turno cargado por este formulario podría
    pisarse con otro sin que nada avise. Los turnos se gestionan desde el CRM.
    """
    list_display = [
        'fecha_hora_inicio', 'cliente', 'servicio', 'estado_coloreado',
        'origen', 'plazo', 'resuelto_por', 'motivo_rechazo',
    ]
    list_filter = ['estado', 'origen', 'sucursal', 'motivo_rechazo']
    search_fields = ['cliente__nombre', 'cliente__apellido', 'servicio__nombre']
    date_hierarchy = 'fecha_hora_inicio'
    ordering = ['-fecha_hora_inicio']
    list_select_related = ['cliente', 'servicio', 'resuelto_por', 'sucursal']

    fieldsets = [
        ('Turno', {
            'fields': [
                'sucursal', 'cliente', 'servicio', 'profesional',
                'fecha_hora_inicio', 'fecha_hora_fin', 'notas',
            ],
        }),
        ('Pedido desde la app', {
            'fields': ['origen', 'estado', 'vence_en', 'plazo'],
            'description': (
                'El plazo sale de la franja de respuesta de la sucursal y se '
                'congela al reservar: si la política cambia, los pedidos vivos '
                'conservan el suyo.'
            ),
        }),
        ('Resolución', {
            'fields': [
                'resuelto_por', 'resuelto_en', 'motivo_rechazo', 'detalle_rechazo',
            ],
            'description': (
                'Sin «resuelto por» y con motivo «venció sin respuesta» significa '
                'que lo cerró el sistema, no una persona.'
            ),
        }),
        ('Cobro', {
            'fields': ['estado_pago', 'monto_total', 'monto_sena'],
            'classes': ['collapse'],
        }),
    ]

    def get_readonly_fields(self, request, obj=None):
        """Todo, siempre. Ver el docstring de la clase."""
        return [f.name for f in self.model._meta.fields] + ['plazo']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='Estado')
    def estado_coloreado(self, obj):
        colores = {
            Turno.Estado.PENDIENTE: '#92400E',
            Turno.Estado.CONFIRMADO: '#065F46',
            Turno.Estado.RECHAZADO: '#9A3412',
            Turno.Estado.CANCELADO: '#6B7280',
            Turno.Estado.COMPLETADO: '#1D4ED8',
            Turno.Estado.NO_SHOW: '#6B7280',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colores.get(obj.estado, '#111827'),
            obj.get_estado_display(),
        )

    @admin.display(description='Plazo')
    def plazo(self, obj):
        """
        Cuánto le queda al pedido antes de vencer.

        Es la columna que justifica todo este admin: dice de un vistazo si un
        pendiente está por caerse o si ya se le pasó el tiempo y el barrido
        todavía no lo levantó.
        """
        if obj.vence_en is None:
            return '—'

        if obj.estado != Turno.Estado.PENDIENTE:
            return format_html(
                '<span style="color: #6B7280;">vencía {}</span>',
                timezone.localtime(obj.vence_en).strftime('%d/%m %H:%M'),
            )

        restante = obj.vence_en - timezone.now()
        if restante.total_seconds() <= 0:
            return format_html('<span style="color: #9A3412;">vencido</span>')

        horas, resto = divmod(int(restante.total_seconds()), 3600)
        minutos = resto // 60
        falta = f'{horas} h {minutos} min' if horas else f'{minutos} min'
        return format_html('<span style="color: #92400E;">faltan {}</span>', falta)
