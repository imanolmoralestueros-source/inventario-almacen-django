from rest_framework.serializers import ModelSerializer, Serializer, EmailField, CharField
from .models import Usuario


class RegistroSerializer(ModelSerializer):
    # La contraseña solo se recibe, nunca se devuelve, y debe tener al menos 8 caracteres
    password = CharField(write_only=True, min_length=8)

    class Meta:
        model = Usuario
        fields = ["id", "nombre", "apellido", "correo", "password", "rol"]
        # El rol no se puede enviar en el registro: todo usuario nuevo es CONSULTA
        read_only_fields = ["id", "rol"]


class LoginSerializer(Serializer):
    correo = EmailField(required=True)
    password = CharField(required=True)


class UsuarioSerializer(ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "nombre", "apellido", "correo", "rol", "creadoEn"]
