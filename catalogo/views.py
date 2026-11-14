from uuid import uuid4
from django.db import transaction
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from botocore.exceptions import BotoCoreError, ClientError
from usuarios.permissions import EsAdminOSoloLectura
from .models import Familia, Material
from .serializers import (FamiliaSerializer, MaterialSerializer, MaterialDetalleSerializer,
                          GenerarUrlSerializer, MediaSerializer, SalidaSerializer)
from .pagination import PaginacionEstandar
from .aws import generarUrlSubida, generarUrlLectura, awsConfigurado


# ------------------------------------------------------------------ FAMILIAS

def consultaFamilias():
    # annotate agrega una columna calculada: cuantos materiales activos (no eliminados) tiene cada familia
    # SELECT f.*, COUNT(m.id) FILTER (WHERE m.eliminado = false) AS "totalMateriales" ... GROUP BY f.id
    # En consultas con GROUP BY Django ignora el ordering del modelo, por eso se ordena explicitamente
    return Familia.objects.annotate(
        totalMateriales=Count("materiales", filter=Q(materiales__eliminado=False))
    ).order_by("nombre")


class FamiliasView(APIView):
    permission_classes = [EsAdminOSoloLectura]

    def get(self, request: Request):
        serializador = FamiliaSerializer(instance=consultaFamilias(), many=True)
        return Response(data={
            "content": serializador.data
        })

    def post(self, request: Request):
        serializador = FamiliaSerializer(data=request.data)
        if serializador.is_valid():
            serializador.save()
            return Response(data={
                "message": "Familia creada exitosamente",
                "content": serializador.data
            }, status=status.HTTP_201_CREATED)
        return Response(data={
            "message": "Error al crear la familia",
            "content": serializador.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class FamiliaView(APIView):
    permission_classes = [EsAdminOSoloLectura]

    def get(self, request: Request, id):
        familiaEncontrada = consultaFamilias().filter(id=id).first()
        if not familiaEncontrada:
            return Response(data={"message": "La familia no existe"}, status=status.HTTP_404_NOT_FOUND)

        return Response(data={
            "content": FamiliaSerializer(instance=familiaEncontrada).data
        })

    def put(self, request: Request, id):
        familiaEncontrada = Familia.objects.filter(id=id).first()
        if not familiaEncontrada:
            return Response(data={"message": "La familia no existe"}, status=status.HTTP_404_NOT_FOUND)

        serializador = FamiliaSerializer(instance=familiaEncontrada, data=request.data)
        if serializador.is_valid():
            serializador.save()
            return Response(data={
                "message": "Familia actualizada exitosamente",
                "content": serializador.data
            })
        return Response(data={
            "message": "Error al actualizar la familia",
            "content": serializador.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request: Request, id):
        familiaEncontrada = Familia.objects.filter(id=id).first()
        if not familiaEncontrada:
            return Response(data={"message": "La familia no existe"}, status=status.HTTP_404_NOT_FOUND)

        # Regla de negocio: no se elimina una familia que tiene materiales (incluye los dados de baja,
        # porque siguen en la bd como historial). Se responde 409 Conflict en vez de dejar que la bd falle
        if familiaEncontrada.materiales.exists():
            return Response(data={
                "message": "No se puede eliminar una familia que tiene materiales registrados"
            }, status=status.HTTP_409_CONFLICT)

        familiaEncontrada.delete()
        return Response(data=None, status=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------ MATERIALES

def generarCodigo():
    # Busca el ultimo codigo registrado (incluye los eliminados para no repetir codigos) y le suma 1
    ultimoCodigo = Material.objects.order_by("-codigo").values_list("codigo", flat=True).first()
    numero = int(ultimoCodigo.split("-")[1]) + 1 if ultimoCodigo else 1
    return f"MAT-{numero:06d}"  # MAT-000342


class MaterialesView(APIView):
    permission_classes = [EsAdminOSoloLectura]

    def get(self, request: Request):
        familia = request.query_params.get("familia")
        buscar = request.query_params.get("buscar")

        # Regla de negocio: el listado solo muestra materiales activos
        # select_related trae la familia en la misma consulta (JOIN) y evita una consulta por cada material
        materiales = Material.objects.filter(eliminado=False).select_related("familia")

        if familia:
            if not familia.isdigit():
                return Response(data={"message": "El id de la familia debe ser numerico"},
                                status=status.HTTP_400_BAD_REQUEST)
            materiales = materiales.filter(familia_id=familia)

        if buscar:
            # Q permite hacer un OR entre condiciones, icontains equivale a un ILIKE '%texto%'
            texto = buscar.strip()
            materiales = materiales.filter(
                Q(descripcion__icontains=texto) | Q(codigo__icontains=texto) | Q(marca__icontains=texto)
            )

        paginador = PaginacionEstandar()
        resultado = paginador.paginate_queryset(materiales, request, view=self)
        serializador = MaterialSerializer(instance=resultado, many=True)
        return paginador.get_paginated_response(serializador.data)

    def post(self, request: Request):
        serializador = MaterialSerializer(data=request.data)
        if serializador.is_valid():
            # El codigo no viene del cliente, lo generamos antes de guardar
            serializador.save(codigo=generarCodigo())
            return Response(data={
                "message": "Material creado exitosamente",
                "content": serializador.data
            }, status=status.HTTP_201_CREATED)
        return Response(data={
            "message": "Error al crear el material",
            "content": serializador.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class MaterialView(APIView):
    permission_classes = [EsAdminOSoloLectura]

    def get(self, request: Request, id):
        # prefetch_related trae todos los atributos en una sola consulta adicional
        materialEncontrado = (Material.objects.filter(id=id, eliminado=False)
                              .select_related("familia", "media").prefetch_related("atributos").first())
        if not materialEncontrado:
            return Response(data={"message": "El material no existe"}, status=status.HTTP_404_NOT_FOUND)

        # La familia anidada muestra su total de materiales activos
        materialEncontrado.familia.totalMateriales = materialEncontrado.familia.materiales.filter(eliminado=False).count()

        # Si tiene foto, agregamos a la instancia el atributo url que hace match con el del serializador
        if materialEncontrado.media:
            materialEncontrado.url = generarUrlLectura(materialEncontrado.media.key())

        return Response(data={
            "content": MaterialDetalleSerializer(instance=materialEncontrado).data
        })

    def patch(self, request: Request, id):
        materialEncontrado = Material.objects.filter(id=id, eliminado=False).first()
        if not materialEncontrado:
            return Response(data={"message": "El material no existe"}, status=status.HTTP_404_NOT_FOUND)

        # partial=True permite enviar solo los campos que se quieren modificar
        serializador = MaterialSerializer(instance=materialEncontrado, data=request.data, partial=True)
        if serializador.is_valid():
            serializador.save()
            return Response(data={
                "message": "Material actualizado exitosamente",
                "content": serializador.data
            })
        return Response(data={
            "message": "Error al actualizar el material",
            "content": serializador.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request: Request, id):
        materialEncontrado = Material.objects.filter(id=id, eliminado=False).first()
        if not materialEncontrado:
            return Response(data={"message": "El material no existe"}, status=status.HTTP_404_NOT_FOUND)

        # Soft delete: no se borra el registro, se marca como eliminado y deja de aparecer en el listado
        materialEncontrado.eliminado = True
        materialEncontrado.save()
        return Response(data=None, status=status.HTTP_204_NO_CONTENT)


@api_view(http_method_names=["POST"])
@permission_classes([EsAdminOSoloLectura])
def registrarSalida(request: Request, id):
    """Regla de negocio: descuenta stock y no permite que la cantidad quede negativa."""
    serializador = SalidaSerializer(data=request.data)
    if not serializador.is_valid():
        return Response(data={
            "message": "Error en la salida",
            "content": serializador.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    cantidadSalida = serializador.validated_data.get("cantidad")

    # transaction.atomic + select_for_update bloquean la fila del material mientras se descuenta,
    # asi dos salidas al mismo tiempo no pueden dejar el stock en negativo
    with transaction.atomic():
        materialEncontrado = Material.objects.select_for_update().filter(id=id, eliminado=False).first()
        if not materialEncontrado:
            return Response(data={"message": "El material no existe"}, status=status.HTTP_404_NOT_FOUND)

        if cantidadSalida > materialEncontrado.cantidad:
            return Response(data={
                "message": "Stock insuficiente",
                "content": {
                    "disponible": str(materialEncontrado.cantidad),
                    "solicitado": str(cantidadSalida)
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        materialEncontrado.cantidad -= cantidadSalida
        materialEncontrado.save()

    return Response(data={
        "message": "Salida registrada exitosamente",
        "content": MaterialSerializer(instance=materialEncontrado).data
    })


# ------------------------------------------------------------------ FOTOS EN AWS S3
# Flujo (el mismo de la clase de S3):
# 1. POST /catalogo/generar-url          > la API devuelve una url firmada para subir el archivo
# 2. PUT <url firmada>                    > el cliente sube la imagen DIRECTO a S3 (no pasa por nuestro servidor)
# 3. POST /catalogo/materiales/<id>/foto  > se registra la media y se asocia al material
# 4. GET  /catalogo/materiales/<id>       > el detalle devuelve una url firmada para ver la foto

@api_view(http_method_names=["POST"])
@permission_classes([EsAdminOSoloLectura])
def generarUrl(request: Request):
    serializador = GenerarUrlSerializer(data=request.data)
    if not serializador.is_valid():
        return Response(data={
            "message": "Error al generar la url",
            "content": serializador.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    fileName = serializador.validated_data.get("fileName")
    ext = serializador.validated_data.get("ext")
    contentType = serializador.validated_data.get("contentType")
    if not awsConfigurado():
        return Response(data={"message": "El servicio de archivos (AWS S3) no esta configurado"},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)

    ruta = "materiales/"
    # El uuid evita que dos archivos con el mismo nombre se sobreescriban en el bucket
    nombre = str(uuid4()) + "_" + fileName

    try:
        url = generarUrlSubida(ruta + nombre + "." + ext, contentType)
    except (BotoCoreError, ClientError):
        return Response(data={"message": "No se pudo generar la url de subida en AWS S3"},
                        status=status.HTTP_502_BAD_GATEWAY)

    return Response(data={
        "content": {
            "url": url,
            "nombre": nombre,
            "ext": ext,
            "mimeType": contentType,
            "ruta": ruta
        }
    })


@api_view(http_method_names=["POST"])
@permission_classes([EsAdminOSoloLectura])
def asociarFoto(request: Request, id):
    materialEncontrado = Material.objects.filter(id=id, eliminado=False).first()
    if not materialEncontrado:
        return Response(data={"message": "El material no existe"}, status=status.HTTP_404_NOT_FOUND)

    serializador = MediaSerializer(data=request.data)
    if not serializador.is_valid():
        return Response(data={
            "message": "Error al registrar la foto",
            "content": serializador.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    nuevaMedia = serializador.save()
    materialEncontrado.media = nuevaMedia
    materialEncontrado.save()

    return Response(data={
        "message": "Foto asociada al material exitosamente",
        "content": {
            "media": serializador.data,
            "url": generarUrlLectura(nuevaMedia.key())
        }
    }, status=status.HTTP_201_CREATED)
