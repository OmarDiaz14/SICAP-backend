# corte/urls.py
from django.urls import path
from .views import CorteView 

urlpatterns = [
    # Esto crea la ruta: http://localhost:8000/api/corte/generar/
    path('generar/', CorteView.as_view(), name='generar-corte'),
]