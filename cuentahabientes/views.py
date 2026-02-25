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
        POST /api/cierre-anual/ 
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
        
        resumen = cambio_anio()
        return Response(resumen, status=status.HTTP_200_OK)



@action(detail=False, methods=["post"], url_path="confirmar")
def confirmar(self, request):
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

    with transaction.atomic():
        cierre, created = CierreAnual.objects.select_for_update().get_or_create(
            anio=data["anio_nuevo"],
            defaults={"ejecutado_por": request.user}
        )

        if cierre.ejecutado:
            return Response(
                {"error": "El cierre anual ya fue ejecutado"},
                status=status.HTTP_409_CONFLICT
            )

        tipo_cierre, _ = TipoCargo.objects.get_or_create(
            nombre="CIERRE_ANUAL",
            defaults={"monto": Decimal("0.00"), "automatico": True}
        )

        # ✅ Una sola query con select_related
        cuentahabientes = list(
            Cuentahabiente.objects.select_for_update()
            .select_related("servicio")
        )

        cargos_a_crear = []
        cuentas_a_actualizar = []
        fecha_cargo = date(data["anio_nuevo"], 1, 1)

        for c in cuentahabientes:
            saldo_anterior = decimal_seguro(c.saldo_pendiente)
            tarifa = obtener_tarifa_cuentahabiente(c)

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

            c.saldo_pendiente = tarifa
            c.deuda = "adeudo" if tarifa > Decimal("0") else "pagado"
            cuentas_a_actualizar.append(c)

        # ✅ Inserts y updates en lote, no uno por uno
        if cargos_a_crear:
            Cargo.objects.bulk_create(cargos_a_crear, batch_size=500)

        Cuentahabiente.objects.bulk_update(
            cuentas_a_actualizar,
            ["saldo_pendiente", "deuda"],
            batch_size=500
        )

        cierre.ejecutado = True
        cierre.fecha = date.today()
        cierre.ejecutado_por = request.user
        cierre.save()

        return Response(
            {"status": "Cierre anual ejecutado correctamente"},
            status=status.HTTP_200_OK
        )
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

def cambio_anio():

    resumen = {
        "reiniciadas": 0,
        "con_adeudo": 0,
        "cargo_total": Decimal("0.00")
    }

    for c in Cuentahabiente.objects.select_related("servicio"):
        tarifa = obtener_tarifa_cuentahabiente(c)
        saldo_actual = decimal_seguro(c.saldo_pendiente)

        if saldo_actual == 0:
            resumen["reiniciadas"] += 1
        else:
            resumen["con_adeudo"] += 1

        resumen["cargo_total"] += tarifa

    return resumen