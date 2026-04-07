from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework import serializers
from cobrador.models import Cobrador
from equipos.models import Equipo, EquipoCobrador

class EquipoCobradorSerializer(serializers.ModelSerializer):
    """Para leer los cobradores anidados dentro de un equipo."""
    id_cobrador = serializers.IntegerField(source='cobrador.id_cobrador', read_only=True)
    nombre = serializers.CharField(source='cobrador.nombre', read_only=True)
    apellidos = serializers.CharField(source='cobrador.apellidos', read_only=True)

    class Meta:
        model = EquipoCobrador
        fields = ['id_cobrador', 'nombre', 'apellidos', 'fecha_ingreso']


class EquipoSerializer(serializers.ModelSerializer):

    cobradores_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    fecha_ingreso_cobradores = serializers.DateField(write_only=True, required=False)

    cobradores = EquipoCobradorSerializer(source='miembros', many=True, read_only=True)

    calle_detalle = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Equipo
        fields = [
            'id_equipo', 'nombre_equipo',
            'calle', 'calle_detalle',
            'fecha_asignacion', 'fecha_termino',
            'activo',
            'cobradores',
            'cobradores_ids', 'fecha_ingreso_cobradores',
        ]
        read_only_fields = ['id_equipo']

    def get_calle_detalle(self, obj):
        return {
            'id_calle': obj.calle.id_calle,
            'nombre_calle': obj.calle.nombre_calle,
        }

    def _validar_cobradores_disponibles(self, cobradores_ids, equipo_actual=None):
        """Verifica que ningún cobrador esté en otro equipo activo."""
        for cobrador_id in cobradores_ids:
            qs = EquipoCobrador.objects.filter(
                cobrador_id=cobrador_id,
                activo=True
            )
            if equipo_actual:
                qs = qs.exclude(equipo=equipo_actual)

            if qs.exists():
                equipo_ocupado = qs.first().equipo.nombre_equipo
                raise serializers.ValidationError(
                    {"cobradores_ids": f"El cobrador con id {cobrador_id} ya pertenece al equipo activo '{equipo_ocupado}'."}
                )
            
    def create(self, validated_data):
        cobradores_ids = validated_data.pop('cobradores_ids', [])
        fecha_ingreso = validated_data.pop('fecha_ingreso_cobradores', validated_data['fecha_asignacion'])

        self._validar_cobradores_disponibles(cobradores_ids)

        equipo = Equipo.objects.create(**validated_data)

        for cobrador_id in cobradores_ids:
            try:
                cobrador = Cobrador.objects.get(pk=cobrador_id)
            except Cobrador.DoesNotExist:
                raise DRFValidationError({"cobradores_ids": f"No existe un cobrador con id {cobrador_id}."})
            
            try:
                EquipoCobrador.objects.create(
                    equipo=equipo,
                    cobrador=cobrador,
                    fecha_ingreso=fecha_ingreso
                )
            except DjangoValidationError as e:
                raise DRFValidationError(e.message_dict)

        return equipo

    def update(self, instance, validated_data):
        # Actualiza campos basicos del equipo
        cobradores_ids = validated_data.pop('cobradores_ids', None)
        fecha_ingreso = validated_data.pop('fecha_ingreso_cobradores', instance.fecha_asignacion)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Si se registran cobradores nuevos se agregan sin borrar los existentes
        if cobradores_ids is not None:
            for cobrador_id in cobradores_ids:
                cobrador = Cobrador.objects.get(pk=cobrador_id)
                EquipoCobrador.objects.get_or_create(
                    equipo=instance,
                    cobrador=cobrador,
                    defaults={'fecha_ingreso': fecha_ingreso}
                )

        return instance