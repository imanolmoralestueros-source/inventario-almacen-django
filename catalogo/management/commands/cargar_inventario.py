"""
Comando personalizado de Django para cargar el inventario inicial desde los CSV de la carpeta data/
Uso: python manage.py cargar_inventario

Se puede ejecutar varias veces: los materiales que ya existen (mismo codigo) se omiten.
"""
import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from catalogo.models import Familia, Material, Atributo

CARPETA_DATA = Path(settings.BASE_DIR) / "data"


def leerCsv(nombreArchivo):
    with open(CARPETA_DATA / nombreArchivo, encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


class Command(BaseCommand):
    help = "Carga familias, materiales y atributos desde data/materiales.csv y data/atributos.csv"

    def handle(self, *args, **options):
        filasMateriales = leerCsv("materiales.csv")
        filasAtributos = leerCsv("atributos.csv")

        # set con los codigos que ya estan en la bd para no duplicarlos
        codigosExistentes = set(Material.objects.values_list("codigo", flat=True))

        # transaction.atomic: si algo falla no se guarda nada (todo o nada)
        with transaction.atomic():
            nuevosMateriales = {}
            for fila in filasMateriales:
                if fila["codigo"] in codigosExistentes:
                    continue

                # get_or_create busca la familia por nombre y si no existe la crea
                familia, _ = Familia.objects.get_or_create(nombre=fila["familia"])

                nuevosMateriales[fila["codigo"]] = Material(
                    codigo=fila["codigo"],
                    descripcion=fila["descripcion"],
                    cantidad=fila["cantidad"] or 0,
                    unidad=fila["unidad"] or "UND",
                    marca=fila["marca"] or None,
                    modelo=fila["modelo"] or None,
                    referenciaFabricante=fila["referencia_fabricante"] or None,
                    tipoMaterial=fila["tipo_material"] or None,
                    aplicacion=fila["aplicacion"] or None,
                    familia=familia,
                )

            # bulk_create inserta todos los materiales en pocas consultas en vez de una por material
            Material.objects.bulk_create(nuevosMateriales.values())

            # Los atributos solo se cargan para los materiales nuevos, asi no se duplican
            nuevosAtributos = [
                Atributo(material=nuevosMateriales[fila["codigo"]], nombre=fila["atributo"],
                         valor=fila["valor"], unidad=fila["unidad"] or None)
                for fila in filasAtributos
                if fila["codigo"] in nuevosMateriales and fila["atributo"] and fila["valor"]
            ]
            Atributo.objects.bulk_create(nuevosAtributos)

        self.stdout.write(self.style.SUCCESS(
            f"Carga completa: {len(nuevosMateriales)} materiales nuevos, {len(nuevosAtributos)} atributos, "
            f"{len(filasMateriales) - len(nuevosMateriales)} ya existian"
        ))
