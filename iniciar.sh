#!/bin/sh
# Script de arranque del contenedor (se usa igual en Docker Compose y en Render)
# set -e detiene el script si algun comando falla
set -e

# 1. Aplica las migraciones pendientes en la base de datos
python manage.py migrate --noinput

# 2. Carga el inventario inicial (si los materiales ya existen no los duplica)
python manage.py cargar_inventario

# 3. Crea el administrador con las variables DJANGO_SUPERUSER_* (si ya existe, solo muestra un aviso)
python manage.py createsuperuser --noinput || echo "El administrador ya existe"

# 4. Levanta la API con gunicorn (servidor para produccion), Render envia el puerto en la variable PORT
exec gunicorn inventario.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2
