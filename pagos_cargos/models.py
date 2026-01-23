from django.db import models
from cargos.models import Cargo
from cobrador.models import Cobrador
from cuentahabientes.models import Cuentahabiente

class PagoCargos(models.Model):
    id_pago = models.AutoField(primary_key=True)
    cuentahabiente = models.ForeignKey(Cuentahabiente, on_delete=models.PROTECT)
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, null=True, blank=True)
    cobrador = models.ForeignKey(Cobrador, on_delete=models.PROTECT)
    monto_recibido = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateField(auto_now_add=True)
    comentarios = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "pagos_cargos"