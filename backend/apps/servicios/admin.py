from django import forms
from django.contrib import admin

from .models import CategoriaServicio, Servicio


@admin.register(CategoriaServicio)
class CategoriaServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sucursal', 'activa', 'cantidad_servicios')
    list_filter = ('activa', 'sucursal')
    search_fields = ('nombre',)
    readonly_fields = ('creado_en', 'actualizado_en')

    @admin.display(description='Servicios')
    def cantidad_servicios(self, obj):
        return obj.servicios.count()


class ServicioCategoriaForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ('categoria',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo las categorías de la sucursal del servicio: el desplegable no
        # tiene que ofrecer las de otro centro.
        self.fields['categoria'].queryset = CategoriaServicio.objects.filter(
            sucursal_id=self.instance.sucursal_id
        )


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    """
    Acá solo se asigna la categoría. El resto del servicio (precio, fechas de
    reserva, etc.) se edita desde el CRM, que es donde están las validaciones.
    """
    form = ServicioCategoriaForm
    list_display = ('nombre', 'sucursal', 'categoria', 'activo')
    list_filter = ('sucursal', 'categoria', 'activo')
    search_fields = ('nombre',)
    fields = ('nombre', 'sucursal', 'categoria')
    readonly_fields = ('nombre', 'sucursal')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
