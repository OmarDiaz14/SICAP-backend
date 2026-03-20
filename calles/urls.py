from rest_framework.routers import DefaultRouter
from .views import CalleViewSet

router = DefaultRouter()
router.register(r'calles', CalleViewSet, basename='calle')

urlpatterns = router.urls