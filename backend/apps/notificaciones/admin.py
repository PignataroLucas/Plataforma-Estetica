from django.contrib import admin

from .models import (
    Aviso,
    DispositivoPush,
    EnvioPush,
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
