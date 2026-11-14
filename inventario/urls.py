from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


# Ruta publica para comprobar que el servicio esta levantado (util en Render y en Docker)
def estado(request):
    return JsonResponse({"message": "API de inventario de almacen funcionando"})


urlpatterns = [
    path("", estado),
    path("admin/", admin.site.urls),
    path("auth/", include("usuarios.urls")),
    path("catalogo/", include("catalogo.urls")),
]
