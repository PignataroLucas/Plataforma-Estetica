from django.urls import path

from . import views

urlpatterns = [
    path('privacidad/', views.privacidad, name='legales-privacidad'),
    path('eliminar-cuenta/', views.eliminar_cuenta, name='legales-eliminar-cuenta'),
]
