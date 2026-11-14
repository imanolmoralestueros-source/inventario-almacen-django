from django.urls import path
from .views import registroUsuario, login, perfilUsuario

urlpatterns = [
    path("registro", registroUsuario),
    path("login", login),
    path("perfil", perfilUsuario),
]
