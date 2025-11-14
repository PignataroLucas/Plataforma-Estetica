from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Usuario, CentroEstetica, Sucursal
from .serializers import (
    UsuarioSerializer,
    CentroEsteticaSerializer,
    SucursalSerializer,
    CustomTokenObtainPairSerializer
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para obtener JWT tokens junto con los datos del usuario
    """
    serializer_class = CustomTokenObtainPairSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo Usuario
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Endpoint para obtener los datos del usuario actual
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class CentroEsteticaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo CentroEstetica
    """
    queryset = CentroEstetica.objects.all()
    serializer_class = CentroEsteticaSerializer
    permission_classes = [IsAuthenticated]


class SucursalViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo Sucursal
    """
    queryset = Sucursal.objects.all()
    serializer_class = SucursalSerializer
    permission_classes = [IsAuthenticated]
