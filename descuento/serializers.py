from rest_framework import serializers
from .models import Descuento

class DescuentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Descuento
        fields = ['id_descuento', 'nombre_descuento', 'porcentaje', 'activo']
        read_only_fields = ['id_descuento']
        