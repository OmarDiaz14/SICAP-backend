from rest_framework import serializers
from .models import Cargo, TipoCargo

class TipoCargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoCargo
        fields = ("id", "nombre", "monto")

class CargoSerializer(serializers.ModelSerializer):
    cuentahabiente_nombre = serializers.SerializerMethodField()
    tipo_cargo_detalle = TipoCargoSerializer(source="tipo_cargo", read_only=True)

    class Meta:
        model = Cargo 
        fields = ("id_cargo", "cuentahabiente", "cuentahabiente_nombre", 
                 "tipo_cargo", "tipo_cargo_detalle", "saldo_restante_cargo", "fecha_cargo", "activo")
        
        read_only_fields = ("id_cargo", "saldo_restante_cargo")

    def get_cuentahabiente_nombre(self, obj):
        ch = obj.cuentahabiente
        return f"{ch.nombres} {ch.ap} {ch.am}"