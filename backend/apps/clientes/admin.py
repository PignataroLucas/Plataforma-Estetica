from django.contrib import admin

from .models import (
    Cliente,
    UsuarioCliente,
    VinculacionCliente,
    CodigoInvitacion,
)


class VinculacionInline(admin.TabularInline):
    model = VinculacionCliente
    extra = 0
    autocomplete_fields = ['cliente']
    raw_id_fields = ['vinculado_por']
    readonly_fields = ['vinculado_en']


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['apellido', 'nombre', 'telefono', 'email', 'centro_estetica', 'activo']
    list_filter = ['centro_estetica', 'activo']
    search_fields = ['nombre', 'apellido', 'telefono', 'email', 'numero_documento']
    actions = ['generar_codigo_invitacion']

    @admin.action(description='Generar código de invitación a la app')
    def generar_codigo_invitacion(self, request, queryset):
        creados = []
        for cliente in queryset:
            codigo = CodigoInvitacion.objects.create(
                cliente=cliente,
                generado_por=request.user if request.user.is_authenticated else None,
            )
            creados.append(codigo.codigo)
        self.message_user(
            request,
            f"{len(creados)} código(s) generado(s): {', '.join(creados)}"
        )


@admin.register(UsuarioCliente)
class UsuarioClienteAdmin(admin.ModelAdmin):
    list_display = ['email', 'nombre', 'apellido', 'email_verificado', 'activo', 'creado_en']
    list_filter = ['email_verificado', 'activo']
    search_fields = ['email', 'nombre', 'apellido']
    readonly_fields = ['password', 'last_login', 'creado_en', 'actualizado_en']
    inlines = [VinculacionInline]


@admin.register(VinculacionCliente)
class VinculacionClienteAdmin(admin.ModelAdmin):
    list_display = ['usuario_cliente', 'cliente', 'metodo_vinculacion', 'vinculado_en', 'vinculado_por']
    list_filter = ['metodo_vinculacion', 'vinculado_en']
    search_fields = ['usuario_cliente__email', 'cliente__nombre', 'cliente__apellido']
    autocomplete_fields = ['usuario_cliente', 'cliente']
    raw_id_fields = ['vinculado_por']
    readonly_fields = ['vinculado_en']


@admin.register(CodigoInvitacion)
class CodigoInvitacionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'cliente', 'estado', 'generado_por', 'generado_en', 'expira_en', 'usado_en']
    list_filter = ['generado_en', 'expira_en']
    search_fields = ['codigo', 'cliente__nombre', 'cliente__apellido']
    autocomplete_fields = ['cliente']
    raw_id_fields = ['generado_por', 'usado_por']
    readonly_fields = ['codigo', 'generado_en', 'usado_en', 'usado_por', 'estado']
