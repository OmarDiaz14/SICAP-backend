from django.db import models

# Create your models here.
class Descuento(models.Model):
    id_descuento = models.AutoField(primary_key=True)
    nombre_descuento = models.CharField(max_length=100)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    activo = models.BooleanField(default=True)