from django.db import models

# Create your models here.
class Calle(models.Model):
    id_calle = models.AutoField(primary_key=True)
    nombre_calle = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre_calle
    
    class Meta:
        ordering = ['nombre_calle']
        verbose_name = "Calle"
        verbose_name_plural = "Calles"