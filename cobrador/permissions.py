from rest_framework.permissions import BasePermission, SAFE_METHODS

# ─── Roles del sistema ────────────────────────────────────────────────────────
ROLE_ADMIN        = "admin"
ROLE_PRESIDENTE   = "presidente"
ROLE_COBRADOR     = "cobrador"
ROLE_SECRETARIO   = "secretario"
ROLE_TESORERO_JR  = "tesorero_jr"
ROLE_TESORERO_SR  = "tesorero_sr"

# Grupos reutilizables
ROLES_DIRECTIVOS  = {ROLE_ADMIN, ROLE_PRESIDENTE}                                     # admin + presidente
ROLES_TESORERIA   = {ROLE_ADMIN, ROLE_PRESIDENTE, ROLE_TESORERO_SR, ROLE_TESORERO_JR} # acceso financiero
ROLES_OPERATIVOS  = {ROLE_ADMIN, ROLE_PRESIDENTE, ROLE_COBRADOR}                      # operaciones de cobro
ROLES_TODOS       = {ROLE_ADMIN, ROLE_PRESIDENTE, ROLE_COBRADOR,ROLE_SECRETARIO, ROLE_TESORERO_JR, ROLE_TESORERO_SR}  

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

# ─── Permisos compuestos ───────────────────────────────────────────────────────
class IsDirectivoOrReadOnly(BasePermission):
    """
    Antes: IsAdminOrSupervisorOrReadOnly
    - Lectura  (GET/HEAD/OPTIONS): cualquier autenticado.
    - Escritura (POST/PUT/PATCH/DELETE): solo admin o presidente.
    """
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        is_auth = bool(u and getattr(u, "is_authenticated", False))
        if request.method in SAFE_METHODS:
            return is_auth
        if not is_auth:
            return False
        return getattr(u, "role", None) in ROLES_DIRECTIVOS


class IsDirectivoOrCobradorCreate(BasePermission):
    """
    Antes: IsAdminSupervisorOrCobradorCreate
    - GET/HEAD/OPTIONS : cualquier autenticado.
    - POST             : admin, presidente o cobrador.
    - PUT/PATCH/DELETE : solo admin o presidente.
    """
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        is_auth = bool(u and getattr(u, "is_authenticated", False))
        if request.method in SAFE_METHODS:
            return is_auth
        if not is_auth:
            return False
        if request.method == "POST":
            return getattr(u, "role", None) in ROLES_OPERATIVOS
        return getattr(u, "role", None) in ROLES_DIRECTIVOS


class IsAdminOnlyWriteExceptPost(BasePermission):
    """
    - GET/HEAD/OPTIONS : cualquier autenticado.
    - POST             : admin, presidente o cobrador.
    - PUT/PATCH/DELETE : solo admin.
    """
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        is_auth = bool(u and getattr(u, "is_authenticated", False))
        if request.method in SAFE_METHODS:
            return is_auth
        if not is_auth:
            return False
        if request.method == "POST":
            return getattr(u, "role", None) in ROLES_OPERATIVOS
        return getattr(u, "role", None) == ROLE_ADMIN