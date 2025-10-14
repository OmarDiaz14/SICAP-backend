from django.db import models
from cobrador.models import Cobrador
from sector.models import Sector


class Asignacion(models.Model):
    id_asignacion = models.AutoField(primary_key=True)
    cobrador = models.ForeignKey(Cobrador, on_delete=models.CASCADE)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE)
    fecha_asignacion = models.DateField()

    def __str__(self):
        return f"Asignacion {self.id_asignacion} - Cobrador: {self.cobrador.nombre} {self.cobrador.apellidos} - Sector: {self.sector.nombre_sector}"

