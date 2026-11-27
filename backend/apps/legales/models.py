from django.db import models


class AceptacionLegal(models.Model):
    """
    Que una cuenta de la app aceptó una versión de un documento, y cuándo.

    Es la constancia del consentimiento: sin esta fila, la app no deja seguir.
    Una por versión, así que el historial queda entero cuando el documento
    cambia. Se borra con la cuenta (ver ``apps/clientes/cuenta_app.py``).
    """

    class Documento(models.TextChoices):
        PRIVACIDAD = 'PRIVACIDAD', 'Política de privacidad'

    usuario_cliente = models.ForeignKey(
        'clientes.UsuarioCliente',
        on_delete=models.CASCADE,
        related_name='aceptaciones_legales',
    )
    documento = models.CharField(max_length=20, choices=Documento.choices)
    version = models.DateField()
    aceptado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Aceptación de documento legal'
        verbose_name_plural = 'Aceptaciones de documentos legales'
        ordering = ['-aceptado_en']
        constraints = [
            models.UniqueConstraint(
                fields=['usuario_cliente', 'documento', 'version'],
                name='aceptacion_unica_por_version',
            ),
        ]

    def __str__(self):
        return f'{self.usuario_cliente_id} aceptó {self.documento} {self.version}'
