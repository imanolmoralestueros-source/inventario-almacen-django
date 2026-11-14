# Imagen base de python liviana
FROM python:3.13-slim

# PYTHONDONTWRITEBYTECODE evita que python cree archivos .pyc
# PYTHONUNBUFFERED hace que los print y logs salgan de inmediato
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primero copiamos solo el requirements para aprovechar la cache de capas:
# si el codigo cambia pero las librerias no, docker no vuelve a instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usuario sin privilegios: la app no corre como root dentro del contenedor
RUN useradd -m almacen && chown -R almacen:almacen /app
USER almacen

EXPOSE 8000

CMD ["sh", "iniciar.sh"]
