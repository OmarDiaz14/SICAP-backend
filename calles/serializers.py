from rest_framework import serializers
from .models import Calle

class CalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calle
        fields = ['id_calle', 'nombre_calle', 'activo']
        read_only_fields = ['id_calle']

    def validate_nombre_calle(self, value):
        # Evita calles duplicadas
        qs = Calle.objects.filter(nombre_calle__iexact=value.strip())
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe una calle con ese nombre.")
        return value.strip()