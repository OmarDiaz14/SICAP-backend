from django.db import models
from cuentahabientes.models import Cuentahabiente

class Cargo(models.Model):
    id_cargo = models.AutoField(primary_key=True)
    cuentahabiente = models.ForeignKey(Cuentahabiente, on_delete=models.PROTECT)
    tipo_cargo = models.CharField(max_length=150)
    monto_cargo = models.IntegerField()
    fecha_cargo = models.DateField()
