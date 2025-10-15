from django.urls import path, include
from .views import ColoniaViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'colonias', ColoniaViewSet, basename='colonia')

urlpatterns = [
    path('', include(router.urls)),
]