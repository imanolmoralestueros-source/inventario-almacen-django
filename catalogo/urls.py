from django.urls import path
from .views import (FamiliasView, FamiliaView, MaterialesView, MaterialView,
                    registrarSalida, generarUrl, asociarFoto)

urlpatterns = [
    path("familias", FamiliasView.as_view()),
    path("familias/<int:id>", FamiliaView.as_view()),
    path("materiales", MaterialesView.as_view()),
    path("materiales/<int:id>", MaterialView.as_view()),
    path("materiales/<int:id>/salida", registrarSalida),
    path("materiales/<int:id>/foto", asociarFoto),
    path("generar-url", generarUrl),
]
