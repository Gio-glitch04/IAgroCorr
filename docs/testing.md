# Guía de Pruebas, Validación y Control de Calidad — IAgroCorr (`testing.md`)

Este documento establece los procedimientos estándar para verificar el funcionamiento de **IAgroCorr** en sus tres modalidades de ejecución (Docker Compose, VS Code Dev Container y entorno local Windows), junto con el protocolo de pruebas funcionales/geoespaciales y las pautas para pruebas automatizadas en **GeoDjango + PostGIS**.

---

## 1. Preparación del Entorno de Pruebas

### Opción A: Docker Compose Completo (Recomendada — Sin dependencias en host)
```powershell
# 1. Levantar base de datos PostGIS + aplicación Django
docker compose up -d --build

# 2. Verificar que ambos contenedores estén saludables (Up / healthy)
docker compose ps

# 3. Verificar configuración interna de Django
docker compose exec web python manage.py check

# 4. Cargar capas territoriales y datos de prueba (requiere al menos 1 usuario)
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py poblar_lotes_demo
```

### Opción B: VS Code Dev Container
1. Abrir la carpeta raíz en VS Code -> **"Reopen in Container"**.
2. El servidor de desarrollo inicia automáticamente en `http://localhost:8000`.
3. Para depuración paso a paso con *breakpoints*, presionar **`F5`** (*"Django: debug (puerto 8001)"*), que levanta una instancia dedicada en `http://localhost:8001`.
4. En la terminal integrada del contenedor (`/workspace/iagrocorr_project`):
   ```bash
   python manage.py check
   python manage.py test
   ```

### Opción C: Entorno Local en Windows + PostGIS en Docker
```powershell
# 1. Asegurar que el contenedor de PostGIS esté corriendo en el puerto 5433
docker compose up -d db

# 2. Activar entorno virtual en la raíz y validar Django
.\venv\Scripts\Activate.ps1
cd iagrocorr_project
python manage.py check
python manage.py test
```

---

## 2. Ejecución de Pruebas Automatizadas (Django / GeoDjango)

### Comandos de Ejecución
- **Con Docker Compose:**
  ```powershell
  docker compose exec web python manage.py test
  ```
- **Por aplicación específica:**
  ```powershell
  docker compose exec web python manage.py test accounts
  docker compose exec web python manage.py test monitoring
  ```
- **Manteniendo la base de datos de test entre corridas (acelera pruebas con PostGIS):**
  ```powershell
  docker compose exec web python manage.py test --keepdb
  ```

> **Nota Importante sobre Permisos en PostGIS:**  
> Al correr `manage.py test`, GeoDjango crea una base temporal `test_iagrocorr` e instala automáticamente la extensión `postgis`. El usuario `admin_iagrocorr` creado por el contenedor oficial `postgis/postgis:16-3.4` cuenta con privilegios de superusuario de PostgreSQL, por lo que la creación de `test_iagrocorr` funciona de forma directa sin configuraciones extra.

---

## 3. Checklist de Validación Funcional y Geoespacial (QA Manual)

Antes de fusionar un Pull Request hacia `main`, verificar los siguientes casos según el área modificada:

### A. Autenticación y Sesiones (`accounts`)
- [ ] **Registro (`/register/`):** Bloquea nombres de usuario o correos duplicados conservando los datos ingresados en el formulario; exige contraseña segura según validadores de Django.
- [ ] **Login (`/login/`):** Permite ingreso mediante correo electrónico; verifica diferencia entre sesión efímera y casilla *"Mantener sesión"* (2 semanas).
- [ ] **Control de acceso:** Un usuario no autenticado que intenta abrir `/dashboard/`, `/global-twins/` o `/monitoring/api/*` es redirigido a `/login/`.

### B. Validación Territorial y ABM de Lotes (`monitoring` + Leaflet-Geoman)
- [ ] **Bloqueo de Ejidos Urbanos (Caso Negativo):** En `/dashboard/#lotes`, activar *"Añadir Lote en Mapa"* y dibujar un polígono que pise total o parcialmente una zona roja punteada (ej. *Ejido Urbano Corrientes Capital* o *Mercedes*). La API debe responder `HTTP 400` con el mensaje de **Restricción de Ordenamiento Territorial** y no persistir el polígono.
- [ ] **Alta de Lote Rural Válido (Caso Positivo):** Dibujar un polígono fuera de ejidos urbanos, asignarle nombre y cultivo. Verificar:
  1. Cálculo coherente de `superficie_ha` en hectáreas.
  2. Aparición inmediata en el mapa y en la tabla *"Mis lotes"* sin recargar toda la página.
  3. Clasificación automática del semáforo (`VERDE`, `AMARILLO` o `ROJO`) y creación de su registro en `HechoMedicionAmbiental`.
