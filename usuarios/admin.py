from django.contrib import admin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ["correo", "nombre", "rol", "is_active"]
    search_fields = ["correo", "nombre"]
    exclude = ["password"]
