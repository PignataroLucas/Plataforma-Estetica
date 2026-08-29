from django.urls import path

from .views import (
    CancelarTurnoView,
    ClienteTokenRefreshView,
    DescuentoAppView,
    DisponibilidadView,
    LoginView,
    MiRutinaView,
    PerfilView,
    PrepararCompraView,
    PreferenciasNotificacionView,
    PushRegisterView,
    RegistroView,
    ServiciosReservablesView,
    TurnosView,
)

urlpatterns = [
    path('auth/registro/', RegistroView.as_view(), name='client-registro'),
    path('auth/login/', LoginView.as_view(), name='client-login'),
    path('auth/refresh/', ClienteTokenRefreshView.as_view(), name='client-refresh'),
    path('perfil/', PerfilView.as_view(), name='client-perfil'),
    path('mi-rutina/', MiRutinaView.as_view(), name='client-mi-rutina'),
    path('descuento/', DescuentoAppView.as_view(), name='client-descuento-app'),
    path('comprar/', PrepararCompraView.as_view(), name='client-comprar'),
    path('turnos/', TurnosView.as_view(), name='client-turnos'),
    path('turnos/servicios/', ServiciosReservablesView.as_view(), name='client-servicios-reservables'),
    path('turnos/disponibilidad/', DisponibilidadView.as_view(), name='client-disponibilidad'),
    path('turnos/<int:pk>/cancelar/', CancelarTurnoView.as_view(), name='client-cancelar-turno'),
    path('push/register/', PushRegisterView.as_view(), name='client-push-register'),
    path('notificaciones/preferencias/', PreferenciasNotificacionView.as_view(),
         name='client-preferencias-notificacion'),
]
