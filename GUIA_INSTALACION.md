# Guia de Instalacion y Puesta en Marcha - IAgroCorr

Guia tecnica completa para clonar, configurar el entorno local y ejecutar **IAgroCorr** con soporte completo para **GeoDjango, PostGIS y Leaflet**.

---

## 1. Arquitectura del Entorno

IAgroCorr integra un **Data Warehouse espacial** con capas vectoriales de ordenamiento territorial:
- **Base de Datos Espacial:** PostgreSQL 16 + PostGIS 3.4 corriendo en contenedor Docker.
- **Backend:** Django 6 con `django.contrib.gis` (GeoDjango).
- **Librerias C++ Geoespaciales:** GDAL y GEOS vinculados en Windows via wheels binarios precompilados.
- **Frontend Geo:** Leaflet, Leaflet-Geoman y capas satelitales hibridas de Esri / OSM.

---

## 2. Requisitos Previos

Antes de comenzar, asegurarse de tener instalado en el equipo:
1. **Git:** [https://git-scm.com/](https://git-scm.com/)
2. **Python 3.12 (64-bit):** [https://www.python.org/downloads/](https://www.python.org/downloads/) *(Marcar la casilla "Add Python to PATH" durante la instalacion).*
3. **Docker Desktop:** [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/) *(Debe estar iniciado con el motor WSL2 / Linux activado).*

---

## 3. Paso a Paso de Instalacion

### Paso 1: Clonar el Repositorio y Cambiar de Rama
Abrir una terminal (PowerShell en Windows) y clonar el repositorio:

```powershell
git clone <URL_DEL_REPOSITORIO>
cd IAgroCorr
git checkout feature/postgis-monitoring
```

---

### Paso 2: Iniciar la Base de Datos PostGIS en Docker
En la raiz del proyecto (`C:\IAgroCorr`), ejecutar:

```powershell
docker compose up -d
```

> **IMPORTANTE - Mapeo de Puertos:**
> La base de datos esta configurada en el puerto host **`5433`** (`5433:5432`). Esto previene conflictos con instalaciones nativas de PostgreSQL en Windows que suelen ocupar el puerto 5432.
>
> **Credenciales configuradas:**
> - **Host:** `localhost`
> - **Puerto:** `5433`
> - **Base de Datos:** `iagrocorr`
> - **Usuario:** `admin_iagrocorr`
> - **Contrasena:** `i4Gr0coRr_dB`

Para comprobar que el contenedor esta corriendo correctamente:
```powershell
docker compose ps
```
Debe figurar `iagrocorr_db_postgis` en estado `Up`.

---

### Paso 3: Crear y Activar el Entorno Virtual Python
Desde la raiz del proyecto (`C:\IAgroCorr`):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

*(Si PowerShell arroja error de directivas de ejecucion de scripts, ejecutar una sola vez: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` y volver a activar).*

---

### Paso 4: Instalar las Dependencias con `requirements.txt`
Con el entorno virtual activo `(venv)`:

```powershell
pip install -r requirements.txt
```

> **Nota Tecnica sobre GDAL en Windows:**
> `requirements.txt` incluye el indice auxiliar `--extra-index-url https://gisidx.github.io/gwi`, el cual descarga e instala automaticamente la version binaria precompilada de GDAL para Windows x64 (`gdal-3.13.3-cp312-cp312-win_amd64.whl`). Esto evita tener que instalar Microsoft Visual C++ Build Tools.
>
> Si por alguna razon fuera necesario instalar GDAL manualmente:
> ```powershell
> pip install --index https://gisidx.github.io/gwi gdal
> ```

---

### Paso 5: Auto-Descubrimiento de GDAL y GEOS en Django
No es necesario configurar variables de entorno del sistema de Windows de forma manual. El archivo `iagrocorr_project/settings.py` detecta automaticamente la carpeta `osgeo` dentro de tu entorno virtual:

```python
if os.name == 'nt':
    VENV_BASE = Path(sys.prefix)
    OSGEO_DIR = VENV_BASE / 'Lib' / 'site-packages' / 'osgeo'
    if OSGEO_DIR.exists():
        os.environ['PATH'] = str(OSGEO_DIR) + ';' + os.environ.get('PATH', '')
        os.environ['PROJ_LIB'] = str(OSGEO_DIR / 'data' / 'proj')
        os.environ['GDAL_DATA'] = str(OSGEO_DIR / 'data' / 'gdal')
        GDAL_LIBRARY_PATH = str(OSGEO_DIR / 'gdal.dll')
        GEOS_LIBRARY_PATH = str(OSGEO_DIR / 'geos_c.dll')
```

---

### Paso 6: Aplicar las Migraciones a PostGIS
Ingresar a la carpeta del proyecto Django y aplicar las migraciones:

```powershell
cd iagrocorr_project
python manage.py migrate
```

Esto creara todas las tablas relacionales y geoespaciales:
- Capas de exclusion periurbana (`monitoring_zonaurbana`).
- Lotes con geometrias MultiPolygon (`monitoring_lote`).
- Capa de conservacion ambiental (`monitoring_areaprotegida` - Esteros del Ibera).
- Red hidrologica provincial (`monitoring_cuerpodeagua` - Rios Parana, Uruguay, Corriente, Santa Lucia, etc.).
- Eventos de aplicacion de fitosanitarios (`monitoring_aplicacioninsumo`).
- Tabla de hechos de series de tiempo del Data Warehouse (`monitoring_hechomedicionambiental`).
- Matriz de analogos agroclimaticos mundiales (`monitoring_gemeloglobal`).

---

### Paso 7: Crear el Usuario Administrador (Superuser)
```powershell
python manage.py createsuperuser
```
Ingresar el nombre de usuario deseado (ej: `admin`), correo y contrasena.

---

### Paso 8: Poblar las Capas Territoriales, Lotes Demo y Gemelos Globales
Ejecutar el comando de carga de datos iniciales:

```powershell
python manage.py poblar_lotes_demo
```

Este comando realiza de manera automatica:
1. Georreferencia los **5 ejidos urbanos de exclusion** (Corrientes Capital, Goya, Mercedes, Paso de los Libres, Virasoro).
2. Georreferencia la **Reserva y Parque Provincial Esteros del Ibera** con su zona de amortiguamiento de 1.000m.
3. Indexa la **red de cursos de agua y rios principales** de la provincia.
4. Registra **3 lotes de prueba** con cultivos tipicos (Arroz en Mercedes, Tabaco en Goya, Forestal en Virasoro).
5. Asigna aplicaciones de fitosanitarios segun **Bandas Toxicologicas SENASA** (Clases Ia, Ib, II, IV).
6. Dispara el **motor de reglas espaciales en tiempo real**, asignando los semaforos de riesgo ambiental y distancias topologicas.
7. Carga los **5 Gemelos Globales** con sus firmas agroclimaticas (Brasil, Uruguay, EE.UU., China, Sudafrica).

---

### Paso 9: Iniciar el Servidor de Desarrollo
```powershell
python manage.py runserver
```

Abrir el navegador e ingresar a las siguientes rutas:
- **Dashboard Operativo & Mapa Interactivo:** [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)
- **Matriz de Gemelos Globales:** [http://127.0.0.1:8000/global-twins/](http://127.0.0.1:8000/global-twins/)
- **Panel Administrativo GIS:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 4. Rutina Diaria (Pausar y Reanudar Trabajo)

### Para pausar al terminar el dia:
1. Detener el servidor Django en la terminal: `Ctrl + C`
2. Detener la base de datos sin borrar datos:
   ```powershell
   docker compose stop
   ```

### Para reanudar al dia siguiente:
1. Iniciar la base de datos:
   ```powershell
   docker compose start
   ```
2. Activar el entorno virtual:
   ```powershell
   cd C:\IAgroCorr
   .\venv\Scripts\Activate.ps1
   ```
3. Iniciar el servidor:
   ```powershell
   cd iagrocorr_project
   python manage.py runserver
   ```

---

## 5. Preguntas Frecuentes y Resolucion de Problemas

#### A. Error `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf3` al conectar a la DB
**Causa:** Django intento conectarse al puerto `5432` donde habia un servicio local de PostgreSQL de Windows.
**Solucion:** Verificar que en `settings.py` el puerto sea `'5433'` y que el contenedor de Docker este activo en el puerto `5433:5432`.

#### B. Error `ImproperlyConfigured: Could not find the GDAL library`
**Causa:** No se encuentra la libreria GDAL instalada en el venv.
**Solucion:** Asegurarse de ejecutar `pip install -r requirements.txt` teniendo el entorno virtual activo. Verificar que exista la carpeta `venv/Lib/site-packages/osgeo`.

#### C. Error de permisos de scripts en PowerShell al ejecutar `Activate.ps1`
**Solucion:** Ejecutar en PowerShell:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
y volver a correr `.\venv\Scripts\Activate.ps1`.
