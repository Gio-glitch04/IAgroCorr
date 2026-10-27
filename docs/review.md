# Registro de Revisión, Hitos y Auditoría Técnica — IAgroCorr (`review.md`)

Documento de seguimiento evolutivo de **IAgroCorr**, donde se audita el grado de avance respecto a los objetivos comprometidos ante la cátedra (**Anexo II — PFC FACENA UNNE**), los hitos integrados por el equipo en GitHub y las observaciones técnicas o deuda técnica pendiente.

---

## 1. Trazabilidad de Cumplimiento — Objetivos Oficiales (Anexo II)

| Nº | Objetivo Específico (Anexo II) | Grado de Avance | Evidencia en el Repositorio | Próximo Hito de Cierre |
| :-: | :--- | :---: | :--- | :--- |
| **OE1** | Profundizar conocimientos en análisis geoespacial con IA (**GeoIA**). | **En progreso continuo** | Modelado topológico en PostGIS (`SRID 4326` / `3857`), índices espaciales GiST, reglas espaciales y diseño de arquitectura GeoIA. | Documentar experimentación y métricas de validación CRISP-DM de los algoritmos entrenados. |
| **OE2** | Diseñar un **Data Warehouse geoespacial** (IDERA, IDECorr, INTA, GEE). | **Avanzado (75%)** | Esquema estrella/dimensional en `monitoring/models.py` (`HechoMedicionAmbiental` + dimensiones espaciales) y conexión WMS en vivo con GeoServer INTA. | Automatizar el pipeline ETL con la API de Google Earth Engine y capas vectoriales completas de IDECorr/IDERA. |
| **OE3** | Desarrollar **aplicación web** portable, de alta disponibilidad y alto rendimiento (móvil/escritorio). | **Completado / Consolidado (90%)** | Stack Dockerizado (`Dockerfile` + `docker-compose.yml`), Dev Container, soporte Windows/Linux, UI responsive móvil/escritorio, modo oscuro y dominios Cloudflare. | Ajustar configuración productiva (`gunicorn` / `whitenoise` o `nginx` y `DEBUG=False`) para despliegue final. |
| **OE4** | Modelos de ML para **detección de anomalías** en índices de vegetación con salida en **formato semáforo**. | **Parcial (55%)** | Semáforo operativo en tiempo real (`rules_engine.py`) cruzando buffers ambientales, SENASA, NDVI y humedad; UI de Semáforo lista. | Entrenar e integrar el modelo **Isolation Forest** (`scikit-learn`) sobre series temporales de NDVI/NDWI reales. |
| **OE5** | Motor de recomendación de cultivos por **similitud (*clustering*)** con zonas globales (**Gemelos Climáticos**). | **Parcial (50%)** | Modelo `GemeloGlobal` en PostGIS, API `/monitoring/api/gemelos-globales/` y vista interactiva `/global-twins/` rediseñada con 5 regiones base. | Implementar el algoritmo de *clustering* edafoclimático que empareje dinámicamente cada lote con su gemelo óptimo y sugiera cultivos de rotación. |
| **OE6** | Módulo de **visualización interactiva (Dashboard)** para la toma de decisiones del productor. | **Avanzado (85%)** | Panel de control con KPIs reales, visor de gestión *Lotes y parcelas* con dibujo y baja real, capas ambientales PostGIS + WMS INTA. | Conectar las pestañas *Estadísticas*, *Rendimiento Técnico* y *Reportes* a consultas históricas reales del DW. |

---

## 2. Historial Consolidado de Hitos Recientes (Octubre 2026)

