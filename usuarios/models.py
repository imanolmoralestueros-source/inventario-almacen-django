from django.db import models
from uuid import uuid4
# AbstractBaseUser permite definir por completo las columnas del auth_user
# PermissionsMixin agrega la relacion con los grupos y permisos del panel administrativo
# BaseUserManager maneja como se crean los usuarios (por ejemplo con createsuperuser)
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

# Roles del sistema: la llave se guarda en la bd y el valor se muestra en el panel administrativo
ROLES_USUARIO = {
    "ADMIN": "ADMIN",        # Puede crear, modificar y dar de baja
    "CONSULTA": "CONSULTA",  # Solo puede consultar el catalogo
}


class ManejadorUsuario(BaseUserManager):
    def create_user(self, correo, nombre, password, rol=ROLES_USUARIO["CONSULTA"], **extra):
        if not correo:
            raise ValueError("El correo es obligatorio")

        # normalize_email deja el dominio en minusculas (Juan@GMAIL.com > Juan@gmail.com)
        nuevoUsuario = self.model(correo=self.normalize_email(correo), nombre=nombre, rol=rol, **extra)
        # set_password genera el hash de la contraseña, nunca se guarda en texto plano
        nuevoUsuario.set_password(password)
        nuevoUsuario.save()
        return nuevoUsuario

    # Se usa al ejecutar: python manage.py createsuperuser
    # El superusuario es el ADMIN del almacen y ademas puede entrar al panel administrativo
    def create_superuser(self, correo, nombre, password, **extra):
        extra["is_staff"] = True
        extra["is_superuser"] = True
        return self.create_user(correo, nombre, password, rol=ROLES_USUARIO["ADMIN"], **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid4)
    nombre = models.TextField()
    apellido = models.TextField(null=True)
    correo = models.EmailField(unique=True)
    rol = models.TextField(choices=ROLES_USUARIO, default=ROLES_USUARIO["CONSULTA"])
    creadoEn = models.DateTimeField(auto_now_add=True, db_column="creado_en")

    # Atributos obligatorios si queremos seguir usando el panel administrativo
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # El login se hace con el correo
    USERNAME_FIELD = "correo"
    # Campos que pedira el createsuperuser ademas del correo y el password
    REQUIRED_FIELDS = ["nombre"]

    objects = ManejadorUsuario()

    class Meta:
        db_table = "usuarios"

    def __str__(self):
        return self.correo
