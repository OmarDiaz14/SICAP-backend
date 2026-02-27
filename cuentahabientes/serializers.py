# cuentahabientes/serializers.py
from django.utils import timezone
from django.db.models import Max
from decimal import Decimal

from rest_framework import serializers

from cargos.models import Cargo, TipoCargo
from .models import Cuentahabiente

class CuentahabienteSerializer(serializers.ModelSerializer):
    
    es_toma_nueva = serializers.BooleanField(write_only=True, required=False, default=False)
    class Meta:

        model = Cuentahabiente
        fields = (
            "id_cuentahabiente", "numero_contrato", "nombres", "ap", "am",
            "calle", "numero", "telefono",
            "colonia",
            "servicio",           # <- el cliente elige el servicio (ID)
            "deuda",
            "saldo_pendiente",    # <- lo calculamos; solo lectura al crear
            "es_toma_nueva",
        )
        read_only_fields = ("id_cuentahabiente", "saldo_pendiente")

    def validate_numero_contrato(self, value):
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

        ultimo = (
            Cuentahabiente.objects
            .filter(numero_contrato__gte=2000)
            .aggregate(max_num=Max("numero_contrato"))
        )["max_num"]

        if ultimo:
            nuevo_numero = ultimo + 1
        else:
            nuevo_numero = 2000

        validated_data["numero_contrato"] = nuevo_numero

        srv = validated_data["servicio"]         # instancia de Servicio (por FK)
        validated_data["saldo_pendiente"] = srv.costo  # Decimal exacto

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
                            EstadoCuenta, RCuentahabientes
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
            "deuda",
            "fecha_pago",
            "monto_recibido",
            "anio",
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