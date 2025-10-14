from django.urls import path
from .views import SignupView,LoginView, MeView


urlpatterns = [
    path('auth/signup/', SignupView.as_view(), name='cobrador-signup'),
    path('auth/login/', LoginView.as_view(), name='cobrador-login'),
    path('auth/me/', MeView.as_view(), name='cobrador-me'),
]