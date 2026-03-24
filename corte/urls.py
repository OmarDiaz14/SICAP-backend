# corte/urls.py
from django.urls import path
from .views import (CorteView, 
                    CorteCajaJrListView,
                    CorteCajaJrDetalleView,
                    CorteCajaJrGenerarView, 
                    SubirPdfCorteJrView,
                    ValidarCorteJrView,


                    ##Tesorero Sr
                    CorteCajaSrGenerarView,
                    CorteCajaSrListView,
                    CorteCajaSrDetalleView,
                    SubirPdfCorteSrView,
                    ValidarCorteSrView,


                    ##consultar pdf
                    CorteCajaJrPdfView,
                    CorteCajaSrPdfView,
)
urlpatterns = [
    # Esto crea la ruta: http://localhost:8000/api/corte/generar/
    path('generar/', CorteView.as_view(), name='generar-corte'),
    # Rutas para Tesorero Jr
    path('jr/', CorteCajaJrListView.as_view(), name='corte-jr-list-create'),
    path('jr/generar/', CorteCajaJrGenerarView.as_view(), name='corte-jr-generar'),
    path('jr/<int:folio>/', CorteCajaJrDetalleView.as_view(), name='corte-jr-detail'),
    path('jr/<int:folio>/pdf/', SubirPdfCorteJrView.as_view(), name='corte-jr-pdf'),
    path('jr/<int:folio>/validar/', ValidarCorteJrView.as_view(), name='corte-jr-validar'),
    ## Rutas para Tesorero Sr
    path("sr/",                      CorteCajaSrListView.as_view(),    name="corte-sr-list"),
    path("sr/generar/",              CorteCajaSrGenerarView.as_view(), name="corte-sr-generar"),
    path("sr/<int:folio>/",          CorteCajaSrDetalleView.as_view(), name="corte-sr-detalle"),
    path("sr/<int:folio>/pdf/",      SubirPdfCorteSrView.as_view(),    name="corte-sr-pdf"),
    path("sr/<int:folio>/validar/",  ValidarCorteSrView.as_view(),     name="corte-sr-validar"), 


    ##ruta de consulta pdf 
    path("jr/<int:folio>/ver-pdf/",  CorteCajaJrPdfView.as_view(), name="corte-jr-ver-pdf"),
    path("sr/<int:folio>/ver-pdf/",  CorteCajaSrPdfView.as_view(), name="corte-sr-ver-pdf"),
]