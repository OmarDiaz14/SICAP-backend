from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (EstadoCuentaResumenViewSet, CierreAnualViewSet, 
                    CuentahabienteViewSet, RCuentahabientesViewSet, VistaHistorialViewSet,
                    VistaPagosViewSet, VistaDeudoresViewSet, VistaProgresoPublicViewSet, EstadoCuentaViewSet
                    , VistaCargosViewSet, EstadoCuentaNewViewSet, ReporteCargosViewSet)


router = DefaultRouter()

router.register(r'cuentahabientes', CuentahabienteViewSet, basename='cuentahabiente')
router.register(r'vista-pagos', VistaPagosViewSet, basename='vista-pagos')
router.register(r'vista-historial', VistaHistorialViewSet, basename='vista-historial')
router.register(r'vista-deudores', VistaDeudoresViewSet, basename='vista-deudores')
router.register(r'vista-progreso', VistaProgresoPublicViewSet, basename='vista-progreso')
router.register(r'estado-cuenta', EstadoCuentaViewSet, basename='estado-cuenta')
router.register(r'r-cuentahabientes', RCuentahabientesViewSet, basename='r-cuentahabientes')
router.register(r'cierre-anual', CierreAnualViewSet, basename='cierre-anual')
router.register(r'estado-cuenta-resumen', EstadoCuentaResumenViewSet, basename='estado-cuenta-resumen')
router.register(r"vista-cargos", VistaCargosViewSet, basename="vista-cargos")
router.register(r"estado-cuenta-new", EstadoCuentaNewViewSet, basename="estado-cuenta-new")
router.register(r"reporte-cargos", ReporteCargosViewSet, basename="reporte-cargos")

urlpatterns = [ 
    path('', include(router.urls)) ,
     path('api/', include(router.urls)),
    ]