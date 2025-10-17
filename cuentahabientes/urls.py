from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CuentahabienteViewSet, VistaHistorialViewSet, VistaPagosViewSet


router = DefaultRouter()

router.register(r'cuentahabientes', CuentahabienteViewSet, basename='cuentahabiente')
router.register(r'vista-pagos', VistaPagosViewSet, basename='vista-pagos')
router.register(r'vista-historial', VistaHistorialViewSet, basename='vista-historial')

urlpatterns = [ 
    path('', include(router.urls)) ,
     path('api/', include(router.urls)),
    ]