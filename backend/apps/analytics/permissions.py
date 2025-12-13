"""
Permisos para el módulo de Analytics
"""

from rest_framework import permissions


class IsAdminOrManager(permissions.BasePermission):
    """
    Solo Admin y Manager pueden acceder a analytics global
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.rol in ['ADMIN', 'MANAGER']


class CanViewClientAnalytics(permissions.BasePermission):
    """
    Puede ver analytics de cliente si:
    - Es Admin/Manager de la misma sucursal/centro
    - Es el empleado asignado a ese cliente
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        cliente_id = view.kwargs.get('cliente_id')
        if not cliente_id:
            return False

        user = request.user

        # Admin siempre puede
        if user.rol == 'ADMIN':
            return True

        # Manager de la misma sucursal/centro
        if user.rol == 'MANAGER':
            from apps.clientes.models import Cliente
            cliente = Cliente.objects.filter(
                id=cliente_id,
                centro_estetica=user.centro_estetica
            ).exists()
            return cliente

        # Empleado puede ver solo clientes que atendió
        if user.rol == 'EMPLEADO':
            from apps.turnos.models import Turno
            has_attended = Turno.objects.filter(
                cliente_id=cliente_id,
                profesional=user
            ).exists()
            return has_attended

        return False
