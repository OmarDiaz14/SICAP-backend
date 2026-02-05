from decimal import Decimal
from django.db import models
from cuentahabientes.models import Cuentahabiente

class TipoCargo(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150, unique=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    automatico = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre
    
class Cargo(models.Model):
    id_cargo = models.AutoField(primary_key=True)
    cuentahabiente = models.ForeignKey(Cuentahabiente, on_delete=models.PROTECT)
    tipo_cargo = models.ForeignKey(TipoCargo, on_delete=models.PROTECT, related_name="cargos")
    saldo_restante_cargo = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    fecha_cargo = models.DateField()
    activo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.pk is None and self.saldo_restante_cargo == Decimal("0.00"):
            self.saldo_restante_cargo = Decimal(self.tipo_cargo.monto)
        super().save(*args, **kwargs)