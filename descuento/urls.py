from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DescuentoViewSet

router = DefaultRouter()
router.register(r'descuentos', DescuentoViewSet, basename='descuento')

urlpatterns = [
    path('', include(router.urls)),
]