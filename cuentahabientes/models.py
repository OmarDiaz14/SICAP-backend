from django.db import models
from colonia.models import Colonia
from servicio.models import Servicio
# Create your models here.
class Cuentahabiente(models.Model):
    id_cuentahabiente = models.AutoField(primary_key=True)
    numero_contrato = models.IntegerField(unique=True)
    nombres = models.CharField(max_length=25)
    ap = models.CharField(max_length=50) # apellido paterno
    am = models.CharField(max_length=50) # apellido materno
    calle = models.CharField(max_length=256)
    numero = models.IntegerField()
    telefono = models.CharField(max_length=20)
    colonia = models.ForeignKey(Colonia, on_delete=models.PROTECT)
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT, null=True, blank=True)
    deuda = models.CharField(max_length=20)
    saldo_pendiente = models.IntegerField()

    deuda = models.CharField(max_length=20)

def __str__(self):
    return f"{self.nombres} {self.ap} {self.am}"
