from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework import exceptions
from .jwt_utils import decode_token
from .models import Cobrador
import jwt

class JWTAuthentication(BaseAuthentication):
    keyword = b"Bearer"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower():
            return None

        if len(auth) == 1:
            raise exceptions.AuthenticationFailed("Token faltante.")
        if len(auth) > 2:
            raise exceptions.AuthenticationFailed("Cabecera Authorization malformada.")

        token = auth[1].decode("utf-8").strip().strip('"').strip("'")  # limpia comillas/espacios

        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token expirado.")
        except jwt.InvalidSignatureError:
            raise exceptions.AuthenticationFailed("Firma inválida del token (SECRET_KEY distinta).")
        except jwt.DecodeError:
            raise exceptions.AuthenticationFailed("Token malformado.")
        except Exception:
            raise exceptions.AuthenticationFailed("Token inválido o expirado.")

        sub = payload.get("sub")
        if not sub:
            raise exceptions.AuthenticationFailed("Token sin 'sub'.")

        try:
            user = Cobrador.objects.get(pk=int(sub))  # 🔸 convertir a int al buscar
        except (ValueError, Cobrador.DoesNotExist):
            raise exceptions.AuthenticationFailed("Cobrador no encontrado.")

        if hasattr(user, "is_active") and not user.is_active:
            raise exceptions.AuthenticationFailed("Cuenta desactivada.")

        return (user, None)
