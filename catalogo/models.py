from django.db import models
from django.core.validators import MinValueValidator


class Familia(models.Model):
    """Agrupa los materiales por tipo: Rodamientos, Material electrico, EPP, etc."""
    nombre = models.CharField(max_length=80, unique=True)

    class Meta:
        db_table = "familias"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Media(models.Model):
    """Datos del archivo guardado en AWS S3. La imagen no se guarda en la bd, solo su ubicacion."""
    nombre = models.CharField(max_length=200)
    ext = models.CharField(max_length=10)
    ruta = models.CharField(max_length=200)
    mimeType = models.CharField(max_length=100, db_column="mime_type")

    class Meta:
        db_table = "medias"

    # Key (ubicacion) del archivo dentro del bucket, ej: materiales/uuid_rodamiento.jpg
    def key(self):
        return self.ruta + self.nombre + "." + self.ext


class Material(models.Model):
    codigo = models.CharField(max_length=20, unique=True)  # Ej. MAT-000001, se genera automaticamente
    descripcion = models.TextField()
    # La cantidad nunca puede ser negativa (validacion del serializer y restriccion en la bd)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    unidad = models.CharField(max_length=10)  # UND, PAR, M, KG...
    marca = models.CharField(max_length=80, null=True, blank=True)
    modelo = models.CharField(max_length=120, null=True, blank=True)
    referenciaFabricante = models.CharField(max_length=120, null=True, blank=True, db_column="referencia_fabricante")
    tipoMaterial = models.CharField(max_length=120, null=True, blank=True, db_column="tipo_material")
    aplicacion = models.TextField(null=True, blank=True)
    # PROTECT: la bd no permite borrar una familia que tenga materiales
    # related_name permite consultar desde la familia: familia.materiales.all()
    familia = models.ForeignKey(to=Familia, on_delete=models.PROTECT, db_column="familia_id", related_name="materiales")
    media = models.ForeignKey(to=Media, on_delete=models.SET_NULL, db_column="media_id", null=True, blank=True)
    # Soft delete: el material no se borra de la bd, solo se marca como eliminado
    eliminado = models.BooleanField(default=False)
    creadoEn = models.DateTimeField(auto_now_add=True, db_column="creado_en")
    actualizadoEn = models.DateTimeField(auto_now=True, db_column="actualizado_en")

    class Meta:
        db_table = "materiales"
        ordering = ["codigo"]
        constraints = [
            models.CheckConstraint(condition=models.Q(cantidad__gte=0), name="ck_materiales_cantidad_no_negativa"),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"


class Atributo(models.Model):
    """Especificacion tecnica de un material (ej. Corriente nominal = 16 A)."""
    nombre = models.CharField(max_length=120)
    valor = models.TextField()
    unidad = models.CharField(max_length=30, null=True, blank=True)
    # CASCADE: si un material se borrara fisicamente, sus atributos tambien
    material = models.ForeignKey(to=Material, on_delete=models.CASCADE, db_column="material_id", related_name="atributos")

    class Meta:
        db_table = "atributos"
