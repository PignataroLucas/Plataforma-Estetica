from rest_framework.permissions import BasePermission


class IsIntegrationAdmin(BasePermission):
    """
    Only ADMIN can see or configure integrations.

    The integration holds a credential and decides where income lands, so it
    sits behind the same wall as the financial module.
    """
    message = 'Solo un administrador puede gestionar integraciones'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.rol == 'ADMIN')
