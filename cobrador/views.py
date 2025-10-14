from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,permissions
from .serializers import LoginSerializer, SignupSerializer,CobradorPublicSerializer
from .models import Cobrador
from .jwt_utils import create_access_token

class SignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = SignupSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        cobrador = ser.save()

        token = create_access_token({
            "sub": cobrador.id_cobrador,
            "usuario": cobrador.usuario,
            "role": "cobrador",
        })

        return Response({
            "access": token,
            "cobrador": CobradorPublicSerializer(cobrador).data
        }, status=status.HTTP_201_CREATED)
    
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)  # <- corregido

        usuario = ser.validated_data["usuario"]
        password = ser.validated_data["password"]

        c = Cobrador.objects.filter(usuario__iexact=usuario).first()  # <- doble "_"

        if not c or not c.check_password(password):
            return Response({"detail": "Credenciales inválidas."}, status=400)

        token = create_access_token({"sub": c.id_cobrador, "usuario": c.usuario, "role": "cobrador"})
        return Response({"access": token, "cobrador": CobradorPublicSerializer(c).data})
        

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(CobradorPublicSerializer(request.user).data)
    


# Create your views here.
