# asignaciones/serializers.py
from rest_framework import serializers
from .models import Asignacion
from cobrador.models import Cobrador
from sector.models import Sector


class AsignacionSerializer(serializers.ModelSerializer):
    # Escritura por ID (PK). Para leer, formateamos salida en to_representation().
    cobrador = serializers.PrimaryKeyRelatedField(
        queryset=Cobrador.objects.all(), write_only=True
    )
    sector = serializers.PrimaryKeyRelatedField(
        queryset=Sector.objects.all(), write_only=True
    )

    class Meta:
        model = Asignacion
        fields = ["id_asignacion", "cobrador", "sector", "fecha_asignacion"]
        read_only_fields = ["id_asignacion"]

    def validate(self, attrs):
        """
        Evita duplicar la misma dupla (cobrador, sector).
        Considera también el caso de actualización (excluye self.instance).
        """
        c = attrs.get("cobrador")
        s = attrs.get("sector")
        if c is None or s is None:
            return attrs

        qs = Asignacion.objects.filter(cobrador_id=c.pk, sector_id=s.pk)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "El cobrador ya está asignado a ese sector."
            )
        return attrs

    def to_representation(self, instance):
        """
        Devuelve datos anidados legibles de cobrador y sector.
        """
        rep = super().to_representation(instance)
        rep["cobrador"] = {
            "id_cobrador": instance.cobrador.pk,
            "nombre": instance.cobrador.nombre,
            "apellidos": instance.cobrador.apellidos,
            "usuario": instance.cobrador.usuario,
            "email": instance.cobrador.email,
            "role": instance.cobrador.role,
        }
        rep["sector"] = {
            "id_sector": instance.sector.pk,
            "nombre_sector": instance.sector.nombre_sector,
            "descripcion": instance.sector.descripcion,
        }
        return rep
