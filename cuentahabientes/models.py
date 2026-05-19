from django.db import models
from decimal import Decimal
from calles.models import Calle
from cobrador.models import Cobrador
from colonia.models import Colonia
from servicio.models import Servicio


class Cuentahabiente(models.Model):
    ESTATUS_DEUDA = [
        ('pagado',    'Pagado'),
        ('corriente', 'Corriente'),
        ('rezagado',  'Rezagado'),
        ('adeudo',    'Adeudo'),
    ]
    TIPO_CUENTA = [
        ('permanente', 'Permanente'),
        ('parcial',    'Parcial'),
    ]

    # ── Identificación ────────────────────────────────────────────────
    id_cuentahabiente = models.AutoField(primary_key=True)
    numero_contrato   = models.IntegerField(unique=True)

    # ── Datos personales ──────────────────────────────────────────────
    nombres  = models.CharField(max_length=25)
    ap       = models.CharField(max_length=50)   # apellido paterno
    am       = models.CharField(max_length=50)   # apellido materno
    telefono = models.CharField(max_length=20)

    # ── Dirección ─────────────────────────────────────────────────────
    calle_fk        = models.ForeignKey(Calle, on_delete=models.PROTECT,
                                        null=True, blank=True)
    numero          = models.CharField(max_length=10, null=True, blank=True)
    numero_interior = models.CharField(max_length=10, null=True, blank=True)
    colonia         = models.ForeignKey(Colonia, on_delete=models.PROTECT)

    # ── Servicio y deuda ──────────────────────────────────────────────
    servicio        = models.ForeignKey(Servicio, on_delete=models.PROTECT,
                                        null=True, blank=True)
    deuda           = models.CharField(max_length=20,
                                       choices=ESTATUS_DEUDA,
                                       default='adeudo')
    saldo_pendiente = models.DecimalField(max_digits=10, decimal_places=2,
                                          default=0)

    # ── Tipo de cuenta ────────────────────────────────────────────────
    tipo_cuenta = models.CharField(max_length=20,
                                   choices=TIPO_CUENTA,
                                   default='permanente')

    # ── Fechas ────────────────────────────────────────────────────────
    fecha_registro      = models.DateField(null=True, blank=True)  # la captura el usuario
    fecha_activacion    = models.DateField(null=True, blank=True)
    fecha_desactivacion = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cuentahabiente"

    def __str__(self):
        return f"{self.nombres} {self.ap} {self.am}"

    # ── Helpers ───────────────────────────────────────────────────────

    @property
    def esta_activo(self):
        """Cuenta activa = fue activada y no ha sido desactivada."""
        return (
            self.fecha_activacion is not None and
            self.fecha_desactivacion is None
        )

    @property
    def tarifa_mensual(self):
        """Costo del servicio / 12."""
        if not self.servicio or not self.servicio.costo:
            return Decimal('0')
        return (Decimal(str(self.servicio.costo)) / 12).quantize(Decimal('0.01'))

    @property
    def tarifa_anual(self):
        """Costo completo del servicio."""
        if not self.servicio or not self.servicio.costo:
            return Decimal('0')
        return Decimal(str(self.servicio.costo))

    @staticmethod
    def aplica_cobro_por_dia(dia: int) -> bool:
        """
        Regla del día 15:
          día <= 15 → True  (aplica cobro)
          día >  15 → False (no aplica cobro)
        El significado depende del contexto:
          Activación:    True  = sí cobra este mes
          Desactivación: True  = NO cobra este mes  (se invierte al usarse)
        """
        return dia <= 15


class CierreAnual(models.Model):
    anio          = models.IntegerField(unique=True)
    ejecutado     = models.BooleanField(default=False)
    fecha         = models.DateField(auto_now_add=True)
    ejecutado_por = models.ForeignKey(
        Cobrador, on_delete=models.PROTECT,
        related_name="cierres_anuales"
    )

    class Meta:
        db_table = "cierre_anual"