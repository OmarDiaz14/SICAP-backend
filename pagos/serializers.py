from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from .models import Pago
from cuentahabientes.models import Cuentahabiente
from descuento.models import Descuento


class PagoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para CREAR pagos.
    - 'cobrador' se toma del request (no viene en el body).
    - 'monto_descuento' se calcula usando el porcentaje del descuento elegido.
    - Actualiza el saldo_pendiente y el estatus de deuda del cuentahabiente.
    """
    descuento = serializers.PrimaryKeyRelatedField(
        queryset=Descuento.objects.all(), required=False, allow_null=True
    )
    cuentahabiente = serializers.PrimaryKeyRelatedField(
        queryset=Cuentahabiente.objects.all()
    )

    comentarios = serializers.CharField(
        max_length=256, required=False, allow_blank=True, allow_null=True 
    )

    class Meta:
        model = Pago
        fields = (
            "id_pago",
            "descuento",
            "cuentahabiente",
            "fecha_pago",
            "monto_recibido",
            "monto_descuento",
            "mes",
            "anio",
            "comentarios"
        )
        read_only_fields = ("id_pago", "monto_descuento")

    def validate_monto_recibido(self, value):
        if value is None or Decimal(value) <= 0:
            raise serializers.ValidationError("El monto recibido debe ser mayor a 0.")
        return value

    def validate(self, attrs):
        return attrs

    def calcular_estatus_deuda(self, cuentahabiente):
        """
        Calcula el estatus de deuda basándose en:
        1. El saldo pendiente
        2. Los meses pagados vs meses transcurridos del año
        
        Retorna: 'pagado', 'corriente', 'rezagado', o 'adeudo'
        """
        # Si no hay saldo pendiente, está pagado
        if cuentahabiente.saldo_pendiente <= 0:
            return 'pagado'
        
        # Obtener el servicio y su costo anual
        if not cuentahabiente.servicio:
            return 'adeudo'
        
        costo_anual = Decimal(cuentahabiente.servicio.costo)
        
        # Calcular cuánto ha pagado (costo anual - saldo pendiente)
        total_pagado = costo_anual - Decimal(cuentahabiente.saldo_pendiente)
        
        # Si el total pagado es negativo o cero, es adeudo
        if total_pagado <= 0:
            return 'adeudo'
        
        # Obtener mes actual del año (1-12)
        mes_actual = timezone.now().month
        
        # Calcular costo mensual
        costo_mensual = costo_anual / 12
        
        # Calcular cuántos meses ha pagado realmente
        meses_pagados = (total_pagado / costo_mensual) if costo_mensual > 0 else 0
        
        # Calcular meses que debería haber pagado hasta ahora
        meses_esperados = mes_actual
        
        # Determinar estatus con tolerancia de medio mes
        # Si está pagado completamente (12 meses o más)
        if meses_pagados >= 12:
            return 'pagado'
        
        # Si ha pagado al menos hasta el mes actual (con margen de 0.5 meses)
        elif meses_pagados >= (meses_esperados - 0.5):
            return 'corriente'
        
        # Si ha pagado al menos la mitad del tiempo transcurrido
        elif meses_pagados >= (meses_esperados / 2):
            return 'rezagado'
        
        # Si ha pagado menos de la mitad o menos de 2 meses
        else:
            return 'adeudo'

    @transaction.atomic
    def create(self, validated_data):
        """
        1) Calcula monto_descuento = monto_recibido * (porcentaje/100) si hay descuento.
        2) Baja el saldo_pendiente del cuentahabiente.
        3) Actualiza el estatus de deuda del cuentahabiente.
        4) Setea el cobrador desde request.user.
        """
        request = self.context.get("request")
        if not request or not getattr(request.user, "is_authenticated", False):
            raise serializers.ValidationError("Autenticación requerida.")

        cobrador = request.user
        ch: Cuentahabiente = validated_data["cuentahabiente"]

        # Lock pesimista para evitar race conditions
        ch_locked = Cuentahabiente.objects.select_for_update().get(pk=ch.pk)

        monto_recibido = Decimal(validated_data["monto_recibido"])
        descuento_obj: Descuento | None = validated_data.get("descuento")
        comentarios = validated_data.pop("comentarios", None)

        # Calcula descuento (si hay)
        # IMPORTANTE: El descuento NO es un porcentaje, es un MONTO FIJO
        # que está almacenado en el campo "porcentaje" (mal nombrado)
        monto_descuento = Decimal("0.00")
        if descuento_obj:
            # El campo "porcentaje" en realidad contiene el MONTO del descuento
            # Ejemplo: Pago_Temprano = 60 (un mes gratis)
            #          INAPAM = 360 (mitad del servicio anual)
            monto_descuento = Decimal(str(descuento_obj.porcentaje))

        # Calcular el total a restar (monto recibido + monto del descuento FIJO)
        total_a_restar = monto_recibido + monto_descuento
        
        # Nuevo saldo = saldo actual - total_a_restar
        saldo_actual = Decimal(str(ch_locked.saldo_pendiente or 0))
        nuevo_saldo_decimal = saldo_actual - total_a_restar
        
        # Redondear a entero
        nuevo_saldo = int(nuevo_saldo_decimal.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        
        # Si el saldo queda negativo, lo dejamos en 0
        if nuevo_saldo < 0:
            nuevo_saldo = 0

        # Actualizar saldo pendiente PRIMERO
        ch_locked.saldo_pendiente = nuevo_saldo
        
        # Calcular estatus DESPUÉS de actualizar el saldo
        nuevo_estatus = self.calcular_estatus_deuda(ch_locked)
        ch_locked.deuda = nuevo_estatus
        
        # Guardar cambios en el cuentahabiente
        ch_locked.save(update_fields=["saldo_pendiente", "deuda"])

        # Crear el registro de pago
        # Convertir montos a entero para IntegerField
        monto_descuento_int = int(monto_descuento.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        
        pago = Pago.objects.create(
            descuento=descuento_obj,
            cobrador=cobrador,
            cuentahabiente=ch_locked,
            fecha_pago=validated_data["fecha_pago"],
            monto_recibido=int(monto_recibido),
            monto_descuento=monto_descuento_int,
            mes=validated_data["mes"],
            anio=validated_data["anio"],
            comentarios=comentarios,
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
    estatus_deuda = serializers.CharField(source="cuentahabiente.deuda", read_only=True)

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
            "comentarios",
            "saldo_pendiente_actual",
            "estatus_deuda",
        )

    def get_cuentahabiente_nombre(self, obj):
        ch = obj.cuentahabiente
        return f"{ch.nombres} {ch.ap} {ch.am}"

    def get_saldo_pendiente_actual(self, obj):
        return obj.cuentahabiente.saldo_pendiente