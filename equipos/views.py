from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Equipo, EquipoCobrador
from .serializers import EquipoSerializer
from .permissions import IsDirectivoOrReadOnly

# Create your views here.
class EquipoViewSet(viewsets.ModelViewSet):
    serializer_class = EquipoSerializer
    permission_classes = [IsAuthenticated, IsDirectivoOrReadOnly]

    def get_queryset(self):
        queryset = Equipo.objects.prefetch_related('miembros__cobrador').all()
        activo = self.request.query_params.get('activo')
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')
        return queryset

    def perform_destroy(self, instance):
        # Se desactiva y se registra fecha_termino
        from django.utils import timezone
        instance.activo = False
        instance.fecha_termino = timezone.now().date()
        instance.save()

    @action(detail=True, methods=['delete'], url_path='remover-cobrador/(?P<cobrador_id>[^/.]+)')
    def remover_cobrador(self, request, pk=None, cobrador_id=None):
        """Elimina un cobrador específico de un equipo."""
        equipo = self.get_object()
        try:
            equipo_asignado = EquipoCobrador.objects.get(equipo=equipo, cobrador_id=cobrador_id)
            equipo_asignado.delete()
            return Response({'detail': 'Cobrador removido del equipo.'}, status=status.HTTP_200_OK)
        except EquipoCobrador.DoesNotExist:
            return Response({'detail': 'El cobrador no pertenece a este equipo.'}, status=status.HTTP_404_NOT_FOUND)