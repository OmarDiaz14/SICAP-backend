from django.db import models
from cobrador.models import Cobrador


class CorteCaja(models.Model):
    folio_corte = models.AutoField(primary_key=True)
    cobrador_id = models.ForeignKey(Cobrador, on_delete=models.PROTECT, related_name='cortes_realizados', null = True, blank=True)

    fecha_generacion = models.DateTimeField(auto_now_add=True)

    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()

    total_pagos_normales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_pagos_cargos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    gran_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)


    class Meta: 
        #nombre de tabla para que la funcion lo encuentre 
        db_table = 'CorteCaja'

        #ordenar del mas reciente a las fechas mas antiguas
        ordering = ['-folio_corte']


    def __str__(self):
        return f"Corte {self.folio_corte} - Cobrador: {self.cobrador_id.nombre} - Total: {self.gran_total} -  Fecha: {self.fecha_generacion.strftime('%Y-%m-%d')}"

