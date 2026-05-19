from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import django_filters
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from cargos.models import Cargo, TipoCargo
from pagos.models import Pago
from cobrador.permissions import IsDirectivoOrCobradorCreate

from .models import CierreAnual, Cuentahabiente
from .serializers import (
    CierreAnioSerializer, CuentahabienteSerializer, EjecutarCierreSerializer,
    RCuentahabientesSerializer, VistaPagosSerializer, VistaHistorialSerializer,
    VistaDeudoresSerializer, VistaProgresoSerializer, EstadoCuentaSerializer,
    EstadoCuentaResumenSerializer, VistaCargosSerializer,
    EstadoCuentaNewSerializer, ReporteCargosSerializer,
    ReportePadronGeneralSerializer,
)
from .models_views import (
    RCuentahabientes, VistaHistorial, VistaPagos, VistaDeudores,
    VistaProgreso, EstadoCuenta, EstadoCuentaResumen, VistaCargos,
    EstadoCuentaNew, ReporteCargos, ReportePadronGeneral,
)


# ══════════════════════════════════════════════════════════════════════
# Cuentahabiente
# ══════════════════════════════════════════════════════════════════════

class CuentahabienteViewSet(viewsets.ModelViewSet):
    queryset = Cuentahabiente.objects.select_related(
        "colonia", "servicio"
    ).order_by("id_cuentahabiente")
    serializer_class   = CuentahabienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = [
        "numero_contrato", "nombres", "ap", "am",
        "telefono", "colonia__nombre_colonia",
    ]
    ordering_fields = ["id_cuentahabiente", "numero_contrato", "nombres"]
    ordering        = ["id_cuentahabiente"]

    # ── POST /cuentahabientes/{id}/activar/ ───────────────────────────

    @action(detail=True, methods=["post"], url_path="activar")
    def activar(self, request, pk=None):
        cuenta = self.get_object()

        if cuenta.fecha_activacion is not None:
            return Response(
                {"error": "La cuenta ya fue activada previamente."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        fecha_str = request.data.get("fecha_activacion")
        if fecha_str:
            try:
                fecha_activacion = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Formato de fecha inválido. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            fecha_activacion = date.today()

        with transaction.atomic():
            cuenta.fecha_activacion = fecha_activacion
            campos_a_guardar        = ["fecha_activacion"]
            cobro_aplicado          = False
            detalle_cobro           = ""

            # ── PERMANENTE: suma el año completo al saldo ─────────────────
            if cuenta.tipo_cuenta == "permanente" and cuenta.servicio:
                tarifa_anual = cuenta.tarifa_anual

                cuenta.saldo_pendiente = (
                    decimal_seguro(cuenta.saldo_pendiente) + tarifa_anual
                )
                cuenta.deuda     = "adeudo"
                campos_a_guardar += ["saldo_pendiente", "deuda"]
                cobro_aplicado   = True
                detalle_cobro    = (
                    f"Cuenta permanente: se sumó el año completo "
                    f"${tarifa_anual} al saldo pendiente."
                )

            # ── PARCIAL: regla del día 15, suma un mes al saldo ───────────
            elif cuenta.tipo_cuenta == "parcial" and cuenta.servicio:
                if Cuentahabiente.aplica_cobro_por_dia(fecha_activacion.day):
                    tarifa_mensual = cuenta.tarifa_mensual

                    cuenta.saldo_pendiente = (
                        decimal_seguro(cuenta.saldo_pendiente) + tarifa_mensual
                    )
                    cuenta.deuda     = "adeudo"
                    campos_a_guardar += ["saldo_pendiente", "deuda"]
                    cobro_aplicado   = True
                    detalle_cobro    = (
                        f"Cuenta parcial: activado el día {fecha_activacion.day} "
                        f"(antes o en el 15) → se sumó ${tarifa_mensual} al saldo."
                    )
                else:
                    detalle_cobro = (
                        f"Cuenta parcial: activado el día {fecha_activacion.day} "
                        f"(después del 15) → el cobro inicia el mes siguiente."
                    )

            cuenta.save(update_fields=campos_a_guardar)

        return Response({
            "mensaje":          "Cuenta activada correctamente.",
            "numero_contrato":  cuenta.numero_contrato,
            "tipo_cuenta":      cuenta.tipo_cuenta,
            "fecha_activacion": fecha_activacion,
            "cobro_aplicado":   cobro_aplicado,
            "detalle":          detalle_cobro,
            "saldo_pendiente":  str(cuenta.saldo_pendiente),
        }, status=status.HTTP_200_OK)


    @action(detail=True, methods=["post"], url_path="desactivar")
    def desactivar(self, request, pk=None):
        cuenta = self.get_object()

        if cuenta.fecha_activacion is None:
            return Response(
                {"error": "La cuenta no ha sido activada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if cuenta.fecha_desactivacion is not None:
            return Response(
                {"error": "La cuenta ya fue desactivada anteriormente."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        fecha_str = request.data.get("fecha_desactivacion")
        if fecha_str:
            try:
                fecha_desactivacion = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Formato de fecha inválido. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            fecha_desactivacion = date.today()

        with transaction.atomic():
            cuenta.fecha_desactivacion = fecha_desactivacion
            campos_a_guardar           = ["fecha_desactivacion"]
            cobro_aplicado             = False
            detalle_cobro              = ""

            # ── PERMANENTE: día > 15 suma 1 mes proporcional al saldo ─────
            if cuenta.tipo_cuenta == "permanente" and cuenta.servicio:
                if not Cuentahabiente.aplica_cobro_por_dia(fecha_desactivacion.day):
                    tarifa_mensual = cuenta.tarifa_mensual

                    cuenta.saldo_pendiente = (
                        decimal_seguro(cuenta.saldo_pendiente) + tarifa_mensual
                    )
                    cuenta.deuda     = "adeudo"
                    campos_a_guardar += ["saldo_pendiente", "deuda"]
                    cobro_aplicado   = True
                    detalle_cobro    = (
                        f"Cuenta permanente: desactivada el día {fecha_desactivacion.day} "
                        f"(después del 15) → se sumó 1 mes proporcional "
                        f"${tarifa_mensual} al saldo."
                    )
                else:
                    detalle_cobro = (
                        f"Cuenta permanente: desactivada el día {fecha_desactivacion.day} "
                        f"(antes o en el 15) → no se sumó nada al saldo."
                    )

            # ── PARCIAL: día > 15 suma un mes al saldo ────────────────────
            elif cuenta.tipo_cuenta == "parcial" and cuenta.servicio:
                if not Cuentahabiente.aplica_cobro_por_dia(fecha_desactivacion.day):
                    tarifa_mensual = cuenta.tarifa_mensual

                    cuenta.saldo_pendiente = (
                        decimal_seguro(cuenta.saldo_pendiente) + tarifa_mensual
                    )
                    cuenta.deuda     = "adeudo"
                    campos_a_guardar += ["saldo_pendiente", "deuda"]
                    cobro_aplicado   = True
                    detalle_cobro    = (
                        f"Cuenta parcial: desactivada el día {fecha_desactivacion.day} "
                        f"(después del 15) → se sumó ${tarifa_mensual} al saldo."
                    )
                else:
                    detalle_cobro = (
                        f"Cuenta parcial: desactivada el día {fecha_desactivacion.day} "
                        f"(antes o en el 15) → no se sumó nada al saldo."
                    )

            cuenta.save(update_fields=campos_a_guardar)

        return Response({
            "mensaje":             "Cuenta desactivada correctamente.",
            "numero_contrato":     cuenta.numero_contrato,
            "tipo_cuenta":         cuenta.tipo_cuenta,
            "fecha_desactivacion": fecha_desactivacion,
            "cobro_aplicado":      cobro_aplicado,
            "detalle":             detalle_cobro,
            "saldo_pendiente":     str(cuenta.saldo_pendiente),
        }, status=status.HTTP_200_OK)
# ══════════════════════════════════════════════════════════════════════
# Vistas de solo lectura
# ══════════════════════════════════════════════════════════════════════

class VistaPagosViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = VistaPagos.objects.all()
    serializer_class = VistaPagosSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter,
                        filters.OrderingFilter]
    filterset_fields = ["anio", "estatus_deuda", "nombre_servicio",
                        "numero_contrato"]
    search_fields    = ["nombre_completo", "numero_contrato"]
    ordering_fields  = ["anio", "pagos_totales", "numero_contrato"]


class VistaHistorialViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = VistaHistorial.objects.all()
    serializer_class = VistaHistorialSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter,
                        filters.OrderingFilter]
    filterset_fields = ["anio", "mes", "numero_contrato", "fecha_pago"]
    search_fields    = ["numero_contrato", "cobrador"]
    ordering_fields  = ["fecha_pago", "anio", "numero_contrato"]


class VistaDeudoresViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = VistaDeudores.objects.all().order_by("-monto_total")
    serializer_class = VistaDeudoresSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter,
                        filters.OrderingFilter]
    filterset_fields = ["estatus", "nombre_colonia"]
    search_fields    = ["nombre_cuentahabiente", "nombre_colonia"]
    ordering_fields  = ["monto_total", "nombre_cuentahabiente", "nombre_colonia"]
    ordering         = ["-monto_total"]


class VistaProgresoPublicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset           = VistaProgreso.objects.all()
    serializer_class   = VistaProgresoSerializer
    permission_classes = [AllowAny]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter,
                          filters.OrderingFilter]
    filterset_fields   = ["estatus", "progreso", "numero_contrato", "anio_pago"]
    search_fields      = ["nombre", "numero_contrato"]
    ordering_fields    = ["numero_contrato", "total", "saldo",
                          "progreso", "anio_pago"]
    ordering           = ["numero_contrato", "anio_pago"]


class EstadoCuentaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset           = EstadoCuenta.objects.all()
    serializer_class   = EstadoCuentaSerializer
    permission_classes = [IsAuthenticated & IsDirectivoOrCobradorCreate]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter,
                          filters.OrderingFilter]
    filterset_fields   = ["id_cuentahabiente", "anio", "tipo_movimiento"]
    search_fields      = ["nombre", "direccion", "telefono", "numero_contrato"]
    ordering_fields    = ["id_cuentahabiente", "numero_contrato",
                          "fecha_pago", "anio"]
    ordering           = ["numero_contrato", "anio", "fecha_pago"]


class VistaCargosViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = VistaCargosSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ["cuentahabiente_id", "cargo_activo", "anio_cargo"]
    ordering_fields    = ["cargo_fecha", "saldo_restante_cargo"]

    def get_queryset(self):
        return VistaCargos.objects.all()


class EstadoCuentaResumenViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = EstadoCuentaResumenSerializer
    permission_classes = [IsAuthenticated & IsDirectivoOrCobradorCreate]
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ["id_cuentahabiente", "numero_contrato"]

    def get_queryset(self):
        id_cuentahabiente = self.request.query_params.get("id_cuentahabiente")
        numero_contrato   = self.request.query_params.get("numero_contrato")
        if not id_cuentahabiente and not numero_contrato:
            return EstadoCuentaResumen.objects.none()
        return EstadoCuentaResumen.objects.all()


class RCuentahabientesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset           = RCuentahabientes.objects.all().order_by(
                            "id_cuentahabiente")
    serializer_class   = RCuentahabientesSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter,
                          filters.OrderingFilter]
    filterset_fields   = ["id_cuentahabiente", "estatus",
                          "numero_contrato", "nombre"]
    search_fields      = ["nombre", "calle", "nombre_colonia",
                          "telefono", "numero_contrato"]
    ordering_fields    = ["id_cuentahabiente", "numero_contrato",
                          "saldo_pendiente", "total_pagado"]
    ordering           = ["id_cuentahabiente"]


