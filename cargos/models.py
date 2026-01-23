from decimal import Decimal
from django.db import models
from cuentahabientes.models import Cuentahabiente

class Cargo(models.Model):
    id_cargo = models.AutoField(primary_key=True)
    cuentahabiente = models.ForeignKey(Cuentahabiente, on_delete=models.PROTECT)
    tipo_cargo = models.CharField(max_length=150)
    monto_cargo = models.IntegerField()
    saldo_restante_cargo = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    fecha_cargo = models.DateField()
    activo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.pk is None and self.saldo_restante_cargo == Decimal("0.00"):
            self.saldo_restante_cargo = Decimal(self.monto_cargo)
        super().save(*args, **kwargs)