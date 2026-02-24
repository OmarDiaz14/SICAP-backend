import json
from django.db import connection, DatabaseError
from rest_framework.views import APIView
from rest_framework.response import Response      
from rest_framework.permissions import IsAuthenticated 
from rest_framework import status
from django.shortcuts import get_object_or_404

# Asegúrate de importar tu modelo correctamente
#from cobrador.models import Cobrador 
from .serializers import CorteSerializer


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