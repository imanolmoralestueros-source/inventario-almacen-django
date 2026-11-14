from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegistroSerializer, LoginSerializer, UsuarioSerializer
from .models import Usuario


@api_view(http_method_names=["POST"])
def registroUsuario(request: Request):
    serializador = RegistroSerializer(data=request.data)

    if serializador.is_valid():
        # create_user se encarga de normalizar el correo y guardar el hash de la contraseña
        nuevoUsuario = Usuario.objects.create_user(**serializador.validated_data)

        return Response(data={
            "message": "Usuario registrado exitosamente",
            "content": UsuarioSerializer(instance=nuevoUsuario).data
        }, status=status.HTTP_201_CREATED)
    else:
        return Response(data={
            "message": "Error al registrar el usuario",
            "content": serializador.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(http_method_names=["POST"])
def login(request: Request):
    serializador = LoginSerializer(data=request.data)

    if not serializador.is_valid():
        return Response(data={
            "message": "Error al hacer el login",
            "content": serializador.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    correo = serializador.validated_data.get("correo")
    password = serializador.validated_data.get("password")

    usuarioEncontrado = Usuario.objects.filter(correo=correo, is_active=True).first()

    # Si el usuario no existe o la contraseña no coincide se responde el mismo mensaje
    # para no revelar que correos estan registrados
    if not usuarioEncontrado or not usuarioEncontrado.check_password(password):
        return Response(data={
            "message": "Credenciales invalidas"
        }, status=status.HTTP_401_UNAUTHORIZED)

    # RefreshToken genera la sesion y de ella obtenemos la token de acceso
    token = RefreshToken.for_user(usuarioEncontrado)

    return Response(data={
        "message": "Login exitoso",
        "content": {
            "accessToken": str(token.access_token),
            "rol": usuarioEncontrado.rol
        }
    })


@api_view(http_method_names=["GET"])
@permission_classes([IsAuthenticated])
def perfilUsuario(request: Request):
    # request.user es la instancia del usuario dueño de la JWT
    serializador = UsuarioSerializer(instance=request.user)
    return Response(data={
        "content": serializador.data
    })