- [ ] **Eliminación Real y Aislamiento:** Eliminar un lote desde el botón de la tabla o el popup del mapa -> confirmar que desaparece de PostGIS (`Lote` y su `historial_dw` en cascada). Verificar que un usuario `A` no pueda borrar un lote perteneciente a un usuario `B` (`HTTP 404`).

### C. Motor de Reglas Espaciales y Bandas SENASA (`rules_engine.py`)
Con los datos cargados por `poblar_lotes_demo`, comprobar los tres escenarios testigos:
- [ ] **Escenario Óptimo / Precaución Moderada (Mercedes - Arroz):** Insumo Clase IV (Banda Verde), NDVI alto (`0.78`) -> evaluar distancia a Iberá y ríos.
- [ ] **Escenario de Infracción Hídrica/Periurbana con Banda Roja (Goya - Tabaco):** Aplicación reciente de Clase IA (Clorpirifos) próxima a curso hídrico -> debe disparar alerta crítica y `semaforo = ROJO` (`score_riesgo >= 90`).
- [ ] **Escenario de Estrés Vegetativo / Déficit Hídrico (Virasoro - Forestal):** Humedad `< 15%` (`11%`) y NDVI `< 0.40` (`0.38`) -> debe disparar alerta de **Estrés Vegetativo Severo** y `semaforo = ROJO`.

### D. Visores Cartográficos, UI Responsive y Modo Oscuro
- [ ] **Zoom Satelital Profundo:** En el mapa de lotes y en `/global-twins/`, acercar el zoom hasta el nivel máximo (`18`–`19`) en modo satélite y comprobar que la imagen se reescala nítidamente **sin mostrar carteles grises de *"Map data not yet available"***.
- [ ] **Capas WMS de INTA:** En *Datos ambientales*, alternar fondos (*Satélite* / *Político*) y superponer *CO2 (INTA)* y *Suelos (INTA)* verificando la carga de teselas desde GeoServer INTA y el botón *Limpiar*.
- [ ] **Cambio de Vistas sin Mapas Cortados:** Alternar entre *Panel de control*, *Lotes y parcelas* y *Datos ambientales*; los mapas deben ocupar el 100% de su contenedor gracias a `ResizeObserver` / `invalidateSize()`.
- [ ] **Modo Claro / Oscuro y Móvil:** Alternar el tema en Landing (`/`), Dashboard (`/dashboard/`) y Gemelos Globales (`/global-twins/`), recargar con `F5` (sin parpadeo blanco inicial) y probar la vista móvil (`< 992px`) con apertura/cierre automático del menú lateral `offcanvas`.

---

## 4. Plan de Cobertura para Pruebas Unitarias (Próxima Iteración)

Actualmente `accounts/tests.py` contiene la plantilla base y `monitoring/` aún no posee suite automatizada. Al implementar los primeros tests automatizados, priorizar:

1. **`monitoring/tests/test_models_spatial.py`:**
   - Test de `Lote.clean()` rechazando intersección con `ZonaUrbana`.
   - Test de restricción `unique_medicion_lote_fecha` en `HechoMedicionAmbiental`.
2. **`monitoring/tests/test_rules_engine.py`:**
   - Tests unitarios determinísticos para las 4 reglas de `evaluar_riesgo_lote()` (amortiguamiento Iberá, deriva hídrica, buffer periurbano y estrés NDVI/humedad).
3. **`monitoring/tests/test_api_views.py`:**
   - Test de `POST /monitoring/api/crear-lote/` (200 en zona rural vs. 400 en zona urbana).
   - Test de permisos en `POST /monitoring/api/eliminar-lote/<id>/` entre distintos productores vs. `superuser`.
4. **`accounts/tests.py`:**
   - Tests de flujo de registro, login por correo electrónico y redirección de rutas protegidas.
