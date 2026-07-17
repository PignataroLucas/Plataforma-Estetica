"""
Tokens JWT para usuarios de la app mobile (UsuarioCliente).

Los tokens de cliente llevan el claim ``token_use='cliente'`` para distinguirlos
de los tokens de staff. Sin esa marca, un token con ``user_id=5`` de un UsuarioCliente
podría resolver ambiguamente a un ``Usuario`` (staff) con pk=5, que es AUTH_USER_MODEL.
"""
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

CLIENTE_TOKEN_USE = 'cliente'


class ClienteRefreshToken(RefreshToken):
    @classmethod
    def for_usuario_cliente(cls, usuario_cliente):
        token = cls()
        token[api_settings.USER_ID_CLAIM] = usuario_cliente.pk
        token['token_use'] = CLIENTE_TOKEN_USE
        return token


def tokens_para_usuario_cliente(usuario_cliente):
    """Devuelve el par {refresh, access} para una cuenta de app."""
    refresh = ClienteRefreshToken.for_usuario_cliente(usuario_cliente)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
