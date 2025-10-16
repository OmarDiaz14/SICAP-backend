from django.db import models

class Servicio(models.Model):
    id_tipo_servicio = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    costo = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['id_tipo_servicio']
        db_table = 'servicio'
        verbose_name_plural = 'Servicios'

    def __str__(self):
        return f"{self.nombre} - ${self.costo}"
    