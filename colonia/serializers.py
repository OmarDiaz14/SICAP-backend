from rest_framework import serializers
from .models import Colonia

class ColoniaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colonia
        fields = ('id_colonia', 'nombre_colonia', 'codigo_postal')
        read_only_fields = ('id_colonia',)