from django.db import models

class VistaPagos(models.Model):
    numero_contrato = models.IntegerField()
    nombre_completo = models.CharField(max_length=255)
    nombre_servicio = models.CharField(max_length=255, null=True, blank=True)
    anio = models.IntegerField()
    pagos_totales = models.DecimalField(max_digits=12, decimal_places=2)
    estatus_deuda = models.CharField(max_length=100)
    id = models.BigIntegerField(primary_key=True)  # <- pk

    class Meta:
        managed = False
        db_table = 'vista_pagos'

class VistaHistorial(models.Model):
    numero_contrato = models.IntegerField()
    fecha_pago = models.DateField()
    monto_recibido = models.DecimalField(max_digits=12, decimal_places=2)
    mes = models.CharField(max_length=20)
    anio = models.IntegerField()
    id = models.BigIntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'vista_historial'
