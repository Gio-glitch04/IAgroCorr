# IAgroCorr 🌾🛰️

**IAgroCorr** es una plataforma de inteligencia de negocios y monitoreo territorial para el sector agropecuario de la provincia de Corrientes y la region NEA (Argentina). 

Combina sistemas de informacion geografica (**GeoDjango / PostGIS**), series temporales de teledeteccion satelital (**Sentinel-2 / GEE**), trazabilidad de insumos agroquimicos con clasificacion toxicologica **SENASA**, y un motor de reglas espaciales en tiempo real para la preservacion ambiental de la cuenca de los **Esteros del Ibera** y cursos hidricos protegidos.

---

## 🚀 Caracteristicas Principales

1. **Dashboard Agroclimatico y Semáforos en Tiempo Real:**
   - Visualizacion dinamica de parcelas con clasificacion semaforica (Verde, Amarillo, Rojo).
   - KPIs de hectareas totales monitoreadas, humedad edafica superficial y vigor vegetativo NDVI.
2. **Delimitacion Espacial y Validacion Anti-Urbanizacion:**
   - Herramientas interactivas de dibujo poligonal sobre mapas satelitales hibridos (Leaflet-Geoman).
   - Bloqueo automatico en PostGIS ante solapamiento con ejidos urbanos de exclusion.
3. **Motor de Reglas y Cumplimiento Normativo (SENASA / Ley de Agroquimicos):**
   - Calculo topologico de distancias a areas protegidas (Parque y Reserva Natural Esteros del Ibera) y cuerpos de agua (Rios Parana, Uruguay, Corriente, Santa Lucia).
   - Control de derivas y fajas de amortiguamiento segun bandas toxicologicas (Clases Ia, Ib, II, III, IV).
4. **Matriz de Gemelos Globales (Global Twins):**
   - Sincronizacion y analisis comparativo con regiones agroclimaticas analogas en el mundo (Brasil, Uruguay, EE.UU., China, Sudafrica).
5. **Data Warehouse (DW) de Mediciones Ambientales:**
   - Tabla de hechos inmutable para auditoria agronica y reportes con trazabilidad temporal.

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python 3.12, Django 6 (GeoDjango).
- **Base de Datos Espacial:** PostgreSQL 16 + PostGIS 3.4 (Docker).
- **Librerias GIS:** GDAL 3.13, GEOS, PROJ.
- **Frontend:** Bootstrap 5, Leaflet 1.9, Leaflet-Geoman, Esri World Imagery, OpenStreetMap.

---

## 📋 Guia de Instalacion y Puesta en Marcha

Para clonar el proyecto, configurar Docker con PostGIS e instalar las dependencias locales en Windows, consulta la guia detallada:

👉 **[GUIA_INSTALACION.md](GUIA_INSTALACION.md)**

### Inicio Rapido con Docker (recomendado)

Solo necesitas **Docker Desktop**. La app Django y PostGIS corren en contenedores, sin instalar Python ni GDAL en tu PC.

```bash
cp .env.example .env          # opcional: ajustar claves y puertos
docker compose up -d --build  # levanta base de datos + app
docker compose exec web python manage.py poblar_lotes_demo   # datos demo (primera vez)
docker compose exec web python manage.py createsuperuser
```

Abre [http://localhost:8000/dashboard/](http://localhost:8000/dashboard/). El codigo de `iagrocorr_project/` se monta en vivo, asi que los cambios se ven al guardar.

Comandos utiles: `docker compose logs -f web`, `docker compose exec web python manage.py <comando>`, `docker compose down` (los datos quedan en el volumen `iagrocorr_data`).

### Desarrollo con VS Code (Dev Container)

1. Instala la extension **Dev Containers** en VS Code.
2. Abre la carpeta del repo y elige **"Reopen in Container"**.
3. VS Code se conecta al contenedor `web` con Python, Django y GDAL listos; Git y GitHub funcionan desde ahi.
4. El servidor arranca solo en [http://localhost:8000](http://localhost:8000) y se recarga al guardar.
5. Para depurar con breakpoints usa **F5** ("Django: debug"), que levanta una segunda instancia en el puerto 8001.
6. Desde la terminal del contenedor tambien funciona `docker` y la vista de contenedores de VS Code.

### Inicio Rapido local en Windows (sin Docker para la app):
```powershell
# 1. Iniciar PostGIS en Docker
docker compose up -d

# 2. Activar entorno virtual e instalar dependencias
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Aplicar migraciones y poblar datos iniciales
cd iagrocorr_project
python manage.py migrate
python manage.py poblar_lotes_demo

# 4. Iniciar servidor
python manage.py runserver
```

Navega a [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/) para ingresar a la plataforma.
