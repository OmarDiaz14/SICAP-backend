from rest_framework import serializers
from .models import Cuenta, Transaccion

class CuentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuenta
        fields = '__all__'

class TransaccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaccion
        fields = '__all__'

    def validate(self, attrs):
        if attrs.get('tipo') == 'egreso' and not attrs.get('requisitor'):
            raise serializers.ValidationError(
                {"requisitor": "El requisitor es obligatorio para un egreso."}
            )
        return attrs