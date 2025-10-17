from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CuentahabienteViewSet

router = DefaultRouter()

router.register(r'cuentahabientes', CuentahabienteViewSet, basename='cuentahabiente')

urlpatterns = [ path('', include(router.urls)) ]