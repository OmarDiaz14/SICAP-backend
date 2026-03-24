from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db import transaction
from .models import Cuenta, Transaccion
from .serializers import CuentaSerializer, TransaccionSerializer


class CuentaViewSet(viewsets.ModelViewSet):
    queryset = Cuenta.objects.all()
    serializer_class = CuentaSerializer


class TransaccionViewSet(viewsets.ModelViewSet):
    queryset = Transaccion.objects.all()
    serializer_class = TransaccionSerializer

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