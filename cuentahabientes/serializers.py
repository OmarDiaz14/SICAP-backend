from datetime import datetime
from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from cargos.models import Cargo, TipoCargo
from .models import Cuentahabiente
from .models_views import (
    VistaPagos, VistaHistorial, VistaDeudores, VistaProgreso,
    EstadoCuenta, RCuentahabientes, EstadoCuentaResumen,
    VistaCargos, EstadoCuentaNew, ReporteCargos, ReportePadronGeneral,
)


class CuentahabienteSerializer(serializers.ModelSerializer):

    numero_contrato = serializers.IntegerField(required=False)
    es_toma_nueva   = serializers.BooleanField(
        write_only=True, required=False, default=False
    )

    class Meta:
        model  = Cuentahabiente
        fields = (
            # ── identificación ──────────────────────────────────────
            "id_cuentahabiente",
            "numero_contrato",
            # ── datos personales ────────────────────────────────────
            "nombres", "ap", "am", "telefono",
            # ── dirección ───────────────────────────────────────────
            "calle_fk",
            "numero",
            "numero_interior",
            "colonia",
            # ── servicio / deuda ────────────────────────────────────
            "servicio",
            "deuda",
            "saldo_pendiente",
            # ── tipo y fechas ───────────────────────────────────────
            "tipo_cuenta",
            "fecha_registro",        # la captura el usuario al crear
            "fecha_activacion",      # se asigna solo desde /activar/
            "fecha_desactivacion",   # se asigna solo desde /desactivar/
            # ── write-only ──────────────────────────────────────────
            "es_toma_nueva",
        )
        read_only_fields = (
            "id_cuentahabiente",
            "saldo_pendiente",
            "fecha_activacion",
            "fecha_desactivacion",
        )

    # ── Validaciones ──────────────────────────────────────────────────

    def validate_numero_contrato(self, value):
        if value is None:
            return value
        if value <= 0:
            raise serializers.ValidationError(
                "El número de contrato no puede ser negativo."
            )
        qs = Cuentahabiente.objects.filter(numero_contrato=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "Ya existe un cuentahabiente con ese número de contrato."
            )
        return value

    def validate_fecha_registro(self, value):
        if value is None:
            raise serializers.ValidationError(
                "La fecha de registro es obligatoria."
            )
        return value

    # ── Creación ──────────────────────────────────────────────────────

    def create(self, validated_data):
        es_toma_nueva = validated_data.pop("es_toma_nueva", False)

        # ── Auto-generar número de contrato desde 2000 ────────────────
        existentes   = set(
            Cuentahabiente.objects
            .filter(numero_contrato__gte=2000)
            .values_list("numero_contrato", flat=True)
        )
        nuevo_numero = 2000
        while nuevo_numero in existentes:
            nuevo_numero += 1
        validated_data["numero_contrato"] = nuevo_numero

        # ── Saldo inicial = 0 ─────────────────────────────────────────
        # El cobro se aplica cuando se activa la cuenta, no al registrar
        validated_data["saldo_pendiente"] = Decimal("0")
        validated_data["deuda"]           = "corriente"

        cuentahabiente = super().create(validated_data)

        # ── Cargo por toma nueva (opcional) ───────────────────────────
        if es_toma_nueva:
            tipo, _ = TipoCargo.objects.get_or_create(
                nombre="Toma nueva",
                defaults={"monto": Decimal("1500.00"), "automatico": True},
            )
            Cargo.objects.create(
                cuentahabiente=cuentahabiente,
                tipo_cargo=tipo,
                fecha_cargo=timezone.now().date(),
                activo=True,
            )

        return cuentahabiente


# ── Serializers de vistas (solo lectura) ──────────────────────────────

class VistaPagosSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VistaPagos
        fields = "__all__"


class VistaHistorialSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VistaHistorial
        fields = "__all__"


class VistaDeudoresSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VistaDeudores
        fields = "__all__"


class VistaProgresoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VistaProgreso
        fields = [
            "numero_contrato", "nombre", "estatus",
            "anio_pago", "total", "saldo", "progreso",
        ]


class EstadoCuentaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EstadoCuenta
        fields = [
            "id_cuentahabiente", "numero_contrato", "nombre",
            "direccion", "telefono", "saldo_pendiente",
            "fecha_pago", "monto_recibido", "anio", "tipo_movimiento",
        ]


class EstadoCuentaResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EstadoCuentaResumen
        fields = [
            "id_cuentahabiente", "numero_contrato", "anio",
            "nombre_servicio", "estatus", "saldo_pendiente",
        ]


class RCuentahabientesSerializer(serializers.ModelSerializer):
    class Meta:
        model  = RCuentahabientes
        fields = "__all__"


class CierreAnioSerializer(serializers.Serializer):
    anio_cierre = serializers.IntegerField()
    anio_nuevo  = serializers.IntegerField()


class EjecutarCierreSerializer(CierreAnioSerializer):
    confirmar = serializers.BooleanField()


class VistaCargosSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VistaCargos
        fields = [
            "id_vista", "id_cargo", "cuentahabiente_id",
            "tipo_cargo_nombre", "cargo_fecha", "anio_cargo",
            "saldo_restante_cargo", "cargo_activo", "desglose_pagos",
        ]


class EstadoCuentaNewSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EstadoCuentaNew
        fields = [
            "id", "id_cobrador", "nombre_cobrador",
            "id_cuentahabiente", "numero_contrato", "nombre_cuentahabiente",
            "calle", "servicio", "saldo_pendiente_actualizado",
            "deuda_actualizada", "anio", "tipo_movimiento", "json_pagos",
        ]


class ReporteCargosSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ReporteCargos
        fields = [
            "id", "id_cobrador", "nombre_cobrador",
            "id_cuentahabiente", "numero_contrato", "nombre_cuentahabiente",
            "calle", "tipo_cargo", "fecha_cargo", "saldo_restante_cargo",
            "estatus_cargo", "fecha_pago", "monto_recibido",
        ]


class ReportePadronGeneralSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ReportePadronGeneral
        fields = [
            "id", "id_cuentahabiente", "numero_contrato", "nombre_usuario",
            "tipo_servicio", "costo_servicio_anual", "cantidad_abonos_servicio",
            "total_pagado_servicio", "detalle_cargos_activos_json",
            "detalle_abonos_cargos_json", "cantidad_pagos_cargos",
            "total_pagado_cargos", "total_pagado_general", "anio_reporte",
            "total_pagos_cobrados", "total_cobros_cargos",
            "total_pagos_pendientes", "total_cargos_pendientes",
            "total_recaudado_global", "total_usuarios",
        ]