from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CuentahabienteViewSet, VistaHistorialViewSet, VistaPagosViewSet, VistaDeudoresViewSet, VistaProgresoPublicViewSet, EstadoCuentaViewSet


router = DefaultRouter()

router.register(r'cuentahabientes', CuentahabienteViewSet, basename='cuentahabiente')
router.register(r'vista-pagos', VistaPagosViewSet, basename='vista-pagos')
router.register(r'vista-historial', VistaHistorialViewSet, basename='vista-historial')
router.register(r'vista-deudores', VistaDeudoresViewSet, basename='vista-deudores')
router.register(r'vista-progreso', VistaProgresoPublicViewSet, basename='vista-progreso')
router.register(r'estado-cuenta', EstadoCuentaViewSet, basename='estado-cuenta')

urlpatterns = [ 
    path('', include(router.urls)) ,
     path('api/', include(router.urls)),
    ]