from django.contrib import admin

from .models import AceptacionLegal


@admin.register(AceptacionLegal)
class AceptacionLegalAdmin(admin.ModelAdmin):
    """Solo lectura: es la constancia del consentimiento y nadie la edita a mano."""
    list_display = ('usuario_cliente', 'documento', 'version', 'aceptado_en')
    list_filter = ('documento', 'version')
    search_fields = ('usuario_cliente__email',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
