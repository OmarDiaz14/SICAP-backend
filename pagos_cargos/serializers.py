from rest_framework import serializers

from cargos.models import Cargo

class PagarCargoSerializer(serializers.Serializer):
    cuentahabiente_id = serializers.IntegerField()
    monto = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01
    )
    comentarios = serializers.CharField(
        required=False,
        allow_blank=True
    )

class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = [
            "id_cargo",
            "tipo_cargo",
            "monto_cargo",
            "fecha_cargo",
            "saldo_restante_cargo",
            "activo"
        ]