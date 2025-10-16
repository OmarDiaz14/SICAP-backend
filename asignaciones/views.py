from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import SAFE_METHODS, BasePermission
from django.db import transaction, IntegrityError
from .models import Asignacion
from .serializers import AsignacionSerializer

class IsAdminOrSupervisorWrite(BasePermission):
    """GET/HEAD/OPTIONS: cualquier autenticado. POST/PUT/PATCH/DELETE: admin/supervisor."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return getattr(request.user, "is_authenticated", False)
        return getattr(request.user, "role", None) in {"admin", "supervisor"}

class AsignacionViewSet(viewsets.ModelViewSet):
    queryset = Asignacion.objects.select_related("cobrador", "sector").order_by("-fecha_asignacion", "-id_asignacion")
    serializer_class = AsignacionSerializer
    permission_classes = [IsAdminOrSupervisorWrite]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                obj = ser.save()
        except IntegrityError as e:
            return Response({"detail": f"Violación de integridad: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(obj).data, status=status.HTTP_201_CREATED)
