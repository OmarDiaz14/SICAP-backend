from rest_framework import serializers
from .models import Sector

class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = ['id_sector', 'nombre_sector', 'descripcion']
        read_only_fields = ['id_sector']