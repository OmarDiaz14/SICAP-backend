from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CargoViewSet, TipoCargoViewSet

router = DefaultRouter()
router.register(r'cargos', CargoViewSet, basename='cargo')
router.register(r"tipos-cargo", TipoCargoViewSet, basename="tipos-cargo")

urlpatterns = [ path('', include(router.urls)) ]