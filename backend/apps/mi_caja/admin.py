from django.contrib import admin
from .models import CierreCaja


@admin.register(CierreCaja)
class CierreCajaAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'empleado', 'sucursal', 'total_sistema', 'efectivo_contado', 'diferencia', 'cerrado_en']
    list_filter = ['fecha', 'sucursal', 'empleado']
    search_fields = ['empleado__first_name', 'empleado__last_name', 'notas']
    readonly_fields = ['cerrado_en']
    date_hierarchy = 'fecha'

    def has_delete_permission(self, request, obj=None):
        # Solo admin puede eliminar cierres
        return request.user.is_superuser
