from django.db import models

# Create your models here.
class Cobrador(models.Model):
    id_cobrador = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=25)
    apellidos = models.CharField(max_length=50)
    email = models.EmailField(max_length=256, unique=True)
    usuario = models.CharField(max_length=25, unique=True)
    password = models.CharField(max_length=256)
    