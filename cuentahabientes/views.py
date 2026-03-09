# cuentahabientes/views.py
from datetime import date
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action

from cargos.models import Cargo, TipoCargo
from pagos.models import Pago
from .models import CierreAnual, Cuentahabiente
from .serializers import CierreAnioSerializer, CuentahabienteSerializer, EjecutarCierreSerializer, RCuentahabientesSerializer, VistaPagosSerializer, VistaHistorialSerializer,VistaDeudoresSerializer, VistaProgresoSerializer, EstadoCuentaSerializer
from cobrador.permissions import IsAdminSupervisorOrCobradorCreate
from .models_views import RCuentahabientes, VistaHistorial,VistaPagos, VistaDeudores, VistaProgreso, EstadoCuenta


class CuentahabienteViewSet(viewsets.ModelViewSet):
    queryset = Cuentahabiente.objects.select_related("colonia", "servicio").order_by("id_cuentahabiente")
    serializer_class = CuentahabienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["numero_contrato", "nombres", "ap", "am", "telefono", "colonia__nombre_colonia"]
    ordering_fields = ["id_cuentahabiente", "numero_contrato", "nombres"]
    ordering = ["id_cuentahabiente"]



class VistaPagosViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VistaPagos.objects.all()
    serializer_class = VistaPagosSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["anio", "estatus_deuda", "nombre_servicio", "numero_contrato"]
    search_fields = ["nombre_completo", "numero_contrato"]
    ordering_fields = ["anio", "pagos_totales", "numero_contrato"]

class VistaHistorialViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VistaHistorial.objects.all()
    serializer_class = VistaHistorialSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["anio", "mes", "numero_contrato", "fecha_pago"]
    search_fields = ["numero_contrato"]
    ordering_fields = ["fecha_pago", "anio", "numero_contrato"]

class VistaDeudoresViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VistaDeudores.objects.all().order_by("-monto_total")
    serializer_class = VistaDeudoresSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # Campos por los que vas a poder filtrar desde el front
    filterset_fields = ["estatus", "nombre_colonia"]
    search_fields = ["nombre_cuentahabiente", "nombre_colonia"]
    ordering_fields = ["monto_total", "nombre_cuentahabiente", "nombre_colonia"]
    ordering = ["-monto_total"]


class VistaProgresoPublicViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API pública:
    - NO requiere autenticación (AllowAny).
    - Solo lectura (GET).
    - Información agregada de avance de pagos.
    """
    queryset = VistaProgreso.objects.all()
    serializer_class = VistaProgresoSerializer
    permission_classes = [AllowAny]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # filtros por query param ?estatus=...&progreso=...&numero_contrato=...
    filterset_fields = ["estatus", "progreso", "numero_contrato"]

    # búsqueda por nombre o contrato: ?search=juan
    search_fields = ["nombre", "numero_contrato"]

    # ordenar: ?ordering=numero_contrato o ?ordering=-total
    ordering_fields = ["numero_contrato", "total", "saldo", "progreso"]
    ordering = ["numero_contrato"]

class EstadoCuentaViewSet(viewsets.ReadOnlyModelViewSet):
        
        """
          /api/estado-cuenta/
          /api/estado-cuenta/?numero_contrato=...
        """
        queryset = EstadoCuenta.objects.all()
        serializer_class = EstadoCuentaSerializer
        permission_classes = [IsAuthenticated&IsAdminSupervisorOrCobradorCreate]
        filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
        filterset_fields = ["id_cuentahabiente", "anio", "deuda"]
        search_fields = ["nombre", "direccion", "telefono", "numero_contrato"]
        ordering_fields = ["id_cuentahabiente", "numero_contrato", "fecha_pago", "anio"]
        ordering = ["numero_contrato", "fecha_pago"]


class RCuentahabientesViewSet(viewsets.ReadOnlyModelViewSet):  
    """/api/r-cuentahabientes/
    /api/r-cuentahabientes/?id_cuentahabiente=123
    """
     

    queryset = RCuentahabientes.objects.all().order_by("id_cuentahabiente")
    serializer_class = RCuentahabientesSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["id_cuentahabiente", "estatus", "numero_contrato", "nombre"]

    search_fields = ["nombre", "calle", "nombre_colonia", "telefono", "numero_contrato"]
    ordering_fields = ["id_cuentahabiente", "numero_contrato", "saldo_pendiente", "total_pagado"]
    ordering = ["id_cuentahabiente"]


class CierreAnualViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
        IsAdminSupervisorOrCobradorCreate
    ]

    def create(self, request):
        """
        POST /cierre-anual/
        Devuelve un resumen previo sin ejecutar el cierre.
        """
        serializer = CierreAnioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if CierreAnual.objects.filter(
            anio=data["anio_nuevo"],
            ejecutado=True
        ).exists():
            return Response(
                {"error": "El cierre anual ya fue ejecutado"},
                status=status.HTTP_409_CONFLICT
            )

        resumen = cambio_anio(data["anio_nuevo"])
        return Response(resumen, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="confirmar")
    def confirmar(self, request):
        """
        POST /cierre-anual/confirmar/
        Ejecuta el cierre anual definitivo.
        """
        serializer = EjecutarCierreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not data["confirmar"]:
            return Response(
                {"error": "Confirmación requerida para ejecutar el cierre anual"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.user.role not in ["admin", "supervisor"]:
            return Response(
                {"error": "Permisos insuficientes para ejecutar el cierre anual"},
                status=status.HTTP_403_FORBIDDEN
            )

        anio_cierre = data["anio_cierre"]  # ej: 2025
        anio_nuevo  = data["anio_nuevo"]   # ej: 2026

        with transaction.atomic():

            # ── Verificar y crear registro de cierre ─────────────────────
            cierre, created = CierreAnual.objects.select_for_update().get_or_create(
                anio=anio_nuevo,
                defaults={"ejecutado_por": request.user}
            )

            if cierre.ejecutado:
                return Response(
                    {"error": "El cierre anual ya fue ejecutado"},
                    status=status.HTTP_409_CONFLICT
                )

            # ── Tipo de cargo para cierre anual ──────────────────────────
            tipo_cierre, _ = TipoCargo.objects.get_or_create(
                nombre="CIERRE_ANUAL",
                defaults={"monto": Decimal("0.00"), "automatico": True}
            )

            # ── Bloquear y cargar cuentahabientes ────────────────────────
            ids = list(
                Cuentahabiente.objects.select_for_update()
                .values_list("id_cuentahabiente", flat=True)
            )
            cuentahabientes = list(
                Cuentahabiente.objects.filter(id_cuentahabiente__in=ids)
                .select_related("servicio")
            )

            # ── Pagos anticipados del nuevo año (más reciente primero) ───
            pagos_nuevo_anio = list(
                Pago.objects.filter(anio=anio_nuevo)
                .select_related("descuento")
                .order_by("cuentahabiente_id", "-fecha_pago")
            )

            # Sumar monto_recibido por cuentahabiente
            # (monto_recibido ya viene con el descuento aplicado)
            pagos_por_cuenta = {}
            for p in pagos_nuevo_anio:
                cid = p.cuentahabiente_id
                pagos_por_cuenta[cid] = (
                    pagos_por_cuenta.get(cid, Decimal("0")) +
                    decimal_seguro(p.monto_recibido)
                )

            # Descuento del pago más reciente con descuento activo
            descuento_por_cuenta = {}
            for p in pagos_nuevo_anio:
                cid = p.cuentahabiente_id
                if cid not in descuento_por_cuenta:
                    if p.descuento_id and p.descuento and p.descuento.activo:
                        descuento_por_cuenta[cid] = decimal_seguro(p.descuento.porcentaje)

            # ── Procesar cada cuentahabiente ─────────────────────────────
            cargos_a_crear       = []
            cuentas_a_actualizar = []
            fecha_cargo = date(anio_nuevo, 1, 1)

            for c in cuentahabientes:
                saldo_anterior = decimal_seguro(c.saldo_pendiente)
                tarifa_base    = obtener_tarifa_cuentahabiente(c)

                # Tarifa real = base - descuento fijo (si tiene)
                descuento_fijo = descuento_por_cuenta.get(c.id_cuentahabiente, Decimal("0"))
                tarifa_real    = tarifa_base - descuento_fijo

                # Cargo de cierre: deuda del año que cierra
                if saldo_anterior > Decimal("0"):
                    cargos_a_crear.append(
                        Cargo(
                            cuentahabiente=c,
                            tipo_cargo=tipo_cierre,
                            saldo_restante_cargo=saldo_anterior,
                            fecha_cargo=fecha_cargo,
                            activo=True
                        )
                    )

                # Nuevo saldo = tarifa real - pagos anticipados
                pagos_anticipados = pagos_por_cuenta.get(c.id_cuentahabiente, Decimal("0"))
                nuevo_saldo       = tarifa_real - pagos_anticipados

                # Estado de deuda
                if nuevo_saldo <= Decimal("0"):
                    estado_deuda = "pagado"
                elif pagos_anticipados > Decimal("0") and nuevo_saldo < tarifa_real:
                    estado_deuda = "corriente"
                else:
                    estado_deuda = "adeudo"

                c.saldo_pendiente = nuevo_saldo
                c.deuda           = estado_deuda
                cuentas_a_actualizar.append(c)

            # ── Guardar en lote ──────────────────────────────────────────
            if cargos_a_crear:
                Cargo.objects.bulk_create(cargos_a_crear, batch_size=500)

            Cuentahabiente.objects.bulk_update(
                cuentas_a_actualizar,
                ["saldo_pendiente", "deuda"],
                batch_size=500
            )

            # ── Marcar cierre como ejecutado ─────────────────────────────
            cierre.ejecutado     = True
            cierre.fecha         = date.today()
            cierre.ejecutado_por = request.user
            cierre.save()

            return Response(
                {
                    "status": "Cierre anual ejecutado correctamente",
                    "anio_cerrado": anio_cierre,
                    "anio_nuevo": anio_nuevo,
                    "cuentas_procesadas": len(cuentas_a_actualizar),
                    "cargos_generados": len(cargos_a_crear),
                    "cuentas_con_pagos_anticipados": len(pagos_por_cuenta),
                },
                status=status.HTTP_200_OK
            )


# ── Funciones auxiliares ─────────────────────────────────────────────────────

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
    """
    Devuelve un resumen previo del cierre sin ejecutar nada.
    """
    resumen = {
        "reiniciadas": 0,
        "con_adeudo": 0,
        "cargo_total": Decimal("0.00"),
        "cuentas_con_pagos_anticipados": 0,
    }

    pagos_anticipados_ids = set(
        Pago.objects.filter(anio=anio_nuevo)
        .values_list("cuentahabiente_id", flat=True)
        .distinct()
    )

    for c in Cuentahabiente.objects.select_related("servicio"):
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