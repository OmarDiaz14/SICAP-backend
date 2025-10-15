from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import Descuento
from .serializers import DescuentoSerializer
from cobrador.permissions import IsAdminOrSupervisorOrReadOnly


class DescuentoViewSet(viewsets.ModelViewSet):
    queryset = Descuento.objects.all().order_by('id_descuento')
    serializer_class = DescuentoSerializer

    #lectura: requiere login; escritura: solo admin o supervisor
    permission_classes = [IsAuthenticated & IsAdminOrSupervisorOrReadOnly]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre_descuento']
    ordering_fields = ['id_descuento', 'nombre_descuento', 'porcentaje', 'activo']
    ordering = ['id_descuento']

    