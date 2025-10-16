from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import Servicio
from .serializers import ServicioSerializer 
from cobrador.permissions import IsAdminOrSupervisorOrReadOnly


class ServicioViewSet(viewsets.ModelViewSet):
    queryset = Servicio.objects.all().order_by('id_tipo_servicio')
    serializer_class = ServicioSerializer
    permission_classes = [IsAdminOrSupervisorOrReadOnly & IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['id_tipo_servicio', 'nombre', 'costo']
    ordering = ['id_tipo_servicio']

# Create your views here.
