# cuentahabientes/serializers.py
from django.utils import timezone
from django.db.models import Max
from decimal import Decimal

from rest_framework import serializers

from cargos.models import Cargo, TipoCargo
from .models import Cuentahabiente

class CuentahabienteSerializer(serializers.ModelSerializer):
    
    numero_contrato = serializers.IntegerField(required=False)
    es_toma_nueva = serializers.BooleanField(write_only=True, required=False, default=False)
    class Meta:

        model = Cuentahabiente
        fields = (
            "id_cuentahabiente", "numero_contrato", "nombres", "ap", "am",
            "calle", "calle_fk", "numero", "telefono",
            "colonia",
            "servicio",           # <- el cliente elige el servicio (ID)
            "deuda",
            "saldo_pendiente",    # <- lo calculamos; solo lectura al crear
            "es_toma_nueva",
        )
        read_only_fields = ("id_cuentahabiente", "saldo_pendiente")

    def validate_numero_contrato(self, value):

        if value is None:
            return value

        # Evitar que el numero de contrato sea negativo
        if value <= 0:
            raise serializers.ValidationError(
                "El número de contrato no puede ser negativo"
            )
        
        qs = Cuentahabiente.objects.filter(numero_contrato=value)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Ya existe un cuentahabiente con ese número de contrato."
            )

        return value
    
    def create(self, validated_data):
        """
        Al crear, establece saldo_pendiente = costo del servicio seleccionado.
        El cliente NO necesita mandar saldo_pendiente.
        """

        es_toma_nueva = validated_data.pop("es_toma_nueva", False)

        # Generar numero de contrato a partir del 2000
        ultimo_existente = set(
            Cuentahabiente.objects
            .filter(numero_contrato__gte=2000)
            .values_list("numero_contrato", flat=True)
        )

        nuevo_numero = 2000
        while nuevo_numero in ultimo_existente:
            nuevo_numero += 1

        validated_data["numero_contrato"] = nuevo_numero

        srv = validated_data["servicio"]
        validated_data["saldo_pendiente"] = srv.costo

        cuentahabiente = super().create(validated_data)

        if es_toma_nueva:

            tipo, created = TipoCargo.objects.get_or_create(
                nombre="Toma nueva",
                defaults={"monto": Decimal("1500.00"), "automatico":True}
            )
            
            Cargo.objects.create(
                cuentahabiente=cuentahabiente,
                tipo_cargo=tipo,
                fecha_cargo=timezone.now().date(),
                activo=True
            )

        return cuentahabiente

# cuentahabientes/serializers.py
from rest_framework import serializers
from .models_views import (VistaPagos,VistaHistorial,
                            VistaDeudores, VistaProgreso,
                            EstadoCuenta, RCuentahabientes, EstadoCuentaResumen
                            , VistaCargos, EstadoCuentaNew, ReporteCargos
)
class VistaPagosSerializer(serializers.ModelSerializer):
    class Meta:
        model = VistaPagos
        fields = "__all__"

class VistaHistorialSerializer(serializers.ModelSerializer):
    class Meta:
        model = VistaHistorial
        fields = "__all__"

class VistaDeudoresSerializer(serializers.ModelSerializer):
    class Meta:
        model = VistaDeudores
        fields = "__all__"


class VistaProgresoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VistaProgreso
        # puedes quitar id_cuentahabiente si no quieres exponerlo
        fields = [
            "numero_contrato",
            "nombre",
            "estatus",
            "anio_pago",
            "total",
            "saldo",
            "progreso",
        ]
    
class EstadoCuentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoCuenta
        fields = [
            "id_cuentahabiente",
            "numero_contrato",
            "nombre",
            "direccion",
            "telefono",
            "saldo_pendiente",
            "fecha_pago",
            "monto_recibido",
            "anio",
            "tipo_movimiento",
        ]

class EstadoCuentaResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoCuentaResumen
        fields = [
            "id_cuentahabiente",
            "numero_contrato",
            "anio",
            "nombre_servicio",
            "estatus",
            "saldo_pendiente",
        ]

class RCuentahabientesSerializer(serializers.ModelSerializer):
    class Meta:
        model = RCuentahabientes
        fields = '__all__'


class CierreAnioSerializer(serializers.Serializer):
    anio_cierre = serializers.IntegerField()
    anio_nuevo = serializers.IntegerField()

class EjecutarCierreSerializer(CierreAnioSerializer):
    confirmar = serializers.BooleanField()


class VistaCargosSerializer(serializers.ModelSerializer):

    class Meta:
        model  = VistaCargos
        fields = [
            "id_vista",
            "id_cargo",
            "cuentahabiente_id",
            "tipo_cargo_nombre",
            "cargo_fecha",
            "anio_cargo",
            "saldo_restante_cargo",
            "cargo_activo",
            "desglose_pagos",
        ]

class EstadoCuentaNewSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EstadoCuentaNew
        fields = [
            "id", "id_cobrador", "nombre_cobrador",
            "id_cuentahabiente", "numero_contrato", "nombre_cuentahabiente",
            "calle", "servicio", "saldo_pendiente_actualizado",
            "deuda_actualizada", "anio", "tipo_movimiento", "json_pagos",
        ]

class ReporteCargosSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ReporteCargos
        fields = [
            "id",
            "id_cobrador",
            "nombre_cobrador",
            "id_cuentahabiente",
            "numero_contrato",
            "nombre_cuentahabiente",
            "calle",
            "tipo_cargo",
            "fecha_cargo",
            "saldo_restante_cargo",
            "estatus_cargo",
            "fecha_pago",
            "monto_recibido",
        ]