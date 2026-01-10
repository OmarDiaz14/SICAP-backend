# cuentahabientes/views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Cuentahabiente
from .serializers import CuentahabienteSerializer, RCuentahabientesSerializer, VistaPagosSerializer, VistaHistorialSerializer,VistaDeudoresSerializer, VistaProgresoSerializer, EstadoCuentaSerializer
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
