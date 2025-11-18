"""
Custom permissions for financial module
Financial data is highly sensitive and should only be accessible to authorized users
"""
from rest_framework import permissions


class IsAdminOrOwner(permissions.BasePermission):
    """
    Permission: Only Admin or Owner roles can access financial data
    Employees and Managers have NO access to finances
    """
    message = "No tiene permisos para acceder a información financiera. Solo administradores."

    def has_permission(self, request, view):
        """Check if user has admin/owner role"""
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers always have access
        if request.user.is_superuser:
            return True

        # Check if user has admin/owner role
        # Assuming role field exists in Usuario model
        if hasattr(request.user, 'rol'):
            return request.user.rol in ['ADMIN', 'DUEÑO', 'ADMINISTRADOR']

        return False


class CanEditTransaction(permissions.BasePermission):
    """
    Permission: Check if transaction can be edited
    - Auto-generated transactions cannot be edited
    - Transactions older than 30 days cannot be edited
    """
    message = "Esta transacción no puede ser editada."

    def has_object_permission(self, request, view, obj):
        """Check if transaction can be edited"""
        # Read operations are allowed if user has general access
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if transaction can be edited
        if hasattr(obj, 'can_be_edited'):
            if not obj.can_be_edited:
                self.message = "No se pueden editar transacciones con más de 30 días de antigüedad."
                return False

        # Check if transaction is auto-generated
        if hasattr(obj, 'auto_generated') and obj.auto_generated:
            self.message = "No se pueden editar transacciones auto-generadas."
            return False

        return True


class CanDeleteTransaction(permissions.BasePermission):
    """
    Permission: Check if transaction can be deleted
    Auto-generated transactions cannot be deleted directly
    """
    message = "Esta transacción no puede ser eliminada."

    def has_object_permission(self, request, view, obj):
        """Check if transaction can be deleted"""
        # Only check for DELETE operations
        if request.method != 'DELETE':
            return True

        # Check if transaction can be deleted
        if hasattr(obj, 'can_be_deleted') and not obj.can_be_deleted:
            self.message = (
                "No se pueden eliminar transacciones auto-generadas. "
                "Elimine el movimiento de inventario asociado."
            )
            return False

        return True


class CanManageCategory(permissions.BasePermission):
    """
    Permission: Check if category can be modified or deleted
    System categories cannot be deleted, only deactivated
    """
    message = "Las categorías del sistema no pueden ser eliminadas."

    def has_object_permission(self, request, view, obj):
        """Check if category can be managed"""
        # Read operations are allowed
        if request.method in permissions.SAFE_METHODS:
            return True

        # Can update (deactivate) system categories
        if request.method in ['PUT', 'PATCH']:
            return True

        # Cannot delete system categories
        if request.method == 'DELETE':
            if hasattr(obj, 'is_system_category') and obj.is_system_category:
                self.message = (
                    "Las categorías del sistema no pueden ser eliminadas, "
                    "solo desactivadas."
                )
                return False

        # Check if category has transactions
        if request.method == 'DELETE':
            if hasattr(obj, 'transaction_count') and obj.transaction_count > 0:
                self.message = (
                    "No se puede eliminar una categoría que tiene transacciones asociadas. "
                    "Desactívela en su lugar."
                )
                return False

        return True


class BelongsToUserBranch(permissions.BasePermission):
    """
    Permission: Ensure the object belongs to user's branch
    Users can only access data from their own branch
    """
    message = "No tiene permisos para acceder a datos de otras sucursales."

    def has_object_permission(self, request, view, obj):
        """Check if object belongs to user's branch"""
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers can access all branches
        if request.user.is_superuser:
            return True

        # Check if user has a branch assigned
        if not hasattr(request.user, 'sucursal'):
            return False

        # Check if object belongs to user's branch
        if hasattr(obj, 'branch'):
            return obj.branch == request.user.sucursal
        elif hasattr(obj, 'sucursal'):
            return obj.sucursal == request.user.sucursal

        return True