# ══════════════════════════════════════════════════════════════════════
# Cierre anual
# ══════════════════════════════════════════════════════════════════════

class CierreAnualViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsDirectivoOrCobradorCreate]

    def create(self, request):
        """POST /cierre-anual/ → previsualiza sin ejecutar."""
        serializer = CierreAnioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if CierreAnual.objects.filter(
            anio=data["anio_nuevo"], ejecutado=True
        ).exists():
            return Response(
                {"error": "El cierre anual ya fue ejecutado."},
                status=status.HTTP_409_CONFLICT,
            )

        resumen = cambio_anio(data["anio_nuevo"])
        return Response(resumen, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="confirmar")
    def confirmar(self, request):
        """POST /cierre-anual/confirmar/ → ejecuta el cierre definitivo."""
        serializer = EjecutarCierreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not data["confirmar"]:
            return Response(
                {"error": "Confirmación requerida para ejecutar el cierre anual."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.user.role not in ["admin", "supervisor"]:
            return Response(
                {"error": "Permisos insuficientes para ejecutar el cierre anual."},
                status=status.HTTP_403_FORBIDDEN,
            )

        anio_cierre = data["anio_cierre"]
        anio_nuevo  = data["anio_nuevo"]

        with transaction.atomic():

            cierre, _ = CierreAnual.objects.select_for_update().get_or_create(
                anio=anio_nuevo,
                defaults={"ejecutado_por": request.user},
            )
            if cierre.ejecutado:
                return Response(
                    {"error": "El cierre anual ya fue ejecutado."},
                    status=status.HTTP_409_CONFLICT,
                )

            tipo_cierre, _ = TipoCargo.objects.get_or_create(
                nombre="CIERRE_ANUAL",
                defaults={"monto": Decimal("0.00"), "automatico": True},
            )

            # ── Solo cuentas PERMANENTES activas ──────────────────────
            # Parciales se excluyen: su cobro es mensual via cron
            # Desactivadas se excluyen: ya no tienen servicio activo
            ids = list(
                Cuentahabiente.objects
                .filter(
                    tipo_cuenta="permanente",
                    fecha_activacion__isnull=False,
                    fecha_desactivacion__isnull=True,
                )
                .select_for_update()
                .values_list("id_cuentahabiente", flat=True)
            )
            cuentahabientes = list(
                Cuentahabiente.objects
                .filter(id_cuentahabiente__in=ids)
                .select_related("servicio")
            )

            # ── Pagos anticipados del nuevo año ───────────────────────
            pagos_nuevo_anio = list(
                Pago.objects.filter(anio=anio_nuevo)
                .select_related("descuento")
                .order_by("cuentahabiente_id", "-fecha_pago")
            )

            pagos_por_cuenta = {}
            for p in pagos_nuevo_anio:
                cid = p.cuentahabiente_id
                pagos_por_cuenta[cid] = (
                    pagos_por_cuenta.get(cid, Decimal("0")) +
                    decimal_seguro(p.monto_recibido)
                )

            descuento_por_cuenta = {}
            for p in pagos_nuevo_anio:
                cid = p.cuentahabiente_id
                if cid not in descuento_por_cuenta:
                    if p.descuento_id and p.descuento and p.descuento.activo:
                        descuento_por_cuenta[cid] = decimal_seguro(
                            p.descuento.porcentaje
                        )

            cargos_a_crear       = []
            cuentas_a_actualizar = []
            fecha_cargo          = date(anio_nuevo, 1, 1)

            for c in cuentahabientes:
                saldo_anterior = decimal_seguro(c.saldo_pendiente)
                tarifa_base    = obtener_tarifa_cuentahabiente(c)
                descuento_fijo = descuento_por_cuenta.get(
                    c.id_cuentahabiente, Decimal("0")
                )
                tarifa_real = tarifa_base - descuento_fijo

                # Deuda del año que cierra → se convierte en cargo
                if saldo_anterior > Decimal("0"):
                    cargos_a_crear.append(
                        Cargo(
                            cuentahabiente=c,
                            tipo_cargo=tipo_cierre,
                            saldo_restante_cargo=saldo_anterior,
                            fecha_cargo=fecha_cargo,
                            activo=True,
                        )
                    )

                # Nuevo saldo = tarifa anual - pagos anticipados
                pagos_anticipados = pagos_por_cuenta.get(
                    c.id_cuentahabiente, Decimal("0")
                )
                nuevo_saldo = tarifa_real - pagos_anticipados

                if nuevo_saldo <= Decimal("0"):
                    estado_deuda = "pagado"
                elif pagos_anticipados > Decimal("0") and nuevo_saldo < tarifa_real:
                    estado_deuda = "corriente"
                else:
                    estado_deuda = "adeudo"

                c.saldo_pendiente = nuevo_saldo
                c.deuda           = estado_deuda
                cuentas_a_actualizar.append(c)

            if cargos_a_crear:
                Cargo.objects.bulk_create(cargos_a_crear, batch_size=500)

            Cuentahabiente.objects.bulk_update(
                cuentas_a_actualizar,
                ["saldo_pendiente", "deuda"],
                batch_size=500,
            )

            cierre.ejecutado     = True
            cierre.fecha         = date.today()
            cierre.ejecutado_por = request.user
            cierre.save()

        return Response({
            "status":                        "Cierre anual ejecutado correctamente.",
            "anio_cerrado":                  anio_cierre,
            "anio_nuevo":                    anio_nuevo,
            "cuentas_procesadas":            len(cuentas_a_actualizar),
            "cargos_generados":              len(cargos_a_crear),
            "cuentas_con_pagos_anticipados": len(pagos_por_cuenta),
        }, status=status.HTTP_200_OK)


# ══════════════════════════════════════════════════════════════════════
# Reportes
# ══════════════════════════════════════════════════════════════════════

class ReporteCargosFilter(django_filters.FilterSet):
    anio = django_filters.NumberFilter(
        field_name="fecha_cargo",
        lookup_expr="year",
        label="Año del cargo",
    )

    class Meta:
        model  = ReporteCargos
        fields = [
            "id_cobrador", "id_cuentahabiente",
            "estatus_cargo", "tipo_cargo", "anio",
        ]


class ReporteCargosViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = ReporteCargosSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class    = ReporteCargosFilter
    ordering_fields    = ["fecha_cargo", "fecha_pago", "saldo_restante_cargo"]

    def get_queryset(self):
        return ReporteCargos.objects.all()


class ReportePadronGeneralViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = ReportePadronGeneralSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ["anio_reporte", "id_cuentahabiente", "tipo_servicio"]
    ordering_fields    = ["anio_reporte", "numero_contrato",
                          "total_pagado_general"]

    def get_queryset(self):
        return ReportePadronGeneral.objects.all()


class EstadoCuentaNewViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = EstadoCuentaNewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = [
        "id_cuentahabiente", "anio", "deuda_actualizada",
        "tipo_movimiento", "id_cobrador",
    ]
    ordering_fields    = ["anio", "numero_contrato",
                          "saldo_pendiente_actualizado"]

    def get_queryset(self):
        return EstadoCuentaNew.objects.all()


# ══════════════════════════════════════════════════════════════════════
# Funciones auxiliares
# ══════════════════════════════════════════════════════════════════════

def decimal_seguro(valor):
    try:
        if valor in (None, "", " ", "NULL"):
            return Decimal("0")
        return Decimal(str(valor))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def obtener_tarifa_cuentahabiente(cuentahabiente):
    if not cuentahabiente.servicio:
        return Decimal("0")
    return decimal_seguro(cuentahabiente.servicio.costo)


def cambio_anio(anio_nuevo):
    """Resumen previo del cierre sin ejecutar nada. Solo permanentes activas."""
    resumen = {
        "reiniciadas":                   0,
        "con_adeudo":                    0,
        "cargo_total":                   Decimal("0.00"),
        "cuentas_con_pagos_anticipados": 0,
        "cuentas_parciales_omitidas":    0,
        "cuentas_desactivadas_omitidas": 0,
    }

    pagos_anticipados_ids = set(
        Pago.objects.filter(anio=anio_nuevo)
        .values_list("cuentahabiente_id", flat=True)
        .distinct()
    )

    for c in Cuentahabiente.objects.select_related("servicio"):
        # Parciales y desactivadas no entran en el cierre
        if c.tipo_cuenta == "parcial":
            resumen["cuentas_parciales_omitidas"] += 1
            continue
        if c.fecha_desactivacion is not None:
            resumen["cuentas_desactivadas_omitidas"] += 1
            continue

        tarifa       = obtener_tarifa_cuentahabiente(c)
        saldo_actual = decimal_seguro(c.saldo_pendiente)

        if saldo_actual == 0:
            resumen["reiniciadas"] += 1
        else:
            resumen["con_adeudo"] += 1

        resumen["cargo_total"] += tarifa

        if c.id_cuentahabiente in pagos_anticipados_ids:
            resumen["cuentas_con_pagos_anticipados"] += 1

    return resumen