from django.contrib import admin

from .models import Sucursal


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    """
    Existe por la franja de respuesta a los pedidos de turno.

    El CRM no tiene pantalla de configuración de sucursal, así que sin esto los
    valores de `APROBACION_TURNOS_SPEC.md` §3.2 quedarían solo tocables por shell
    —o sea, "configurables" en el papel y hardcodeados en la práctica—.

    Lo demás de la sucursal se administra desde el CRM; acá está en solo lectura
    para poder identificar cuál es cuál sin abrir otra pestaña.
    """
    list_display = [
        'nombre', 'centro_estetica', 'respuesta_hora_inicio',
        'respuesta_hora_fin', 'horas_para_responder', 'destino_avisos',
    ]
    list_filter = ['centro_estetica', 'activa']
    search_fields = ['nombre']
    ordering = ['centro_estetica', 'nombre']

    readonly_fields = ['centro_estetica', 'nombre', 'direccion', 'ciudad', 'provincia']

    fieldsets = [
        ('Sucursal', {
            'fields': ['centro_estetica', 'nombre', 'direccion', 'ciudad', 'provincia'],
        }),
        ('Pedidos de turno de la app', {
            'fields': [
                'respuesta_hora_inicio', 'respuesta_hora_fin',
                'horas_para_responder', 'email_avisos',
            ],
            'description': (
                'La franja NO es el horario del local: es cuándo alguien mira los '
                'pedidos de turno que llegan desde la app. El plazo para responder '
                'corre solo dentro de esta franja, y de ella se deriva qué horarios '
                'se le ofrecen a la clienta.'
            ),
        }),
    ]

    def has_add_permission(self, request):
        """Las sucursales se crean desde el CRM, no desde acá."""
        return False

    def has_delete_permission(self, request, obj=None):
        return False
