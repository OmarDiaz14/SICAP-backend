from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Calle
from .serializers import CalleSerializer
from .permissions import IsDirectivoOrReadOnly
# Create your views here.
class CalleViewSet(viewsets.ModelViewSet):
    serializer_class = CalleSerializer
    permission_classes = [IsAuthenticated, IsDirectivoOrReadOnly]