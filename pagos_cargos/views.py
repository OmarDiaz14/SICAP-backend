from decimal import Decimal
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import Sum
from cargos.models import Cargo
from pagos_cargos.models import PagoCargos
from pagos_cargos.serializers import PagarCargoSerializer

class PagarCargoView(APIView):

    def post(self, request):
        """
        POST /pagar-cargo/
        """
        serializer = PagarCargoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cobrador = request.user
        data = serializer.validated_data

        monto = data["monto"]
        cuentahabiente_id = data["cuentahabiente_id"]
        comentarios = data.get("comentarios", "")

        cargos = Cargo.objects.filter(
            cuentahabiente_id=cuentahabiente_id,
            activo=True
        ).order_by("fecha_cargo")

        if not cargos.exists():
            return Response(
                {"error": "No hay cargos pendientes"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        total_deuda = cargos.aggregate(
            total=Sum("saldo_restante_cargo")
        )["total"] or Decimal("0")

        if monto > total_deuda:
            return Response(
                {
                    "error": "El monto excede la deuda total",
                    "deuda_total": str(total_deuda)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():

            monto_restante = monto
            aplicaciones = []

            for cargo in cargos:
                if monto_restante <= 0:
                    break

                if monto_restante >= cargo.saldo_restante_cargo:
                    monto_aplicado = cargo.saldo_restante_cargo
                    cargo.saldo_restante_cargo = Decimal("0")
                    cargo.activo = False
                    pago_completo = True
                else:
                    monto_aplicado = monto_restante
                    cargo.saldo_restante_cargo -= monto_aplicado
                    pago_completo = False

                monto_restante -= monto_aplicado
                cargo.save()

                pago = PagoCargos.objects.create(
                    cuentahabiente_id=cuentahabiente_id,
                    cargo=cargo,
                    cobrador=cobrador,
                    monto_recibido=monto_aplicado,
                    comentarios=comentarios
                )

                aplicaciones.append({
                    "pago_id": pago.id_pago,
                    "cargo_id": cargo.id_cargo,
                    "monto_aplicado": str(monto_aplicado),
                    "pago_completo": pago_completo
                })

            saldo_restante = Cargo.objects.filter(
                cuentahabiente_id=cuentahabiente_id,
                activo=True
            ).aggregate(
                total=Sum("saldo_restante_cargo")
            )["total"] or Decimal("0")

        return Response({
            "status": "Pago aplicado correctamente",
            "monto_entregado": str(monto),
            "aplicaciones": aplicaciones,
            "saldo_restante_cargo": str(saldo_restante)
        }, status=status.HTTP_200_OK)
