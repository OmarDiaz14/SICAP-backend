from rest_framework import serializers
from .models import Servicio

class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = ['id_tipo_servicio', 'nombre', 'costo']
        read_only_fields = ['id_tipo_servicio']
