from django.db import models

class Cuenta(models.Model):
    nombre = models.CharField(max_length=100)
    saldo = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'cuentas'

    def __str__(self):
        return f"{self.nombre} - Saldo: {self.saldo}"
    
class Transaccion(models.Model):
    TIPO_CHOICES = (
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso'),
    )

    cuenta = models.ForeignKey(Cuenta, on_delete=models.PROTECT, related_name='transacciones')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateTimeField()
    observaciones = models.TextField(blank=True)
    comprobante = models.URLField(max_length=200)
    requisitor = models.CharField(max_length=150, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transacciones'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo.upper()} - ${self.monto}"