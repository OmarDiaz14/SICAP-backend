from rest_framework import viewsets, filters
from  rest_framework.permissions import IsAuthenticated
from .models import Sector
from .serializers import SectorSerializer
from cobrador.permissions import IsAdminOrSupervisorOrReadOnly


class SectorViewSet(viewsets.ModelViewSet):
    queryset = Sector.objects.all().order_by('id_sector')
    serializer_class = SectorSerializer
    permission_classes = [IsAuthenticated & IsAdminOrSupervisorOrReadOnly]


    #busquedas y ordenamientos 
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre_sector', 'descripcion']
    ordering_fields = ['id_sector', 'nombre_sector']
    ordering = ['id_sector']  # Ordenamiento por defecto
# Create your views here.
