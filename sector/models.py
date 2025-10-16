from django.db import models

# Create your models here.
class Sector(models.Model):
    id_sector = models.AutoField(primary_key=True)
    nombre_sector = models.CharField(max_length=50)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre_sector

    
