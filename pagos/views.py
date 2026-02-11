# pagos/views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from cargos.models import Cargo
from .models import Pago
from .serializers import PagoCreateSerializer, PagoReadSerializer
from cobrador.permissions import IsAdminOnlyWriteExceptPost  # <— usa este permiso

class PagoViewSet(viewsets.ModelViewSet):
    """
    - GET: cualquiera autenticado.
    - POST: admin / supervisor / cobrador.
    - PUT/PATCH/DELETE: solo admin.
    - En POST, el cobrador se toma de request.user.
    """
    queryset = (
        Pago.objects
        .select_related("descuento", "cobrador", "cuentahabiente")
        .order_by("-fecha_pago", "-id_pago")
    )
    permission_classes = [IsAuthenticated & IsAdminOnlyWriteExceptPost]

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return PagoReadSerializer
        return PagoCreateSerializer

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        
        # bloquear pago de tarifa con cargos pendientes
        cuentahabiente = ser.validated_data["cuentahabiente"]

        if Cargo.objects.filter(
            cuentahabiente=cuentahabiente,
            activo=True 
        ).exists():
            return Response(
                {
                    "error": "Debe liquidar todos los cargos antes de pagar la tarifa"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            pago = ser.save()

        read = PagoReadSerializer(pago)
        return Response(read.data, status=status.HTTP_201_CREATED)
