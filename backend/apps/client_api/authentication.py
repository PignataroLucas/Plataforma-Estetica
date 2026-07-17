"""Autenticación JWT para usuarios de la app mobile (UsuarioCliente)."""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.settings import api_settings

from apps.clientes.models import UsuarioCliente

from .tokens import CLIENTE_TOKEN_USE


class ClienteJWTAuthentication(JWTAuthentication):
    """
    Resuelve tokens de cliente contra ``UsuarioCliente``.

    Exige el claim ``token_use='cliente'``: un token de staff (sin ese claim) es
    rechazado, de modo que las credenciales de staff nunca autentican en la app.
    """

    def get_user(self, validated_token):
        if validated_token.get('token_use') != CLIENTE_TOKEN_USE:
            raise InvalidToken('El token no corresponde a un usuario de la app')

        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken('El token no contiene identificador de usuario')

        try:
            usuario = UsuarioCliente.objects.get(pk=user_id)
        except UsuarioCliente.DoesNotExist:
            raise AuthenticationFailed('Usuario no encontrado', code='user_not_found')

        if not usuario.activo:
            raise AuthenticationFailed('Cuenta inactiva', code='user_inactive')

        return usuario
