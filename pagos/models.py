from django.db import models
from descuento.models import Descuento
from cobrador.models import Cobrador
from cuentahabientes.models import Cuentahabiente

class Pago(models.Model):
    id_pago = models.AutoField(primary_key=True)
    descuento = models.ForeignKey(Descuento, on_delete=models.PROTECT, null=True, blank=True)
    cobrador = models.ForeignKey(Cobrador, on_delete=models.PROTECT)
    cuentahabiente = models.ForeignKey(Cuentahabiente, on_delete=models.PROTECT)
    fecha_pago = models.DateField()
    monto_recibido = models.IntegerField()
    monto_descuento = models.IntegerField()
    mes = models.CharField(max_length=20)
    anio = models.IntegerField()

    def __str__(self):
        return f"Pago {self.id_pago} - Cuentahabiente: {self.cuentahabiente.nombres} {self.cuentahabiente.ap} {self.cuentahabiente.am} - Monto: {self.monto_recibido}"
    


    
