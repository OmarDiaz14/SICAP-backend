from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PagarCargoView

urlpatterns = [ path("pagar-cargo/", PagarCargoView.as_view(), name="pagar-cargo") ]