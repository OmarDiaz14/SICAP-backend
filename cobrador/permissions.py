from rest_framework.permissions import BasePermission, SAFE_METHODS
class HasAnyRole(BasePermission):
    """Permiso genérico: deja pasar si el usuario tiene alguno de los roles requeridos."""
    roles = ()

    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        if not u or not getattr(u, "is_authenticated", False):
            return False
        return not self.roles or u.role in self.roles

def Roles(*roles: str):
    """Factory para declarar permisos por roles en una línea.
    Ejemplo: permission_classes = [Roles('admin', 'supervisor')]
    """
    class _P(HasAnyRole):
        pass
    _P.roles = tuple(roles)  # <- asignamos fuera del body de la clase
    _P.__name__ = f"Roles_{'_'.join(roles) or 'Any'}"
    return _P


class IsAdminOrSupervisorOrReadOnly(BasePermission):
    """
    - Lectura (GET/HEAD/OPTIONS): requiere estar autenticado.
    - Escritura (POST/PUT/PATCH/DELETE): solo 'admin' o 'supervisor'.
    """
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        is_auth = bool(u and getattr(u, "is_authenticated", False))
        if request.method in SAFE_METHODS:
            return is_auth
        if not is_auth:
            return False
        return getattr(u, "role", None) in {"admin", "supervisor"}