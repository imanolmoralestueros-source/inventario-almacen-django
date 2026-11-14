from os import getenv
from boto3 import client
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

# boto3 lee las credenciales automaticamente de las variables de entorno:
# AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY y AWS_DEFAULT_REGION
# https://docs.aws.amazon.com/boto3/latest/guide/s3-presigned-urls.html


def clienteS3():
    # Firma version 4 y endpoint de la region del bucket: asi la url firmada funciona en cualquier region
    region = getenv("AWS_DEFAULT_REGION", "us-east-1")
    return client("s3", region_name=region, endpoint_url=f"https://s3.{region}.amazonaws.com",
                  config=Config(signature_version="s3v4"))


def awsConfigurado():
    return bool(getenv("BUCKET_NAME") and getenv("AWS_ACCESS_KEY_ID") and getenv("AWS_SECRET_ACCESS_KEY"))


def generarUrlSubida(key: str, contentType: str):
    """URL firmada para que el cliente suba el archivo DIRECTO a S3 (metodo PUT)."""
    s3 = clienteS3()
    return s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": getenv("BUCKET_NAME"),
            "Key": key,
            "ContentType": contentType
        },
        ExpiresIn=300  # 5 minutos para subir el archivo
    )


def generarUrlLectura(key: str):
    """URL firmada para ver el archivo. El bucket es privado, sin esta url no se puede abrir."""
    # Si AWS no esta configurado el detalle del material igual responde, solo que sin foto
    if not awsConfigurado():
        return None
    try:
        s3 = clienteS3()
        return s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": getenv("BUCKET_NAME"),
                "Key": key
            },
            ExpiresIn=900  # 15 minutos
        )
    except (BotoCoreError, ClientError):
        return None
