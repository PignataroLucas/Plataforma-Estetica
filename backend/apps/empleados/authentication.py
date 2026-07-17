"""Autenticación JWT para staff (Usuario)."""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class StaffJWTAuthentication(JWTAuthentication):
    """
    Auth JWT por defecto del sistema (staff).

    Endurecimiento: rechaza tokens emitidos para usuarios de la app mobile
    (claim ``token_use='cliente'``). Esto impide que un token de cliente con
    ``user_id=N`` autentique como el ``Usuario`` staff con pk=N.

    Es retrocompatible: los tokens de staff no llevan ``token_use``, así que
    ``super().get_user()`` se ejecuta sin cambios.
    """

    def get_user(self, validated_token):
        if validated_token.get('token_use') == 'cliente':
            raise InvalidToken('El token corresponde a un usuario de la app, no a staff')
        return super().get_user(validated_token)
