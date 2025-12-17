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
    id = models.BigIntegerField(primary_key=True)
    numero_contrato = models.IntegerField()
    fecha_pago = models.DateField()
    monto_recibido = models.DecimalField(max_digits=12, decimal_places=2)
    mes = models.CharField(max_length=20)
    anio = models.IntegerField()
    nombre_descuento = models.CharField(max_length=150, null=True, blank=True)
    comentarios = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'vista_historial'
        ordering = ['-fecha_pago', 'numero_contrato']


class VistaDeudores(models.Model):
    id_cuentahabiente = models.IntegerField(primary_key=True)
    nombre_cuentahabiente = models.CharField(max_length=255)
    monto_total = models.IntegerField()
    estatus = models.CharField(max_length=20)
    nombre_colonia = models.CharField(max_length=255)
    class Meta:
        managed = False
        db_table = 'vista_deudores' 

class VistaProgreso(models.Model):
    numero_contrato = models.IntegerField()
    nombre = models.CharField(max_length=150)
    estatus = models.CharField(max_length=20)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    saldo = models.DecimalField(max_digits=12, decimal_places=2)
    progreso = models.CharField(max_length=4)
    id_cuentahabiente = models.IntegerField(primary_key=True)

    class Meta:
        managed = False        
        db_table = "vista_progreso"
        ordering = ["numero_contrato"]

    def __str__(self):
        return f"{self.numero_contrato} - {self.nombre} ({self.progreso})"