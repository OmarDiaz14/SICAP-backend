from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AsignacionViewSet


router = DefaultRouter()
router.register(r'asignaciones', AsignacionViewSet, basename='asignacion')

urlpatterns = [
    path('', include(router.urls)),
]