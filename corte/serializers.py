from rest_framework import serializers
from .models import CorteCajaJr, CorteCajaSr
class CorteSerializer(serializers.Serializer):
    #el frontend manda el string  "YYYY-MM-DD" y el backend lo convierte a datetime
    fecha_inicio = serializers.DateField(format="%Y-%m-%d", input_formats=["%Y-%m-%d"])
    fecha_fin = serializers.DateField(format="%Y-%m-%d", input_formats=["%Y-%m-%d"])

# ─── CorteCajaJr ──────────────────────────────────────────────────────────────
class CorteCajaJrSerializer(serializers.ModelSerializer):
    tesorero_nombre     = serializers.SerializerMethodField()
    validado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model  = CorteCajaJr
        fields = [
            "folio_corte",
            "fecha_generacion",
            "fecha_inicio",
            "fecha_fin",
            "total_pagos_normales",
            "total_pagos_cargos",
            "gran_total",
            "cobrador",
            "tesorero_nombre",
            "pdf",
            "validado",
            "fecha_validacion",
            "validado_por",
            "validado_por_nombre",
        ]
        read_only_fields = [
            "folio_corte",
            "fecha_generacion",
            "total_pagos_normales",
            "total_pagos_cargos",
            "gran_total",
            "cobrador",
            "validado",
            "fecha_validacion",
            "validado_por",
        ]

    def get_tesorero_nombre(self, obj):
        return f"{obj.cobrador.nombre} {obj.cobrador.apellidos}"

    def get_validado_por_nombre(self, obj):
        if obj.validado_por:
            return f"{obj.validado_por.nombre} {obj.validado_por.apellidos}"
        return None


class SubirPdfCorteJrSerializer(serializers.ModelSerializer):
    """Solo recibe el PDF firmado que manda el front."""
    class Meta:
        model  = CorteCajaJr
        fields = ["pdf"]


# ─── CorteCajaSr ──────────────────────────────────────────────────────────────
class CorteCajaSrSerializer(serializers.ModelSerializer):
    tesorero_sr_nombre  = serializers.SerializerMethodField()
    tesorero_jr_nombre  = serializers.SerializerMethodField()
    equipo_nombre       = serializers.SerializerMethodField()
    validado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model  = CorteCajaSr
        fields = [
            "folio_corte",
            "fecha_generacion",
            "fecha_inicio",
            "fecha_fin",
            "total_pagos_normales",
            "total_pagos_cargos",
            "gran_total",
            "tesorero_sr",
            "tesorero_sr_nombre",
            "tesorero_jr",
            "tesorero_jr_nombre",
            "equipo",
            "equipo_nombre",
            "pdf",
            "validado",
            "fecha_validacion",
            "validado_por",
            "validado_por_nombre",
        ]
        read_only_fields = [
            "folio_corte",
            "fecha_generacion",
            "total_pagos_normales",
            "total_pagos_cargos",
            "gran_total",
            "tesorero_sr",
            "tesorero_jr",
            "equipo",
            "validado",
            "fecha_validacion",
            "validado_por",
        ]

    def get_tesorero_sr_nombre(self, obj):
        return f"{obj.tesorero_sr.nombre} {obj.tesorero_sr.apellidos}"

    def get_tesorero_jr_nombre(self, obj):
        return f"{obj.tesorero_jr.nombre} {obj.tesorero_jr.apellidos}"

    def get_equipo_nombre(self, obj):
        if obj.equipo:
            return obj.equipo.nombre_equipo
        return None

    def get_validado_por_nombre(self, obj):
        if obj.validado_por:
            return f"{obj.validado_por.nombre} {obj.validado_por.apellidos}"
        return None


class SubirPdfCorteSrSerializer(serializers.ModelSerializer):
    """Solo recibe el PDF firmado que sube el Tesorero Sr."""
    class Meta:
        model  = CorteCajaSr
        fields = ["pdf"]
