from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import Colonia
from .serializers import ColoniaSerializer  
from .permissions import IsAdminOrSupervisorOrReadOnly

class ColoniaViewSet(viewsets.ModelViewSet):
    queryset = Colonia.objects.all().order_by('id_colonia')
    serializer_class = ColoniaSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSupervisorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre_colonia']
    ordering_fields = ['id_colonia', 'nombre_colonia', 'codigo_postal']
    ordering = ['id_colonia']

# Create your views here.
