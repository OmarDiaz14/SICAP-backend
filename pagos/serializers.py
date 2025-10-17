from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from rest_framework import serializers
from .models import Pago
from cuentahabientes.models import Cuentahabiente
from descuento.models import Descuento


class PagoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para CREAR pagos.
    - 'cobrador' se toma del request (no viene en el body).
    - 'monto_descuento' se calcula usando el porcentaje del descuento elegido.
    - Actualiza el saldo_pendiente del cuentahabiente en la misma transacción.
    """
    # Solo permitir que el cliente mande: cuentahabiente, descuento (opcional), fecha, monto, mes, anio
    descuento = serializers.PrimaryKeyRelatedField(
        queryset=Descuento.objects.all(), required=False, allow_null=True
    )
    cuentahabiente = serializers.PrimaryKeyRelatedField(
        queryset=Cuentahabiente.objects.all()
    )

    class Meta:
        model = Pago
        fields = (
            "id_pago",
            "descuento",
            "cuentahabiente",
            "fecha_pago",
            "monto_recibido",
            "monto_descuento",  # <- lo calculamos; lo dejamos read_only
            "mes",
            "anio",
        )
        read_only_fields = ("id_pago", "monto_descuento")

    def validate_monto_recibido(self, value):
        if value is None or Decimal(value) <= 0:
            raise serializers.ValidationError("El monto recibido debe ser mayor a 0.")
        return value

    def validate(self, attrs):
        # (Opcional) valida mes/año/formato adicional
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """
        1) Calcula monto_descuento = monto_recibido * (porcentaje/100) si hay descuento.
        2) Baja el saldo_pendiente del cuentahabiente = saldo - (monto_recibido + monto_descuento).
        3) Setea el cobrador desde request.user.
        """
        request = self.context.get("request")
        if not request or not getattr(request.user, "is_authenticated", False):
            raise serializers.ValidationError("Autenticación requerida.")

        cobrador = request.user  # viene de tu auth JWT -> Cobrador
        ch: Cuentahabiente = validated_data["cuentahabiente"]

        # Lock pesimista para evitar race (dos pagos al mismo tiempo)
        ch_locked = Cuentahabiente.objects.select_for_update().get(pk=ch.pk)

        monto_recibido = Decimal(validated_data["monto_recibido"])
        descuento_obj: Descuento | None = validated_data.get("descuento")

        # Calcula descuento (si hay)
        monto_descuento = Decimal("0.00")
        if descuento_obj:
            # porcentaje es Decimal con 2 decimales (ej 10.00)
            porcentaje = Decimal(descuento_obj.porcentaje)
            monto_descuento = (monto_recibido * porcentaje / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        # Nuevo saldo = saldo actual - (monto + descuento)
        saldo_actual = Decimal(ch_locked.saldo_pendiente or 0)
        nuevo_saldo = saldo_actual - (monto_recibido + monto_descuento)
        if nuevo_saldo < 0:
            nuevo_saldo = Decimal("0.00")

        # Persistimos el nuevo saldo
        ch_locked.saldo_pendiente = nuevo_saldo
        ch_locked.save(update_fields=["saldo_pendiente"])

        # Crear pago con cobrador del request y monto_descuento calculado
        pago = Pago.objects.create(
            descuento=descuento_obj,
            cobrador=cobrador,
            cuentahabiente=ch_locked,
            fecha_pago=validated_data["fecha_pago"],
            monto_recibido=monto_recibido,
            monto_descuento=monto_descuento,
            mes=validated_data["mes"],
            anio=validated_data["anio"],
        )
        return pago


class PagoReadSerializer(serializers.ModelSerializer):
    """
    Serializer para LEER pagos con datos enriquecidos.
    """
    descuento_nombre = serializers.CharField(source="descuento.nombre_descuento", read_only=True)
    cobrador_usuario = serializers.CharField(source="cobrador.usuario", read_only=True)
    cuentahabiente_nombre = serializers.SerializerMethodField()
    saldo_pendiente_actual = serializers.SerializerMethodField()

    class Meta:
        model = Pago
        fields = (
            "id_pago",
            "descuento", "descuento_nombre",
            "cobrador", "cobrador_usuario",
            "cuentahabiente", "cuentahabiente_nombre",
            "fecha_pago",
            "monto_recibido",
            "monto_descuento",
            "mes",
            "anio",
            "saldo_pendiente_actual",  # estado actual del CH tras el pago
        )

    def get_cuentahabiente_nombre(self, obj):
        ch = obj.cuentahabiente
        return f"{ch.nombres} {ch.ap} {ch.am}"

    def get_saldo_pendiente_actual(self, obj):
        return obj.cuentahabiente.saldo_pendiente
