from django.db import models
from apps.empleados.models import Usuario, Sucursal


class CierreCaja(models.Model):
    """
    Daily cash register closing record per employee.
    Records the physical cash count vs system calculations.
    """
    # Relationships
    empleado = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='cierres_caja',
        help_text="Empleado que realiza el cierre"
    )
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='cierres_caja'
    )

    # Date
    fecha = models.DateField(
        db_index=True,
        help_text="Fecha del cierre de caja"
    )

    # System amounts (calculated from transactions)
    total_sistema = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total según transacciones registradas en el sistema"
    )

    # Physical count
    efectivo_contado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Efectivo físico contado al cierre"
    )

    # Difference
    diferencia = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Diferencia entre sistema y físico (negativo = falta, positivo = sobra)"
    )

    # Payment method breakdown (from system)
    desglose_metodos = models.JSONField(
        default=dict,
        help_text="Desglose por método de pago según sistema: {'CASH': 5000, 'DEBIT_CARD': 3000, ...}"
    )

    # Notes
    notas = models.TextField(
        blank=True,
        help_text="Notas o explicaciones sobre diferencias"
    )

    # Timestamps
    cerrado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cierre de Caja'
        verbose_name_plural = 'Cierres de Caja'
        ordering = ['-fecha', '-cerrado_en']
        unique_together = [['empleado', 'fecha']]
        indexes = [
            models.Index(fields=['sucursal', 'fecha']),
            models.Index(fields=['empleado', 'fecha']),
        ]

    def __str__(self):
        return f"Cierre {self.empleado.get_full_name()} - {self.fecha.strftime('%d/%m/%Y')}"

    @property
    def tiene_diferencia(self):
        """Check if there's a difference between system and physical count"""
        return abs(self.diferencia) > 0

    @property
    def diferencia_significativa(self):
        """Check if difference is significant (> $500)"""
        return abs(self.diferencia) > 500
