from django.utils import timezone
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
    fecha_pago = serializers.DateField(required=False)

    def validate_fecha_pago(self, value):
        hoy = timezone.localtime().date()
        if value > hoy:
            raise serializers.ValidationError(
                "No se puede registrar un pago con fecha futura."
            )
        return value

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