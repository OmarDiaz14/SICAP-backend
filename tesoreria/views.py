from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework.decorators import action
from .models import Cuenta, Transaccion
from .serializers import CuentaSerializer, TransaccionSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


class CuentaViewSet(viewsets.ModelViewSet):
    queryset = Cuenta.objects.all()
    serializer_class = CuentaSerializer


class TransaccionViewSet(viewsets.ModelViewSet):
    queryset = Transaccion.objects.all()
    serializer_class = TransaccionSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def handle_exception(self, exc):
        if isinstance(exc, DjangoValidationError):
            raise DRFValidationError(
                exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            )
        return super().handle_exception(exc)

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            cuenta = serializer.validated_data['cuenta']
            tipo = serializer.validated_data['tipo']
            monto = serializer.validated_data['monto']

            if tipo == 'egreso':
                cuenta.refresh_from_db()
                if cuenta.saldo < monto:
                    return Response(
                        {"error": "Saldo insuficiente"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            transaccion = serializer.save()

            return Response(
                TransaccionSerializer(transaccion).data,
                status=status.HTTP_201_CREATED
            )
        
    """@action(
        detail=True,
        methods=['patch'],
        url_path='comprobante',
        parser_classes=[MultiPartParser, FormParser],
    )
    def subir_comprobante(self, request, pk=None):
        
        PATCH /tesoreria/transacciones/{id}/comprobante/
        Sube el comprobante de un egreso por separado.
        
        try:
            transaccion = Transaccion.objects.get(pk=pk)
        except Transaccion.DoesNotExist:
            return Response({"detail": "Transacción no encontrada."}, status=404)

        ser = SubirComprobanteSerializer(transaccion, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()

        return Response(TransaccionSerializer(transaccion).data)"""