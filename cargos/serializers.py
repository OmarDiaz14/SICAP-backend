from rest_framework import serializers
from .models import Cargo


class CargoSerializer(serializers.ModelSerializer):
    cuentahabiente_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Cargo 
        fields = ("id_cargo", "cuentahabiente", "cuentahabiente_nombre", 
                 "tipo_cargo", "monto_cargo","saldo_restante_cargo", "fecha_cargo", "activo")
        
        read_only_fields = ("id_cargo",)

    def get_cuentahabiente_nombre(self, obj):
        ch = obj.cuentahabiente
        return f"{ch.nombres} {ch.ap} {ch.am}"
    