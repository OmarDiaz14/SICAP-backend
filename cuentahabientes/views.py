# cuentahabientes/views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import Cuentahabiente
from .serializers import CuentahabienteSerializer, VistaPagosSerializer, VistaHistorialSerializer, VistaDeudoresSerializer
from cobrador.permissions import IsAdminSupervisorOrCobradorCreate
from .models_views import VistaHistorial,VistaPagos, VistaDeudores


class CuentahabienteViewSet(viewsets.ModelViewSet):
    queryset = Cuentahabiente.objects.select_related("colonia", "servicio").order_by("id_cuentahabiente")
    serializer_class = CuentahabienteSerializer
    permission_classes = [IsAuthenticated & IsAdminSupervisorOrCobradorCreate]
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