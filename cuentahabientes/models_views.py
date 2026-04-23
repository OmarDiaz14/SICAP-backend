from django.db.models import Field
from django.db import models

class PreParsedJSONField(Field):
    """
    PostgreSQL + psycopg2 ya deserializa columnas JSON/JSONB a tipos Python.
    Este campo evita que Django intente hacer json.loads() sobre un valor
    que ya es list/dict, lo que causaría el TypeError.
    """

    def from_db_value(self, value, expression, connection):
        return value  # ya es list o dict, no hacer nada

    def get_internal_type(self):
        return "JSONField"


class VistaPagos(models.Model):
    numero_contrato = models.IntegerField()
    nombre_completo = models.CharField(max_length=255)
    nombre_servicio = models.CharField(max_length=255, null=True, blank=True)
    anio = models.IntegerField()
    pagos_totales = models.DecimalField(max_digits=12, decimal_places=2)
    estatus_deuda = models.CharField(max_length=100)
    calle = models.CharField(max_length=255)
    saldo_pendiente = models.DecimalField(max_digits=12, decimal_places=2)
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
    cobrador = models.CharField(max_length=301, null=True, blank=True)
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
    anio_pago = models.IntegerField()
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

class EstadoCuenta(models.Model):
    id_cuentahabiente = models.IntegerField(primary_key=True)
    numero_contrato = models.IntegerField()
    nombre = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    saldo_pendiente = models.IntegerField()
    fecha_pago = models.DateField(null = True)
    monto_recibido = models.IntegerField()
    anio = models.IntegerField()
    tipo_movimiento = models.CharField(max_length=50)  # "pago" o "cargo"

    class Meta:
        managed = False
        db_table = "estado_cuenta"  

class EstadoCuentaResumen(models.Model):
    id                = models.BigIntegerField(primary_key=True)
    id_cuentahabiente = models.IntegerField()
    numero_contrato   = models.IntegerField()
    anio              = models.IntegerField()
    nombre_servicio   = models.CharField(max_length=255, null=True)
    estatus           = models.CharField(max_length=20)   # 'Pagado' | 'Corriente' | 'Adeudo' | 'Sin servicio'
    saldo_pendiente   = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    class Meta:
        managed = False
        db_table = "estado_cuenta_resumen"
class RCuentahabientes(models.Model):
    id_cuentahabiente = models.AutoField(primary_key=True)
    numero_contrato = models.IntegerField()
    nombre = models.CharField(max_length=255)
    calle = models.CharField(max_length=255)
    nombre_colonia = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    saldo_pendiente = models.DecimalField(max_digits=12, decimal_places=2)
    total_pagado = models.DecimalField(max_digits=12, decimal_places=2)
    estatus = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = "r_cuentahabientes"


class VistaCargos(models.Model):
    """Modelo de solo lectura mapeado a la vista vista_cargos."""

    id_vista          = models.IntegerField(primary_key=True)
    id_cargo          = models.IntegerField()
    cuentahabiente_id = models.IntegerField()
    tipo_cargo_nombre = models.CharField(max_length=255)
    cargo_fecha       = models.DateField()
    anio_cargo        = models.IntegerField()
    saldo_restante_cargo = models.DecimalField(max_digits=12, decimal_places=2)
    cargo_activo      = models.BooleanField()
    desglose_pagos       = PreParsedJSONField() 

    class Meta:
        managed  = False          # Django no toca esta tabla/vista
        db_table = "vista_cargos"
        ordering = ["-cargo_fecha"]


class EstadoCuentaNew(models.Model):

    id                          = models.BigIntegerField(primary_key=True)
    id_cobrador                 = models.IntegerField(null=True)
    nombre_cobrador             = models.CharField(max_length=255, null=True)
    id_cuentahabiente           = models.IntegerField()
    numero_contrato             = models.CharField(max_length=100)
    nombre_cuentahabiente       = models.CharField(max_length=255, null=True)
    calle                       = models.CharField(max_length=255, null=True)
    servicio                    = models.CharField(max_length=255, null=True)
    saldo_pendiente_actualizado = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    deuda_actualizada           = models.CharField(max_length=20, null=True)
    anio                        = models.IntegerField()
    tipo_movimiento             = models.CharField(max_length=50)
    json_pagos                  = PreParsedJSONField()

    class Meta:
        managed  = False
        db_table = "estado_cuenta_new"
        ordering = ["numero_contrato", "anio"]

class ReporteCargos(models.Model):

    id                      = models.BigIntegerField(primary_key=True)
    id_cobrador             = models.IntegerField(null=True)
    nombre_cobrador         = models.CharField(max_length=255, null=True)
    id_cuentahabiente       = models.IntegerField()
    numero_contrato         = models.CharField(max_length=100)
    nombre_cuentahabiente   = models.CharField(max_length=255, null=True)
    calle                   = models.CharField(max_length=255, null=True)
    tipo_cargo              = models.CharField(max_length=255)
    fecha_cargo             = models.DateField(null=True)
    saldo_restante_cargo    = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    estatus_cargo           = models.CharField(max_length=20)
    fecha_pago              = models.DateField(null=True)
    monto_recibido          = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        managed  = False
        db_table = "reporte_cargos"
        ordering = ["numero_contrato", "fecha_cargo"]

class ReportePadronGeneral(models.Model):

    id                          = models.BigIntegerField(primary_key=True)
    id_cuentahabiente           = models.IntegerField()
    numero_contrato             = models.CharField(max_length=100)
    nombre_usuario              = models.CharField(max_length=255, null=True)
    tipo_servicio               = models.CharField(max_length=255, null=True)
    saldo_pendiente             = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    total_pagado_acumulado      = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    detalle_cargos_json         = PreParsedJSONField(null=True)
    anio_reporte                = models.IntegerField()
    total_pagos_cobrados        = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    total_cobros_cargos         = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    total_pagos_pendientes      = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    total_cargos_pendientes     = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    total_usuarios              = models.BigIntegerField(null=True)

    class Meta:
        managed  = False
        db_table = "reporte_padron_general"
        ordering = ["numero_contrato", "anio_reporte"]