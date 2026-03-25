from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CuentaViewSet, TransaccionViewSet

router = DefaultRouter()
router.register(r'cuentas', CuentaViewSet)
router.register(r'transacciones', TransaccionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]