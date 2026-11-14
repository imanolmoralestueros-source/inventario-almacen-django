from decimal import Decimal
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, Serializer
from .models import Familia, Material, Atributo, Media


class FamiliaSerializer(ModelSerializer):
    # Este campo no existe en la tabla, se calcula en la consulta (annotate) con la cantidad de materiales activos
    totalMateriales = serializers.IntegerField(read_only=True)

    class Meta:
        model = Familia
        fields = ["id", "nombre", "totalMateriales"]


class AtributoSerializer(ModelSerializer):
    class Meta:
        model = Atributo
        fields = ["nombre", "valor", "unidad"]


class MaterialSerializer(ModelSerializer):
    # Al leer devolvemos tambien el nombre de la familia sin tener que hacer otra consulta desde el cliente
    familiaNombre = serializers.CharField(source="familia.nombre", read_only=True)

    class Meta:
        model = Material
        fields = ["id", "codigo", "descripcion", "cantidad", "unidad", "marca", "modelo",
                  "referenciaFabricante", "tipoMaterial", "aplicacion", "familia", "familiaNombre"]
        # El codigo lo genera la API, el cliente no lo puede enviar ni modificar
        read_only_fields = ["id", "codigo"]


class MaterialDetalleSerializer(ModelSerializer):
    # Serializadores anidados: devuelven la familia y los atributos completos dentro del material
    familia = FamiliaSerializer(read_only=True)
    atributos = AtributoSerializer(many=True, read_only=True)
    # url temporal (firmada) para ver la foto guardada en S3, se agrega en la vista
    url = serializers.CharField(read_only=True, default=None)

    class Meta:
        model = Material
        exclude = ["eliminado", "media"]


class GenerarUrlSerializer(Serializer):
    fileName = serializers.CharField(max_length=100)
    # Solo se aceptan imagenes
    # https://www.iana.org/assignments/media-types
    contentType = serializers.ChoiceField(choices=["image/jpeg", "image/png", "image/webp"])
    ext = serializers.ChoiceField(choices=["jpg", "jpeg", "png", "webp"])


class MediaSerializer(ModelSerializer):
    class Meta:
        model = Media
        fields = ["id", "nombre", "ext", "ruta", "mimeType"]


class SalidaSerializer(Serializer):
    # Cantidad que sale del almacen, debe ser mayor que cero
    cantidad = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    motivo = serializers.CharField(max_length=200, required=False)
