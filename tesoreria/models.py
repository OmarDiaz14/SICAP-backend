import os
from django.db import models
from django.forms import ValidationError

def upload_comprobante_egreso(instance, filename):
        return os.path.join(
            "comprobantes_egresos",
            str(instance.fecha.year),
            str(instance.fecha.month),
            filename,
        )


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
    comprobante = models.FileField(upload_to=upload_comprobante_egreso, null=True, blank=True)
    requisitor = models.CharField(max_length=150, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.tipo == 'egreso' and not self.requisitor:
            raise ValidationError(
                {"requisitor": "El requisitor es obligatorio."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'transacciones'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo.upper()} - ${self.monto}"