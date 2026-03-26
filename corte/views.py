import json
from django.conf import settings
from django.db import connection, DatabaseError
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response      
from rest_framework.permissions import IsAuthenticated 
from rest_framework import status, permissions

from equipos.models import Equipo

# Asegúrate de importar tu modelo correctamente
#from cobrador.models import Cobrador 
from .serializers import (CorteSerializer
                          , CorteCajaJrSerializer
                          , SubirPdfCorteJrSerializer, CorteCajaSrSerializer,
                          SubirPdfCorteSrSerializer)
from .models import CorteCajaJr, CorteCajaSr
from equipos.models import Equipo
from cobrador.permissions import Roles



### pdf consultar 
import boto3
from botocore.config import Config

"""
class CorteView(APIView):
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        serializer = CorteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True) 
        fechas = serializer.validated_data

        try:
            # -----------------------------------------------------------
            # CORRECCIÓN AQUÍ:
            # -----------------------------------------------------------
            # 1. Obtenemos el nombre de usuario (string) del token (ej. "efrenmt")
            #    Usamos 'getattr' por seguridad, por si tu User usa otro campo.
            username_actual = getattr(request.user, 'username', None) or getattr(request.user, 'usuario', None)

            if not username_actual:
                # Si request.user es el Cobrador mismo (caso Custom Auth)
                if hasattr(request.user, 'id_cobrador'):
                    cobrador_id = request.user.id_cobrador
                else:
                    raise Cobrador.DoesNotExist 
            else:
                # 2. Buscamos en la tabla Cobrador comparando TEXTO con TEXTO
                perfil_cobrador = Cobrador.objects.get(usuario=username_actual)
                cobrador_id = perfil_cobrador.id_cobrador

            # -----------------------------------------------------------
            # FIN DE LA CORRECCIÓN
            # -----------------------------------------------------------

            # Ejecuta la función SQL
            resultado_json = self._ejecutar_funcion_corte_db(
                cobrador_id=cobrador_id,
                fecha_inicio=fechas['fecha_inicio'],  
                fecha_fin=fechas['fecha_fin']
            )

            return Response(resultado_json, status=status.HTTP_200_OK)
        
        except Cobrador.DoesNotExist:
            return Response(
                {"error": f"El usuario '{request.user}' no está registrado en la tabla de Cobradores."},
                status=status.HTTP_403_FORBIDDEN
            )
        except DatabaseError as e:
            print(f"Error DB: {str(e)}")
            return Response(
                {"error": "Error interno de base de datos al generar el corte."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _ejecutar_funcion_corte_db(self, cobrador_id, fecha_inicio, fecha_fin):
        #Se usa la funcion SQL almacenada y asegura el retorno del JSON 
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT corte_caja(%s, %s, %s);",
                [fecha_inicio, fecha_fin, cobrador_id]
            )
            raw_data = cursor.fetchone()[0]

        if isinstance(raw_data, str):
            return json.loads(raw_data)
        return raw_data or {}
        """
class CorteView(APIView):
    # Seguimos protegiendo la ruta: solo usuarios logueados pueden pedir el corte
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        serializer = CorteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True) 
        fechas = serializer.validated_data

        try:
            # -----------------------------------------------------------
            # CORTE GENERAL
            # -----------------------------------------------------------
            # Simplemente ejecutamos la función mandando "None" en el cobrador_id.
            # Tu función SQL está preparada para recibir NULL y sumar todos los pagos.
            
            resultado_json = self._ejecutar_funcion_corte_db(
                fecha_inicio=fechas['fecha_inicio'],  
                fecha_fin=fechas['fecha_fin'],
                cobrador_id=None  # <--- MAGIA: Esto hace que sea general
            )

            return Response(resultado_json, status=status.HTTP_200_OK)
        
        except DatabaseError as e:
            print(f"Error DB: {str(e)}")
            return Response(
                {"error": "Error interno de base de datos al generar el corte general."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _ejecutar_funcion_corte_db(self, fecha_inicio, fecha_fin, cobrador_id):
        """ Se usa la funcion SQL almacenada y asegura el retorno del JSON """
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT corte_caja(%s, %s, %s);",
                [fecha_inicio, fecha_fin, cobrador_id]
            )
            raw_data = cursor.fetchone()[0]

        if isinstance(raw_data, str):
            return json.loads(raw_data)
        return raw_data or {}
    




####-------Corte Jr -------####
class CorteCajaJrGenerarView(APIView):
    """
    POST /corte/jr/generar/
    Corre la función Postgres y devuelve el JSON al front.
    El front genera el PDF con esa información.
    """
    permission_classes = [permissions.IsAuthenticated, Roles("tesorero_jr")]

    def post(self, request):
        fecha_inicio = request.data.get("fecha_inicio")
        fecha_fin    = request.data.get("fecha_fin")
        cobrador_id  = request.data.get("cobrador_id", None)  # opcional

        if not fecha_inicio or not fecha_fin:
            return Response(
                {"detail": "fecha_inicio y fecha_fin son requeridos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT public.corte_caja_jr(%s, %s, %s, %s)",
                    [fecha_inicio, fecha_fin, request.user.id_cobrador, cobrador_id],
                )
                resultado = cursor.fetchone()[0]

            corte_info  = resultado["corte_info"]
            movimientos = resultado["movimientos"]
            folio_corte = corte_info["folio_corte"]

            corte = CorteCajaJr.objects.get(folio_corte=folio_corte)

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "corte":       CorteCajaJrSerializer(corte).data,
                "movimientos": movimientos,
            },
            status=status.HTTP_201_CREATED,
        )


