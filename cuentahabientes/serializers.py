# cuentahabientes/serializers.py
from rest_framework import serializers
from .models import Cuentahabiente

class CuentahabienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuentahabiente
        fields = (
            "id_cuentahabiente", "numero_contrato", "nombres", "ap", "am",
            "calle", "numero", "telefono",
            "colonia",
            "servicio",           # <- el cliente elige el servicio (ID)
            "deuda",
            "saldo_pendiente",    # <- lo calculamos; solo lectura al crear
        )
        read_only_fields = ("id_cuentahabiente", "saldo_pendiente")

    def create(self, validated_data):
        """
        Al crear, establece saldo_pendiente = costo del servicio seleccionado.
        El cliente NO necesita mandar saldo_pendiente.
        """
        srv = validated_data["servicio"]         # instancia de Servicio (por FK)
        validated_data["saldo_pendiente"] = srv.costo  # Decimal exacto
        return super().create(validated_data)


# cuentahabientes/serializers.py
from rest_framework import serializers
from .models_views import VistaPagos, VistaHistorial, VistaDeudores

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