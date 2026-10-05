from django.contrib import admin

from .models import (
    Aviso,
    DispositivoPush,
    EnvioPush,
    NotificacionInterna,
    PlantillaNotificacion,
    PreferenciaNotificacion,
)


@admin.register(DispositivoPush)
class DispositivoPushAdmin(admin.ModelAdmin):
    list_display = ('usuario_cliente', 'plataforma', 'activo', 'motivo_baja', 'actualizado_en')
    list_filter = ('activo', 'plataforma', 'motivo_baja')
    search_fields = ('usuario_cliente__email', 'token')
    readonly_fields = ('token', 'creado_en', 'actualizado_en')


@admin.register(PreferenciaNotificacion)
class PreferenciaNotificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario_cliente', 'categoria', 'habilitada', 'actualizado_en')
    list_filter = ('categoria', 'habilitada')
    search_fields = ('usuario_cliente__email',)


@admin.register(PlantillaNotificacion)
class PlantillaNotificacionAdmin(admin.ModelAdmin):
    list_display = ('evento', 'centro_estetica', 'activa', 'actualizado_en')
    list_filter = ('activa', 'centro_estetica')
    search_fields = ('evento', 'titulo', 'cuerpo')


class EnvioPushInline(admin.TabularInline):
    model = EnvioPush
    extra = 0
    can_delete = False
    readonly_fields = ('dispositivo', 'estado', 'ticket_id', 'error', 'confirmado_en')


@admin.register(Aviso)
class AvisoAdmin(admin.ModelAdmin):
    list_display = ('evento', 'usuario_cliente', 'estado', 'programado_para', 'enviado_en')
    list_filter = ('estado', 'categoria', 'evento')
    search_fields = ('usuario_cliente__email', 'titulo', 'clave')
    date_hierarchy = 'creado_en'
    inlines = [EnvioPushInline]
    readonly_fields = ('creado_en', 'enviado_en', 'intentos')


@admin.register(NotificacionInterna)
class NotificacionInternaAdmin(admin.ModelAdmin):
    """
    La bandeja del centro, en solo lectura, para diagnosticar entregas.

    La columna que importa es `email_estado`: sin esto, un mail que no sale no
    deja rastro en ningún lado visible, y el síntoma —"AME dice que no le
    llegó"— no distingue entre un aviso que nunca se creó, uno que falló tres
    veces y uno que se mandó a una casilla sin configurar.

    El CRM va a tener su propia pantalla en la Fase 6; esta es la de atrás.
    """
    list_display = (
        'creada_en', 'tipo', 'sucursal', 'titulo',
        'email_estado', 'email_intentos', 'email_destino', 'leida_en',
    )
    list_filter = ('email_estado', 'tipo', 'sucursal')
    search_fields = ('titulo', 'email_destino', 'clave')
    date_hierarchy = 'creada_en'
    ordering = ('-creada_en',)
    list_select_related = ('sucursal', 'turno')

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False
