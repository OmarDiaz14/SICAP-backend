from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from .models import Pago
from cuentahabientes.models import Cuentahabiente
from descuento.models import Descuento


class PagoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para CREAR pagos.
    Ajustado para manejar zona horaria local (America/Mexico_City).
    - Convierte fecha_pago naive a hora local (MX)
    - Deriva mes y año automáticamente desde fecha_pago
    - Valida coherencia si el front manda mes/anio
    """

    # ---- Campos ----
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
            "comentarios",
        )
        # ✅ marcamos mes y año como derivados (no los pone el front)
        read_only_fields = ("id_pago", "monto_descuento", "mes", "anio")

    # ---- Función auxiliar ----
    def _month_year_from_fecha(self, fecha_pago):
        """Extrae mes y año, haciendo aware si es datetime naive"""
        if isinstance(fecha_pago, datetime):
            # ✅ Si viene sin tz (naive), asumimos hora local MX
            if timezone.is_naive(fecha_pago):
                fecha_pago = timezone.make_aware(fecha_pago, timezone.get_default_timezone())
            fecha_local = timezone.localtime(fecha_pago)
            return fecha_local.month, fecha_local.year
        elif isinstance(fecha_pago, date):
            return fecha_pago.month, fecha_pago.year
        raise serializers.ValidationError("`fecha_pago` debe ser date o datetime.")

    # ---- Validación de coherencia ----
    def validate(self, attrs):
        fecha_pago = attrs.get("fecha_pago")
        if fecha_pago is not None:
            m, y = self._month_year_from_fecha(fecha_pago)
            mes = attrs.get("mes")
            anio = attrs.get("anio")
            # ✅ Si el front insiste en mandar mes/anio, se validan contra la fecha real
            if mes is not None and str(mes).zfill(2) != str(m).zfill(2):
                raise serializers.ValidationError("`mes` no coincide con `fecha_pago`.")
            if anio is not None and int(anio) != int(y):
                raise serializers.ValidationError("`anio` no coincide con `fecha_pago`.")
        return attrs

    # ---- Cálculo del estatus de deuda ----
    def calcular_estatus_deuda(self, cuentahabiente, referencia_dt=None):
        # ✅ Usa hora local MX (no UTC) y permite referencia retroactiva
        ref = referencia_dt or timezone.localtime()
        if isinstance(ref, datetime):
            ref_local = timezone.localtime(
                ref if timezone.is_aware(ref)
                else timezone.make_aware(ref, timezone.get_default_timezone())
            )
            mes_actual = ref_local.month
        elif isinstance(ref, date):
            mes_actual = ref.month
        else:
            mes_actual = timezone.localtime().month

        # ---- Lógica original ----
        if cuentahabiente.saldo_pendiente <= 0:
            return 'pagado'
        if not cuentahabiente.servicio:
            return 'adeudo'

        costo_anual = Decimal(cuentahabiente.servicio.costo)
        total_pagado = costo_anual - Decimal(cuentahabiente.saldo_pendiente)
        if total_pagado <= 0:
            return 'adeudo'

        costo_mensual = costo_anual / 12
        meses_pagados = (total_pagado / costo_mensual) if costo_mensual > 0 else 0
        meses_esperados = mes_actual

        if meses_pagados >= 12:
            return 'pagado'
        elif meses_pagados >= (meses_esperados - 0.5):
            return 'corriente'
        elif meses_pagados >= (meses_esperados / 2):
            return 'rezagado'
        else:
            return 'adeudo'

    # ---- Creación del pago ----
    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")
        if not request or not getattr(request.user, "is_authenticated", False):
            raise serializers.ValidationError("Autenticación requerida.")

        cobrador = request.user
        ch = validated_data["cuentahabiente"]
        ch_locked = Cuentahabiente.objects.select_for_update().get(pk=ch.pk)

        # ✅ Normaliza fecha_pago
        fecha_pago = validated_data["fecha_pago"]
        if isinstance(fecha_pago, datetime) and timezone.is_naive(fecha_pago):
            fecha_pago = timezone.make_aware(fecha_pago, timezone.get_default_timezone())

        # ✅ Deriva mes/anio automáticamente
        mes_num, anio_num = self._month_year_from_fecha(fecha_pago)
        mes_str = f"{mes_num:02d}"

        monto_recibido = Decimal(validated_data["monto_recibido"])
        descuento_obj = validated_data.get("descuento")
        comentarios = validated_data.pop("comentarios", None)

        # ---- Lógica de montos ----
        monto_descuento = Decimal("0.00")
        if descuento_obj:
            monto_descuento = Decimal(str(descuento_obj.porcentaje))

        total_a_restar = monto_recibido + monto_descuento
        saldo_actual = Decimal(str(ch_locked.saldo_pendiente or 0))
        nuevo_saldo_decimal = saldo_actual - total_a_restar
        nuevo_saldo = int(nuevo_saldo_decimal.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        if nuevo_saldo < 0:
            nuevo_saldo = 0

        ch_locked.saldo_pendiente = nuevo_saldo
        nuevo_estatus = self.calcular_estatus_deuda(ch_locked, referencia_dt=fecha_pago)
        ch_locked.deuda = nuevo_estatus
        ch_locked.save(update_fields=["saldo_pendiente", "deuda"])

        monto_descuento_int = int(monto_descuento.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

        # ✅ Se guarda la fecha ya normalizada (aware)
        pago = Pago.objects.create(
            descuento=descuento_obj,
            cobrador=cobrador,
            cuentahabiente=ch_locked,
            fecha_pago=fecha_pago,
            monto_recibido=int(monto_recibido),
            monto_descuento=monto_descuento_int,
            mes=mes_str,
            anio=anio_num,
            comentarios=comentarios,
        )
        return pago


class PagoReadSerializer(serializers.ModelSerializer):
    """
    Serializer para LEER pagos.
    ✅ SOLUCIÓN: Retorna fecha_pago como string YYYY-MM-DD sin timezone
    """
    descuento_nombre = serializers.CharField(source="descuento.nombre_descuento", read_only=True)
    cobrador_usuario = serializers.CharField(source="cobrador.usuario", read_only=True)
    cuentahabiente_nombre = serializers.SerializerMethodField()
    saldo_pendiente_actual = serializers.SerializerMethodField()
    estatus_deuda = serializers.CharField(source="cuentahabiente.deuda", read_only=True)
    
    # ✅ SOLUCIÓN: Sobrescribir fecha_pago para retornar solo la fecha
    fecha_pago = serializers.SerializerMethodField()

    class Meta:
        model = Pago
        fields = (
            "id_pago",
            "descuento", "descuento_nombre",
            "cobrador", "cobrador_usuario",
            "cuentahabiente", "cuentahabiente_nombre",
            "fecha_pago",  # ✅ Ahora retorna YYYY-MM-DD
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

    def get_fecha_pago(self, obj):
        """
        ✅ CLAVE: Retorna fecha como string YYYY-MM-DD sin conversión de timezone
        """
        fp = obj.fecha_pago
        
        # Si es DateTimeField, extraer solo la fecha en hora local
        if isinstance(fp, datetime):
            fecha_local = timezone.localtime(fp)
            return fecha_local.date().isoformat()
        
        # Si es DateField, retornar directamente
        elif isinstance(fp, date):
            return fp.isoformat()
        
        # Fallback
        return str(fp)