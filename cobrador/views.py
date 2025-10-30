from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, filters, generics
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    LoginSerializer, SignupSerializer, AdminCreateUserSerializer, CobradorPublicSerializer
)
from .models import Cobrador
from .jwt_utils import create_access_token
from .permissions import Roles

class SignupView(APIView):
    """Autoregistro: siempre crea con rol 'cobrador'."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = SignupSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        token = create_access_token({
            "sub": user.id_cobrador, "usuario": user.usuario, "role": user.role
        })
        return Response({"access": token, "cobrador": CobradorPublicSerializer(user).data},
                        status=status.HTTP_201_CREATED)

class AdminCreateUserView(APIView):
    """Crear usuarios con cualquier rol (solo ADMIN)."""
    permission_classes = [Roles("admin")]

    def post(self, request):
        ser = AdminCreateUserSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response({"cobrador": CobradorPublicSerializer(user).data}, status=201)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        usuario = ser.validated_data["usuario"]
        password = ser.validated_data["password"]

        c = Cobrador.objects.filter(usuario__iexact=usuario, is_active=True).first()
        if not c or not c.check_password(password):
            return Response({"detail": "Credenciales inválidas."}, status=400)

        token = create_access_token({"sub": c.id_cobrador, "usuario": c.usuario, "role": c.role})
        return Response({"access": token, "cobrador": CobradorPublicSerializer(c).data})

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        return Response(CobradorPublicSerializer(request.user).data)
    

class CobradorListView(generics.ListAPIView):
    """
    GET /auth/cobradores/?search=...&role=...
    - Solo admin o supervisor.
    - Por defecto muestra usuarios con role='cobrador'.
    """
    serializer_class = CobradorPublicSerializer
    permission_classes = [IsAuthenticated & Roles("admin", "supervisor")]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre", "apellidos", "usuario", "email"]
    ordering_fields = ["nombre", "apellidos", "usuario", "id_cobrador"]
    ordering = ["nombre", "apellidos"]

    def get_queryset(self):
        role = self.request.query_params.get("role", "cobrador")
        qs = Cobrador.objects.filter(is_active=True)
        if role:
            qs = qs.filter(role=role)
        # Solo campos públicos
        return qs.only("id_cobrador", "nombre", "apellidos", "usuario", "email", "role")


# ---- Ejemplos de vistas protegidas por rol ----
""""class AdminDashboardView(APIView):
    permission_classes = [Roles("admin")]
    def get(self, request): return Response({"ok": True, "msg": "solo admin"})

class SupervisorAreaView(APIView):
    permission_classes = [Roles("admin","supervisor")]
    def get(self, request): return Response({"ok": True, "msg": "admin o supervisor"})

class CobranzaView(APIView):
    permission_classes = [Roles("admin","supervisor","cobrador")]
    def get(self, request): return Response({"ok": True, "msg": "cualquier rol autenticado"})"""
