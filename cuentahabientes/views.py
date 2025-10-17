# cuentahabientes/views.py
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import Cuentahabiente
from .serializers import CuentahabienteSerializer
from cobrador.permissions import IsAdminSupervisorOrCobradorCreate

class CuentahabienteViewSet(viewsets.ModelViewSet):
    queryset = Cuentahabiente.objects.select_related("colonia", "servicio").order_by("id_cuentahabiente")
    serializer_class = CuentahabienteSerializer
    permission_classes = [IsAuthenticated & IsAdminSupervisorOrCobradorCreate]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["numero_contrato", "nombres", "ap", "am", "telefono", "colonia__nombre_colonia"]
    ordering_fields = ["id_cuentahabiente", "numero_contrato", "nombres"]
    ordering = ["id_cuentahabiente"]
