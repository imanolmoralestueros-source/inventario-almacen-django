from django.contrib import admin
from .models import Familia, Material, Atributo


@admin.register(Familia)
class FamiliaAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre"]
    search_fields = ["nombre"]


class AtributoInline(admin.TabularInline):
    model = Atributo
    extra = 0


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ["codigo", "descripcion", "cantidad", "unidad", "familia", "eliminado"]
    list_filter = ["familia", "eliminado"]
    search_fields = ["codigo", "descripcion", "marca"]
    inlines = [AtributoInline]
