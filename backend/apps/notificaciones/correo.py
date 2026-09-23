"""
Envío de correo por AWS SES.

Se usa boto3 directo y no el framework de mail de Django ni `django-ses`: boto3
ya está en el proyecto por S3, así que esto no suma ninguna dependencia. Las
credenciales son las mismas que las del bucket.

**Dos trampas de SES que conviene tener presentes:**

1. Una cuenta nueva arranca en *sandbox*: solo puede escribirle a direcciones
   verificadas. Alcanza para probar con la propia, pero para mandarle a las
   clientas hay que pedir acceso a producción, que tarda alrededor de un día.
2. El remitente también tiene que estar verificado, sea la dirección suelta o
   el dominio entero.

En desarrollo, sin SES configurado, el mensaje se escribe en el log en lugar de
enviarse. Eso es lo que permite probar el circuito de recuperación de contraseña
sin credenciales: el código aparece en la consola del backend.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class CorreoNoEnviado(Exception):
    """No se pudo entregar el mensaje a SES."""


def hay_correo_configurado() -> bool:
    return bool(getattr(settings, 'EMAIL_REMITENTE', '')) and bool(
        getattr(settings, 'AWS_ACCESS_KEY_ID', '')
    )


def enviar_correo(destinatario: str, asunto: str, cuerpo: str) -> None:
    """
    Manda un correo de texto plano. Lanza ``CorreoNoEnviado`` si falla.

    Sin configuración de SES no lanza: registra el mensaje entero en el log y
    sigue. Es deliberado —en desarrollo el circuito tiene que poder probarse—
    pero significa que **en producción hay que verificar que las variables estén
    puestas**, porque si faltan esto no falla, solo deja de entregar.
    """
    if not hay_correo_configurado():
        logger.warning(
            'SES no configurado: el correo para %s no se envía. Asunto: %s\n%s',
            destinatario, asunto, cuerpo,
        )
        return

    # La importación va acá adentro para que el módulo se pueda importar (y
    # testear) en entornos sin boto3 instalado.
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    cliente = boto3.client(
        'ses',
        region_name=settings.AWS_SES_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

    try:
        cliente.send_email(
            Source=settings.EMAIL_REMITENTE,
            Destination={'ToAddresses': [destinatario]},
            Message={
                'Subject': {'Data': asunto, 'Charset': 'UTF-8'},
                'Body': {'Text': {'Data': cuerpo, 'Charset': 'UTF-8'}},
            },
        )
    except (BotoCoreError, ClientError) as exc:
        logger.exception('SES rechazó el correo para %s', destinatario)
        raise CorreoNoEnviado(str(exc)) from exc
