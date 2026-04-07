from django.db import models
from django.forms import ValidationError
from calles.models import Calle
from cobrador.models import Cobrador

# Create your models here.
class Equipo(models.Model):
    id_equipo = models.AutoField(primary_key=True)
    nombre_equipo = models.CharField(max_length=100, unique=True)
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
    fecha_salida  = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)  

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['equipo', 'cobrador'],
                name='uniq_equipo_cobrador'
            )
        ]
        verbose_name = "Miembro de Equipo"

    def clean(self):
        """Un cobrador no puede estar en más de un equipo activo al mismo tiempo"""

        qs = EquipoCobrador.objects.filter(
            cobrador=self.cobrador,
            activo=True
        )
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        if qs.exists():
            equipo_actual = qs.first().equipo.nombre_equipo
            raise ValidationError(
                {"cobrador": f"Este cobrador ya pertenece al equipo activo '{equipo_actual}'."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)