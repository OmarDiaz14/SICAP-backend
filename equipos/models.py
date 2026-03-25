from django.db import models
from calles.models import Calle
from cobrador.models import Cobrador

# Create your models here.
class Equipo(models.Model):
    id_equipo = models.AutoField(primary_key=True)
    nombre_equipo = models.CharField(max_length=100)
    calle = models.ForeignKey(Calle, on_delete=models.PROTECT, related_name='equipos')
    fecha_asignacion = models.DateField()
    fecha_termino = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    cobradores = models.ManyToManyField(
        Cobrador,
        through='EquipoCobrador',
        related_name='equipos'
    )

    def __str__(self):
        return f"{self.nombre_equipo} - {self.calle.nombre_calle}"
    
class EquipoCobrador(models.Model):
    """Tabla que registra que cobrador pertenece a que equipo."""
    
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='miembros')
    cobrador = models.ForeignKey(Cobrador, on_delete=models.PROTECT, related_name='equipo_asignado')
    fecha_ingreso = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['equipo', 'cobrador'],
                name='uniq_equipo_cobrador'
            )
        ]
        verbose_name = "Miembro de Equipo"