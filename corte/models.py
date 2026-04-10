import os
from django.db import models
from cobrador.models import Cobrador
from equipos.models import Equipo

#### Corte de Caja Principal (Tesorero Sr) ####
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



def upload_corte_jr_pdf(instance, filename):
    """cortes_jr/<año>/<mes>/corte_jr_<folio>.pdf"""
    return os.path.join(
        "cortes_jr",
        str(instance.fecha_generacion.year),
        str(instance.fecha_generacion.month),
        f"corte_jr_{instance.folio_corte}.pdf",
    )


class CorteCajaJr(models.Model):
    # ─── PK ───────────────────────────────────────────────────────────────────
    folio_corte = models.AutoField(primary_key=True)

    # ─── Fechas ───────────────────────────────────────────────────────────────
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    fecha_inicio     = models.DateField()
    fecha_fin        = models.DateField()

    # ─── Totales ──────────────────────────────────────────────────────────────
    total_pagos_normales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_pagos_cargos   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gran_total           = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # ─── Quién generó el corte (debe ser tesorero_jr) ─────────────────────────
    cobrador = models.ForeignKey(
        Cobrador,
        on_delete=models.PROTECT,
        related_name="cortes_jr_generados",
        limit_choices_to={"role": Cobrador.ROLE_TESORERO_JR},
    )

    # ─── PDF ──────────────────────────────────────────────────────────────────
    pdf = models.FileField(
        upload_to=upload_corte_jr_pdf,
        null=True,
        blank=True,
    )

    # ─── Validación (la hace el Tesorero Sr) ──────────────────────────────────
    validado         = models.BooleanField(default=False)
    fecha_validacion = models.DateTimeField(null=True, blank=True)
    validado_por     = models.ForeignKey(
        Cobrador,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cortes_jr_validados",
        limit_choices_to={"role": Cobrador.ROLE_TESORERO_SR},
    )

    def __str__(self):
        return f"Corte Jr #{self.folio_corte} — {self.cobrador} [{self.fecha_inicio} / {self.fecha_fin}]"

    class Meta:
        db_table            = "CorteCajaJr" 
        ordering            = ["-fecha_generacion"]
        verbose_name        = "Corte de Caja Jr"
        verbose_name_plural = "Cortes de Caja Jr"


#### Corte de Caja Senior (Tesorero Sr) ####

def upload_corte_sr_pdf(instance, filename):
    return os.path.join(
        "cortes_sr",
        str(instance.fecha_generacion.year),
        str(instance.fecha_generacion.month),   
        f"corte_sr_{instance.folio_corte}.pdf",
    )

class CorteCajaSr(models.Model):
    folio_corte = models.AutoField(primary_key=True)

    fecha_generacion = models.DateTimeField(auto_now_add=True)
    fecha_inicio     = models.DateField()
    fecha_fin        = models.DateField()

    total_pagos_normales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_pagos_cargos   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gran_total           = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    tesorero_sr = models.ForeignKey(
        Cobrador,
        on_delete=models.PROTECT,
        related_name="cortes_sr_generados",
        limit_choices_to={"role": Cobrador.ROLE_TESORERO_SR},
    )

    tesorero_jr = models.ForeignKey(
        Cobrador,
        on_delete=models.PROTECT,
        related_name="cortes_sr_de_equipo",
        limit_choices_to={"role": Cobrador.ROLE_TESORERO_JR},
    )

    equipo = models.ForeignKey(
        Equipo,
        on_delete=models.PROTECT,
        related_name="cortes_sr",
        null=True,
        blank=True,
    )
    

    pdf = models.FileField(
        upload_to=upload_corte_sr_pdf,
        null=True,
        blank=True,
    )

    validado         = models.BooleanField(default=False)
    fecha_validacion = models.DateTimeField(null=True, blank=True)
    validado_por     = models.ForeignKey(
        Cobrador,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cortes_sr_validados",
        limit_choices_to={"role": Cobrador.ROLE_TESORERO_SR},
    )

    def __str__(self):
        return f"Corte Sr #{self.folio_corte} — {self.equipo} [{self.fecha_inicio} / {self.fecha_fin}]"

    class Meta:
        db_table            = "CorteCajaSr"
        ordering            = ["-fecha_generacion"]
        verbose_name        = "Corte de Caja Sr"
        verbose_name_plural = "Cortes de Caja Sr"


