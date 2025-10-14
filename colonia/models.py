from django.db import models

# Create your models here.
class Colonia(models.Model):
    id_colonia = models.AutoField(primary_key=True)
    nombre_colonia = models.CharField(max_length=50)
    codigo_postal = models.IntegerField()

    def __str__(self):
        return self.nombre_colonia
  