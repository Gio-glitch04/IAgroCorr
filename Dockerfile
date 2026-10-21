# ========================================================
# IAgroCorr - Imagen de la aplicacion Django (GeoDjango)
# ========================================================
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Librerias geoespaciales del sistema (GDAL, GEOS, PROJ) y cliente de Postgres.
# En Linux GeoDjango las encuentra solas, sin configurar rutas.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gdal-bin libgdal-dev libgeos-dev libproj-dev \
        postgresql-client git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY iagrocorr_project/ /app/

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]
