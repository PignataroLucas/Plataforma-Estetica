from django.db import models
from apps.empleados.models import Usuario, Sucursal


class TransaccionEliminada(models.Model):
    """
    Audit log for deleted transactions from Mi Caja.
    Stores a snapshot of the original transaction data + deletion reason.
    """
    # Who deleted and when
    eliminada_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transacciones_eliminadas'
    )
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name='transacciones_eliminadas'
    )
    eliminada_en = models.DateTimeField(auto_now_add=True)

    # Mandatory reason
    motivo = models.TextField(
        help_text="Motivo obligatorio de la eliminación"
    )

    # Snapshot of original transaction
    transaccion_id_original = models.IntegerField(
        help_text="ID original de la transacción eliminada"
    )
    tipo = models.CharField(max_length=20)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=20)
    fecha = models.DateField()
    descripcion = models.CharField(max_length=300)
    notas_originales = models.TextField(blank=True)
    cliente_nombre = models.CharField(max_length=200, blank=True)
    registrada_por_nombre = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Transacción Eliminada'
        verbose_name_plural = 'Transacciones Eliminadas'
        ordering = ['-eliminada_en']

    def __str__(self):
        return f"Eliminada #{self.transaccion_id_original} - ${self.monto} - {self.motivo[:50]}"


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
