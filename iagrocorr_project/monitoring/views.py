import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from .models import Lote, ZonaUrbana, NivelRiesgo, GemeloGlobal


@login_required
def lotes_geojson(request):
    """
    Retorna los lotes del usuario en formato GeoJSON para Leaflet
    """
    if request.user.is_superuser:
        lotes = Lote.objects.filter(activo=True)
    else:
        lotes = Lote.objects.filter(productor=request.user, activo=True)
    features = []
    for l in lotes:
        features.append({
            "type": "Feature",
            "properties": {
                "id": l.id,
                "nombre": l.nombre,
                "cultivo": l.cultivo_actual,
                "riesgo": l.riesgo_actual,
                "superficie_ha": str(l.superficie_ha) if l.superficie_ha else None
            },
            "geometry": json.loads(l.geom.geojson)
        })
    return JsonResponse({
        "type": "FeatureCollection",
        "features": features
    })


@login_required
def zonas_urbanas_geojson(request):
    """
    Retorna las zonas urbanas de exclusión en formato GeoJSON para visualizarlas en Leaflet
    """
    zonas = ZonaUrbana.objects.all()
    features = []
    for z in zonas:
        features.append({
            "type": "Feature",
            "properties": {
                "id": z.id,
                "nombre": z.nombre,
                "departamento": z.departamento,
                "buffer_m": z.radio_buffer_metros
            },
            "geometry": json.loads(z.geom.geojson)
        })
    return JsonResponse({
        "type": "FeatureCollection",
        "features": features
    })


@login_required
@require_POST
def crear_lote_api(request):
    """
    Recibe un polígono dibujado por el usuario, valida que NO intersecte con
    zonas urbanas, calcula automáticamente las hectáreas y lo persiste en PostGIS.
    """
    try:
        body = json.loads(request.body.decode('utf-8'))
        nombre = body.get('nombre', '').strip()
        cultivo = body.get('cultivo', '').strip()
        geometry_data = body.get('geometry')

        if not nombre:
            return JsonResponse({"ok": False, "error": "El nombre del lote es obligatorio."}, status=400)

        if not geometry_data:
            return JsonResponse({"ok": False, "error": "No se recibió la geometría del polígono."}, status=400)

        # Convertir GeoJSON a objeto espacial GEOSGeometry
        geos_geom = GEOSGeometry(json.dumps(geometry_data))
        if geos_geom.geom_type == 'Polygon':
            multi_geom = MultiPolygon(geos_geom)
        elif geos_geom.geom_type == 'MultiPolygon':
            multi_geom = geos_geom
        else:
            return JsonResponse({"ok": False, "error": "Geometría inválida. Debe ser un polígono."}, status=400)

        # Asignar SRID WGS84
        multi_geom.srid = 4326

        # 1. VALIDACIÓN ESPACIAL EN POSTGIS: ¿Intersecta con zonas urbanas de exclusión?
        zonas_conflicto = ZonaUrbana.objects.filter(geom__intersects=multi_geom)
        if zonas_conflicto.exists():
            nombres = ", ".join([z.nombre for z in zonas_conflicto])
            return JsonResponse({
                "ok": False,
                "error": f"Restricción de Ordenamiento Territorial: El lote intersecta con '{nombres}'. Está prohibido registrar lotes agrícolas dentro de ejidos urbanos."
            }, status=400)

        # 2. CÁLCULO DE HECTÁREAS en PostGIS (Proyección métrica EPSG 3857)
        try:
            area_m2 = multi_geom.transform(3857, clone=True).area
            superficie_ha = round(area_m2 / 10000.0, 2)
        except Exception:
            superficie_ha = None

        # 3. Guardar el lote asignado al usuario activo
        nuevo_lote = Lote.objects.create(
            productor=request.user,
            nombre=nombre,
            cultivo_actual=cultivo or None,
            superficie_ha=superficie_ha,
            geom=multi_geom,
            riesgo_actual=NivelRiesgo.VERDE,
            activo=True
        )

        return JsonResponse({
            "ok": True,
            "mensaje": f"¡Lote '{nuevo_lote.nombre}' guardado exitosamente!",
            "lote": {
                "id": nuevo_lote.id,
                "nombre": nuevo_lote.nombre,
                "cultivo": nuevo_lote.cultivo_actual,
                "superficie_ha": str(nuevo_lote.superficie_ha) if nuevo_lote.superficie_ha else "0.0",
                "riesgo": nuevo_lote.riesgo_actual,
                "geometry": json.loads(nuevo_lote.geom.geojson)
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Formato JSON inválido."}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Error interno: {str(e)}"}, status=500)


@login_required
def gemelos_globales_api(request):
    """
    Retorna la lista de gemelos globales ordenados por similitud y orden
    con sus coordenadas PostGIS WGS84 y firmas agroclimáticas.
    """
    gemelos = GemeloGlobal.objects.filter(activo=True).order_by('orden', '-similitud_pct')
    data = []
    for g in gemelos:
        data.append({
            "id": g.id,
            "nombre": g.nombre,
            "pais": g.pais,
            "lat": g.geom.y,
            "lng": g.geom.x,
            "sim": g.similitud_pct,
            "hum": g.humedad_anual_pct,
            "ndviMin": g.ndvi_min,
            "ndviMax": g.ndvi_max,
            "ndviText": g.ndvi_rango_texto,
            "ndviVal": g.ndvi_val_pct,
            "cultivos": g.cultivos_principales,
            "descripcion": g.descripcion_climatica,
        })
    return JsonResponse(data, safe=False)