| Fecha | PR / Referencia | Autor(es) | Resumen Técnico del Avance |
| :--- | :--- | :--- | :--- |
| **2026-10-14** | `97d9f5d` / `64a6ff0` / `d6cd21d` (PR #2) | Julio César Pintos | Creación de la app geoespacial `monitoring`: modelos PostGIS (`Lote`, `ZonaUrbana`, `AreaProtegida`, `CuerpoDeAgua`, `AplicacionInsumo`, `HechoMedicionAmbiental`, `GemeloGlobal`), validación anti-urbana, dibujo interactivo en Dashboard y **Motor de Reglas Espaciales (`rules_engine.py`)** para Iberá, ríos y bandas SENASA. |
| **2026-10-15** | `0550c71` (PR #3) | Julio César Pintos | Incorporación de `requirements.txt` con soporte de wheels GDAL para Windows, `GUIA_INSTALACION.md` detallada y renovación inicial de `README.md`. |
| **2026-10-21** | `42b456c` / `d29d799` | Giovanni Oscar Piazza | Mejora de autodetección dinámica de librerías `GDAL` / `GEOS` (`osgeo`) en `settings.py` para cualquier entorno de Python en Windows y limpieza de `.gitignore`. |
| **2026-10-21 a 22** | PR #5, #6, #7, #8 | Giovanni Oscar Piazza | **Dockerización completa** de la plataforma (Django + PostGIS) y configuración integral de **VS Code Dev Container** con recarga automática, acceso al CLI oficial de Docker y depuración en puerto `8001`. |
| **2026-10-25** | PR #11, #12, #13 | Giovanni Oscar Piazza | Rediseño estilístico de barra lateral colapsable y vista **Gemelos Globales**, corrección de botones de login/registro, implementación de **Modo Oscuro sin parpadeo** en toda la app y navegación *responsive* móvil. |
| **2026-10-26** | PR #14, #15 | Giovanni Oscar Piazza | Nueva vista dedicada **Lotes y parcelas** (`/dashboard/#lotes`), endpoint y flujo de **eliminación real de lotes** en PostGIS, y solución al límite de zoom satelital (`maxNativeZoom: 17`) en mapas Esri. |
| **2026-10-27** | PR #16 (`331392c`) | Giovanni Oscar Piazza | **Rediseño integral de la Landing Page** (`demo.html` + `landing.css`) con identidad visual unificada, vista previa de Gemelos Globales y hoja de ruta del proyecto. |

---

## 3. Auditoría de Deuda Técnica y Puntos de Revisión

Puntos detectados en el código actual para abordar ordenadamente en próximos Sprints:

1. **Unificación o sincronización de `requirements.txt`:**
   - Existen dos archivos idénticos: `requirements.txt` (raíz) e `iagrocorr_project/requirements.txt`. Conviene mantener uno solo en la raíz (o hacer que el interno referencie `-r ../requirements.txt`) para evitar divergencias cuando se instalen `scikit-learn`, `pandas` y `earthengine-api`.
2. **Alineación menor de versiones Python/Django entre documentación y entorno:**
   - `Dockerfile` utiliza `python:3.13-slim` mientras la guía local Windows sugiere `Python 3.12` (por compatibilidad del wheel `GDAL 3.13.3` en `gisidx`). Mantener documentada esta dualidad para evitar errores al instalar en Windows nativo.
3. **Formulario UI para `AplicacionInsumo`:**
   - El motor `rules_engine.py` ya evalúa las aplicaciones de los últimos 30 días, pero los productores aún no tienen un modal/formulario en *Lotes y parcelas* para cargar una pulverización o fertilización desde el panel web (actualmente se cargan por comando demo o desde `/admin/`).
4. **Transición de vistas prototipo (*Mago de Oz*) a datos dinámicos:**
   - Reemplazar progresivamente los indicadores estáticos en las pestañas *Datos ambientales* (tarjetas superiores), *Semáforo de impacto* y *Estadísticas* por consultas agregadas sobre `HechoMedicionAmbiental` y salidas de los modelos ML.
5. **Archivos heredados de primeras iteraciones:**
   - `index.html` (en la raíz), `sql/CREATE TABLE usuarios.sql` e `iagrocorr_project/backup_iagrocorr.sql` corresponden a etapas previas a la contenedorización con migraciones de GeoDjango. Evaluar junto al equipo si se archivan o eliminan antes de la entrega final del PFC.
6. **Endurecimiento para despliegue en producción:**
   - Cuando se publique detrás de Cloudflare en el servidor definitivo, asegurar que `.env` defina un `DJANGO_SECRET_KEY` robusto, `DJANGO_DEBUG=False`, contraseña segura de PostgreSQL y servidor WSGI de producción (`gunicorn`).
