from django.urls import path
from .views import SignupView,LoginView, MeView,AdminCreateUserView, CobradorEstadoView
from .views import CobradorListView


urlpatterns = [
    path('auth/signup/', SignupView.as_view(), name='cobrador-signup'),
    path('auth/login/', LoginView.as_view(), name='cobrador-login'),
    path('auth/me/', MeView.as_view(), name='cobrador-me'),

    #solo es para Admin crear usuarios(y elegir el rol)
    path('auth/users/', AdminCreateUserView.as_view(), name='cobrador-users'), 

    #listado de cobradores 
    path('auth/cobradores/',CobradorListView.as_view(), name = 'cobrador-list' ),

    path('auth/cobradores/<int:pk>/estado/', CobradorEstadoView.as_view(), name='cobrador-estado'),

] 