class SubirPdfCorteJrView(APIView):
    """
    PATCH /corte/jr/<folio>/pdf/
    El front genera el PDF, lo imprime, lo firma y lo sube aquí.
    """
    permission_classes = [permissions.IsAuthenticated, Roles("tesorero_jr")]

    def patch(self, request, folio):
        try:
            corte = CorteCajaJr.objects.get(folio_corte=folio)
        except CorteCajaJr.DoesNotExist:
            return Response({"detail": "Corte no encontrado."}, status=404)

        if corte.cobrador != request.user:
            return Response(
                {"detail": "No puedes modificar un corte que no es tuyo."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if corte.validado:
            return Response(
                {"detail": "No puedes modificar un corte ya validado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ser = SubirPdfCorteJrSerializer(corte, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()

        return Response(CorteCajaJrSerializer(corte).data)


class ValidarCorteJrView(APIView):
    """
    PATCH /corte/jr/<folio>/validar/
    El Tesorero Jr valida su propio corte.
    Requiere tener el PDF subido primero.
    """
    permission_classes = [permissions.IsAuthenticated, Roles("tesorero_jr")]

    def patch(self, request, folio):
        try:
            corte = CorteCajaJr.objects.get(folio_corte=folio)
        except CorteCajaJr.DoesNotExist:
            return Response({"detail": "Corte no encontrado."}, status=404)

        if corte.cobrador != request.user:
            return Response(
                {"detail": "No puedes validar un corte que no es tuyo."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not corte.pdf:
            return Response(
                {"detail": "Debes subir el comprobante firmado antes de validar."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if corte.validado:
            return Response(
                {"detail": "Este corte ya fue validado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        corte.validado         = True
        corte.fecha_validacion = timezone.now()
        corte.validado_por     = request.user
        corte.save(update_fields=["validado", "fecha_validacion", "validado_por_id"])

        return Response(CorteCajaJrSerializer(corte).data)


class CorteCajaJrListView(APIView):
    """
    GET /corte/jr/
    Tesorero Jr: solo sus cortes.
    Tesorero Sr / Admin / Presidente: todos.
    """
    permission_classes = [
        permissions.IsAuthenticated,
        Roles("tesorero_jr", "tesorero_sr", "admin", "presidente"),
    ]

    def get(self, request):
        if request.user.role == "tesorero_jr":
            qs = CorteCajaJr.objects.filter(cobrador=request.user)
        else:
            qs = CorteCajaJr.objects.all()

        return Response(CorteCajaJrSerializer(qs, many=True).data)


class CorteCajaJrDetalleView(APIView):
    """
    GET /corte/jr/<folio>/
    """
    permission_classes = [
        permissions.IsAuthenticated,
        Roles("tesorero_jr", "tesorero_sr", "admin", "presidente"),
    ]

    def get(self, request, folio):
        try:
            corte = CorteCajaJr.objects.get(folio_corte=folio)
        except CorteCajaJr.DoesNotExist:
            return Response({"detail": "Corte no encontrado."}, status=404)

        if request.user.role == "tesorero_jr" and corte.cobrador != request.user:
            return Response(
                {"detail": "No tienes permiso para ver este corte."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(CorteCajaJrSerializer(corte).data)


#### Corte Senior (Tesorero Sr) ####
class CorteCajaSrGenerarView(APIView):
    """
    POST /corte/sr/generar/
    El Tesorero Sr busca el equipo por nombre y genera el corte.
    """
    permission_classes = [permissions.IsAuthenticated, Roles("tesorero_sr")]

    def post(self, request):
        fecha_inicio  = request.data.get("fecha_inicio")
        fecha_fin     = request.data.get("fecha_fin")
        nombre_equipo = request.data.get("nombre_equipo")

        if not fecha_inicio or not fecha_fin or not nombre_equipo:
            return Response(
                {"detail": "fecha_inicio, fecha_fin y nombre_equipo son requeridos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Buscar equipo por nombre ──────────────────────────────────────────
        try:
            equipo = Equipo.objects.get(
                nombre_equipo__iexact=nombre_equipo,
                activo=True,
            )
        except Equipo.DoesNotExist:
            return Response(
                {"detail": f"No se encontró el equipo '{nombre_equipo}'."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT public.corte_caja_sr(%s, %s, %s, %s)",
                    [fecha_inicio, fecha_fin, request.user.id_cobrador, equipo.id_equipo],
                )
                resultado = cursor.fetchone()[0]

            corte_info  = resultado["corte_info"]
            movimientos = resultado["movimientos"]
            folio_corte = corte_info["folio_corte"]

            corte = CorteCajaSr.objects.get(folio_corte=folio_corte)

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "corte":       CorteCajaSrSerializer(corte).data,
                "movimientos": movimientos,
            },
            status=status.HTTP_201_CREATED,
        )


class SubirPdfCorteSrView(APIView):
    """
    PATCH /corte/sr/<folio>/pdf/
    El front genera el PDF, lo imprime, lo firma y lo sube aquí.
    """
    permission_classes = [permissions.IsAuthenticated, Roles("tesorero_sr")]

    def patch(self, request, folio):
        try:
            corte = CorteCajaSr.objects.get(folio_corte=folio)
        except CorteCajaSr.DoesNotExist:
            return Response({"detail": "Corte no encontrado."}, status=404)

        if corte.tesorero_sr != request.user:
            return Response(
                {"detail": "No puedes modificar un corte que no es tuyo."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if corte.validado:
            return Response(
                {"detail": "No puedes modificar un corte ya validado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ser = SubirPdfCorteSrSerializer(corte, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()

        return Response(CorteCajaSrSerializer(corte).data)


class ValidarCorteSrView(APIView):
    """
    PATCH /corte/sr/<folio>/validar/
    El Tesorero Sr valida su propio corte.
    Requiere tener el PDF subido primero.
    Solo al validar se registra el ingreso en transacciones.
    """
    permission_classes = [permissions.IsAuthenticated, Roles("tesorero_sr")]

    def patch(self, request, folio):
        try:
            corte = CorteCajaSr.objects.get(folio_corte=folio)
        except CorteCajaSr.DoesNotExist:
            return Response({"detail": "Corte no encontrado."}, status=404)

        if corte.tesorero_sr != request.user:
            return Response(
                {"detail": "No puedes validar un corte que no es tuyo."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not corte.pdf:
            return Response(
                {"detail": "Debes subir el comprobante firmado antes de validar."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if corte.validado:
            return Response(
                {"detail": "Este corte ya fue validado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        corte.validado         = True
        corte.fecha_validacion = timezone.now()
        corte.validado_por     = request.user
        corte.save(update_fields=["validado", "fecha_validacion", "validado_por_id"])

        # ── Insertar en transacciones solo al validar ─────────────────────────
        from tesoreria.models import Transaccion, Cuenta
        try:
            cuenta = Cuenta.objects.get(id=1)
        except Cuenta.DoesNotExist:
            return Response(
                {"detail": "No existe una cuenta configurada."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        comprobante_url = ''
        if corte.pdf:
            try:
                comprobante_url = generar_url_firmada(corte.pdf.name)
            except Exception:
                comprobante_url = ''

        Transaccion.objects.create(
            cuenta        = cuenta,
            tipo          = 'ingreso',
            monto         = corte.gran_total,
            fecha         = corte.fecha_generacion,
            observaciones = f'Corte Sr #{folio}',
            comprobante   = corte.pdf.name if corte.pdf else '',
            requisitor    = None,
        )

        return Response(CorteCajaSrSerializer(corte).data)


class CorteCajaSrListView(APIView):
    """
    GET /corte/sr/
    Tesorero Sr: solo sus cortes.
    Admin / Presidente: todos.
    """
    permission_classes = [
        permissions.IsAuthenticated,
        Roles("tesorero_sr", "admin", "presidente"),
    ]

    def get(self, request):
        if request.user.role == "tesorero_sr":
            qs = CorteCajaSr.objects.filter(tesorero_sr=request.user)
        else:
            qs = CorteCajaSr.objects.all()

        return Response(CorteCajaSrSerializer(qs, many=True).data)


class CorteCajaSrDetalleView(APIView):
    """
    GET /corte/sr/<folio>/
    """
    permission_classes = [
        permissions.IsAuthenticated,
        Roles("tesorero_sr", "admin", "presidente"),
    ]

    def get(self, request, folio):
        try:
            corte = CorteCajaSr.objects.get(folio_corte=folio)
        except CorteCajaSr.DoesNotExist:
            return Response({"detail": "Corte no encontrado."}, status=404)

        if request.user.role == "tesorero_sr" and corte.tesorero_sr != request.user:
            return Response(
                {"detail": "No tienes permiso para ver este corte."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(CorteCajaSrSerializer(corte).data)
    




#### cosultar pdf 
def generar_url_firmada(ruta_pdf: str, expiracion: int = 3600) -> str:
    """
    Genera una URL temporal para ver el PDF.
    expiracion: segundos que dura la URL (default 1 hora)
    """
    s3_client = boto3.client(
        "s3",
        endpoint_url       = "https://nyc3.digitaloceanspaces.com",
        aws_access_key_id  = settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
        config             = Config(signature_version="s3v4"),
    )

    url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
            "Key":    ruta_pdf,
        },
        ExpiresIn=expiracion,
    )
    return url


class CorteCajaJrPdfView(APIView):
    """
    GET /corte/jr/<folio>/ver-pdf/
    Devuelve una URL temporal para ver el PDF.
    """
    permission_classes = [
        permissions.IsAuthenticated,
        Roles("tesorero_jr", "tesorero_sr", "admin", "presidente"),
    ]

    def get(self, request, folio):
        try:
            corte = CorteCajaJr.objects.get(folio_corte=folio)
        except CorteCajaJr.DoesNotExist:
            return Response({"detail": "Corte no encontrado."}, status=404)

        if not corte.pdf:
            return Response(
                {"detail": "Este corte no tiene PDF subido."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Tesorero Jr solo puede ver sus propios cortes
        if request.user.role == "tesorero_jr" and corte.cobrador != request.user:
            return Response(
                {"detail": "No tienes permiso para ver este PDF."},
                status=status.HTTP_403_FORBIDDEN,
            )

        url = generar_url_firmada(corte.pdf.name)

        return Response({
            "folio_corte": folio,
            "pdf_url":     url,
            "expira_en":   "1 hora",
        })

class CorteCajaSrPdfView(APIView):
    """
    GET /corte/sr/<folio>/ver-pdf/
    Tesorero Sr: solo sus propios cortes.
    Admin / Presidente: cualquier corte.
    """
    permission_classes = [
        permissions.IsAuthenticated,
        Roles("tesorero_sr", "admin", "presidente"),
    ]

    def get(self, request, folio):
        try:
            corte = CorteCajaSr.objects.get(folio_corte=folio)
        except CorteCajaSr.DoesNotExist:
            return Response({"detail": "Corte no encontrado."}, status=404)

        if not corte.pdf:
            return Response(
                {"detail": "Este corte no tiene PDF subido."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.role == "tesorero_sr" and corte.tesorero_sr != request.user:
            return Response(
                {"detail": "No tienes permiso para ver este PDF."},
                status=status.HTTP_403_FORBIDDEN,
            )

        url = generar_url_firmada(corte.pdf.name)

        return Response({
            "folio_corte": folio,
            "pdf_url":     url,
            "expira_en":   "1 hora",
        })