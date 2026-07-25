from django.urls import path

from .views import (
    ClienteTokenRefreshView,
    LoginView,
    MiRutinaView,
    PerfilView,
    PushRegisterView,
    RegistroView,
)

urlpatterns = [
    path('auth/registro/', RegistroView.as_view(), name='client-registro'),
    path('auth/login/', LoginView.as_view(), name='client-login'),
    path('auth/refresh/', ClienteTokenRefreshView.as_view(), name='client-refresh'),
    path('perfil/', PerfilView.as_view(), name='client-perfil'),
    path('mi-rutina/', MiRutinaView.as_view(), name='client-mi-rutina'),
    path('push/register/', PushRegisterView.as_view(), name='client-push-register'),
]
