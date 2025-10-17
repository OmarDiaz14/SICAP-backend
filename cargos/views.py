from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import Cargo
from .serializers import CargoSerializer
from cobrador.permissions import IsAdminOrSupervisorOrReadOnly

class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.select_related("cuentahabiente").order_by("-fecha_cargo","-id_cargo")
    serializer_class = CargoSerializer
    permission_classes = [IsAuthenticated & IsAdminOrSupervisorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "cuentahabiente__numero_contrato",
        "cuentahabiente__nombres", "cuentahabiente__ap", "cuentahabiente__am",
        "tipo_cargo"
    ]
    ordering_fields = ["fecha_cargo", "monto_cargo", "id_cargo"]
    ordering = ["-fecha_cargo", "-id_cargo"]

# Create your views here.
