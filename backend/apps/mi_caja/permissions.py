from rest_framework.permissions import BasePermission


class CanAccessMiCaja(BasePermission):
    """
    Todos los usuarios autenticados pueden acceder a Mi Caja
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class CanViewTransaction(BasePermission):
    """
    Empleado solo ve sus propias transacciones
    Admin/Manager ve todas
    """
    def has_object_permission(self, request, view, obj):
        user = request.user

        # Admin/Manager ven todo
        if user.rol in ['ADMIN', 'MANAGER']:
            return True

        # Empleado solo ve las suyas (las que él registró)
        return obj.registered_by == user


class CanCobrarTurno(BasePermission):
    """
    Empleado puede cobrar solo sus propios turnos
    Admin/Manager pueden cobrar cualquier turno
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Admin/Manager pueden cobrar cualquier turno
        if user.rol in ['ADMIN', 'MANAGER']:
            return True

        # Empleado solo puede cobrar sus propios turnos
        return obj.profesional == user
