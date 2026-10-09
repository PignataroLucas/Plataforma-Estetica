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

        # Multi-tenancy: ningún rol puede salir de su propio centro.
        # El cliente objetivo DEBE pertenecer al centro del usuario; si no,
        # se deniega antes de evaluar el rol. Esto cierra el IDOR cross-tenant
        # (un ADMIN del centro A ya no puede leer analytics de clientes del
        # centro B). Ver CLAUDE.md: toda consulta filtra por centro_estetica.
        from apps.clientes.models import Cliente
        cliente_en_centro = Cliente.objects.filter(
            id=cliente_id,
            centro_estetica=user.centro_estetica
        ).exists()
        if not cliente_en_centro:
            return False

        # Admin y Manager: cualquier cliente de su propio centro
        if user.rol in ('ADMIN', 'MANAGER'):
            return True

        # Empleado: solo clientes de su centro que además atendió
        if user.rol == 'EMPLEADO':
            from apps.turnos.models import Turno
            has_attended = Turno.objects.filter(
                cliente_id=cliente_id,
                profesional=user
            ).exists()
            return has_attended

        return False
