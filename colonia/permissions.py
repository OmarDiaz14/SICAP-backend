from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrSupervisorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        if request.method in SAFE_METHODS:
            return True                   # GET/HEAD/OPTIONS: cualquier autenticado
        return getattr(user, "role", None) in ("admin", "supervisor")