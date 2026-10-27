# Memoria Activa del Proyecto — IAgroCorr (`memory.md`)

> **Última actualización:** 27 de octubre de 2026  
> **Rama principal:** `main` (sincronizada con `origin/main` en el merge del PR #16)  
> **Estado general:** Prototipo funcional avanzado (**Beta abierta**) con infraestructura Docker/PostGIS completa, motor de reglas espaciales activo y UX/UI renovada.

---

## 1. Resumen de las Últimas Actualizaciones del Equipo

### Infraestructura, Entorno y DevOps
- **Dockerización integral (`Dockerfile` + `docker-compose.yml` + `.env.example`):** La aplicación Django (`iagrocorr_web`) y la base de datos (`iagrocorr_db_postgis`, PostgreSQL 16 + PostGIS 3.4) levantan juntas con `docker compose up -d --build`, aplicando migraciones automáticamente y montando `./iagrocorr_project:/app` para recarga en vivo.
- **VS Code Dev Container (`.devcontainer/` + `.vscode/launch.json`):** Configurado con la raíz del repositorio en `/workspace`, inicio automático de Django en el puerto `8000`, CLI oficial de Docker (`docker-outside-of-docker` con `moby: false`) y perfil de depuración con *breakpoints* (`F5`) sobre una instancia independiente en el puerto `8001`.
- **Autodetección robusta de GDAL/GEOS en Windows (`settings.py`):** Búsqueda automática de `osgeo` (`gdal*.dll`, `geos_c.dll`, `PROJ_LIB`, `GDAL_DATA`) tanto en entornos virtuales (`venv`) como en instalaciones globales o de usuario, eliminando configuraciones manuales en el `PATH` de Windows.

### Backend Geoespacial, Data Warehouse y Motor de Reglas
- **Esquema espacial completo en `monitoring`:** Tablas `ZonaUrbana`, `AreaProtegida` (Esteros del Iberá), `CuerpoDeAgua` (Ríos Paraná, Uruguay, Corriente, Santa Lucía, Riacho Goya, Laguna Iberá), `Lote`, `AplicacionInsumo` (bandas SENASA), `HechoMedicionAmbiental` (DW) y `GemeloGlobal`.
- **Motor de reglas espaciales en tiempo real (`monitoring/rules_engine.py`):** Evalúa distancias proyectadas en `EPSG:3857` contra buffers normativos de Iberá, cursos de agua y zonas periurbanas + aplicaciones fitosanitarias recientes (30 días) + NDVI/humedad del DW, persistiendo el semáforo (`VERDE`, `AMARILLO`, `ROJO`) y el diagnóstico JSON.
- **ABM real de lotes vía API (`monitoring/views.py`):** Alta interactiva con validación anti-ejido urbano y cálculo automático de hectáreas (`POST /monitoring/api/crear-lote/`) + **eliminación real en cascada** (`POST /monitoring/api/eliminar-lote/<lote_id>/`) restringida al propietario del lote o superusuario.
- **Semilla de datos reproducible:** Comando `python manage.py poblar_lotes_demo` listo para inicializar todas las capas territoriales, 3 lotes testigos (Mercedes, Goya, Virasoro), insumos SENASA, mediciones DW y 5 Gemelos Globales.

### Frontend, Mapas y Experiencia de Usuario (UX/UI)
- **Rediseño visual de la Landing Page (`demo.html` + `static/css/landing.css`):** Nueva portada institucional *"Beta abierta"*, tarjeta de vista previa de Gemelos Globales, secciones de Funcionalidades, Tecnología/Fuentes de datos y Hoja de ruta alineada con CRISP-DM.
- **Modo Oscuro y Diseño Responsive (`theme_init.html`, `theme_toggle_script.html`, `styles2.css`):** Conmutador claro/oscuro persistido en `localStorage` (`iagrocorr-tema`) sin parpadeo al cargar, barra superior adaptable y menú lateral `offcanvas` en pantallas móviles.
- **Barra lateral colapsable y rediseño de `global-twins.html`:** El estado expandido/contraído del menú lateral se recuerda en `localStorage` (`iagrocorr-barra-lateral`).
- **Nueva vista dedicada "Lotes y parcelas" en `dashboard.html`:** Separa el mapa informativo del Panel de Control respecto del mapa de gestión (`mapaGestionLotes`), incorporando tabla interactiva *"Mis lotes"*, soporte de enlaces directos (`/dashboard/#lotes` y `/dashboard/#lotes-dibujar`) y borrado de parcelas desde tabla o popup.
- **Corrección de zoom satelital profundo:** Configurado `maxNativeZoom: 17` y `maxZoom: 19` en `Esri World Imagery` tanto en Dashboard como en Gemelos Globales para evitar el mensaje *"Map data not yet available"* al acercarse a nivel de parcela.

---

## 2. Matriz de Estado Actual: Operativo vs. Maqueta (*Mago de Oz*) / Pendiente

Para evitar confusiones durante los próximos Sprints, este cuadro distingue qué partes ya consumen datos reales de PostGIS y cuáles son maquetas visuales listas para conectarse con los pipelines de datos e IA:

| Módulo / Funcionalidad | Estado Actual | Detalle Técnico |
| :--- | :---: | :--- |
| **Autenticación, Registro y Perfiles** | **Operativo (Real)** | Login por email, validación de contraseña, *"Mantener sesión"* y vistas protegidas. |
| **Landing Page Pública (`/`)** | **Operativo (Real)** | Rediseñada, responsive y con soporte completo de modo claro/oscuro. |
| **Panel de Control: KPIs, Mapa y Actividad** | **Operativo (Real)** | Hectáreas, alertas, promedios NDVI/Humedad, capas PostGIS y últimos hechos leídos del DW. |
| **Gestión de Lotes (`/dashboard/#lotes`)** | **Operativo (Real)** | Dibujo con Leaflet-Geoman, bloqueo urbano PostGIS, área en Ha, semáforo inicial y borrado real. |
| **Matriz de Gemelos Globales (`/global-twins/`)** | **Parcial (BD Real / ML Pendiente)** | Consulta puntos y métricas reales desde `GemeloGlobal` en PostGIS; falta automatizar el *clustering* dinámico por lote. |
| **Motor de Reglas Normativas (Iberá / Ríos / SENASA)** | **Operativo (Real)** | Distancias topológicas PostGIS + bandas SENASA + persistencia en `HechoMedicionAmbiental`. |
| **Visor de Capas WMS INTA (*Datos Ambientales*)** | **Parcial (WMS Real / KPIs Fijos)** | Las capas WMS de Suelos y COS se consumen en vivo de GeoServer INTA; las 4 tarjetas superiores de esa pestaña aún tienen valores fijos de referencia (`68%`, `412 ppm`, `0.75`, `26.5 °C`). |
| **Vista *Semáforo de Triple Impacto*** | **Maqueta (*Mago de Oz*)** | Tarjetas demostrativas (Isolation Forest `5.2%` anomalías, Proyección INTA, Huella Ambiental) listas para vincular a datos reales. |
| **Vista *Estadísticas* / *Reportes* / *Rendimiento Técnico*** | **Maqueta / En construcción** | Estructura UI/UX presentada en el panel; pendiente conexión a series históricas del DW y exportación PDF/CSV. |
| **Pipeline ETL Google Earth Engine (GEE) & IDECorr** | **Pendiente (Próxima Etapa)** | El modelo `HechoMedicionAmbiental` ya está preparado; falta el conector automatizado con la API Python de GEE (`earthengine-api`) e ingesta masiva de shapefiles/WFS oficiales de IDECorr. |
| **Modelos ML (`Isolation Forest` + `Clustering`)** | **Pendiente (Etapa CRISP-DM)** | Definidos en el Anexo II (`pandas` + `scikit-learn`); aún no añadidos a `requirements.txt` ni entrenados en un módulo de inferencia. |

---

## 3. Decisiones Técnicas Activas que Deben Respetarse

1. **Puerto de Base de Datos:**
   - Desde **Windows local**: `localhost:5433`.
   - Desde el contenedor **`web` / Dev Container**: `db:5432` (inyectado por `docker-compose.yml`).
2. **Sincronización de `requirements.txt`:**
   - Existen dos copias (`C:\IAgroCorr\requirements.txt` en la raíz y `C:\IAgroCorr\iagrocorr_project\requirements.txt`). El `Dockerfile` consume el de la raíz; **mantener ambos sincronizados** (o unificar referencia) cuando se agreguen librerías como `scikit-learn`, `pandas` o `earthengine-api`.
3. **Claves de `localStorage` en el Frontend:**
   - `iagrocorr-tema`: `"light"` | `"dark"`.
   - `iagrocorr-barra-lateral`: `"expandida"` | `"contraida"`.
4. **Ramas Git:**
   - `main` es la rama estable e integra todas las funcionalidades actuales; trabajar cambios nuevos en ramas descriptivas (`feature/...`, `fix/...`, `docs/...`).

---

## 4. Próximos Pasos Prioritarios (Backlog Sugerido)

1. **Etapa 1 Hoja de Ruta — Pipeline ETL Real (IDECorr / IDERA / GEE):**
   - Incorporar scripts/comandos de gestión en `monitoring/management/commands/` para importar polígonos oficiales de **IDECorr / IDERA** (reemplazando las geometrías simplificadas de demostración) y consultar series reales de NDVI/NDWI y humedad en **Google Earth Engine**.
2. **Carga de Aplicaciones de Insumos desde la UI:**
   - Permitir al productor registrar eventos de `AplicacionInsumo` (fecha, ingrediente activo, dosis, banda SENASA) desde la vista de lotes para disparar el recalculo del semáforo sin depender del panel `/admin/`.
3. **Etapa 3 Hoja de Ruta — Motor de Machine Learning (CRISP-DM):**
   - Añadir `pandas` y `scikit-learn` al entorno.
   - Implementar el detector de anomalías vegetativas con **Isolation Forest** sobre el historial de `HechoMedicionAmbiental` y conectarlo a la vista *Semáforo de Impacto*.
   - Implementar el algoritmo de **Clustering** edafoclimático para calcular dinámicamente la similitud entre un lote específico del productor y los `GemeloGlobal`.
4. **Calidad y Automatización de Tests:**
   - Implementar la suite inicial de pruebas automatizadas en `monitoring/` y `accounts/` siguiendo `docs/testing.md`.
