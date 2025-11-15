from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permiso personalizado: Solo Administradores
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'rol') and
            request.user.rol == 'ADMIN'
        )


class IsAdminOrManager(permissions.BasePermission):
    """
    Permiso personalizado: Administradores o Managers
    """
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'rol') and
            request.user.rol in ['ADMIN', 'MANAGER']
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado: Solo Admin puede escribir, otros solo lectura
    """
    def has_permission(self, request, view):
        # Permitir lectura a todos los autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Solo Admin puede escribir
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'rol') and
            request.user.rol == 'ADMIN'
        )


class IsAdminOrManagerOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado: Admin/Manager pueden escribir, otros solo lectura
    """
    def has_permission(self, request, view):
        # Permitir lectura a todos los autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Solo Admin/Manager pueden escribir
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'rol') and
            request.user.rol in ['ADMIN', 'MANAGER']
        )
