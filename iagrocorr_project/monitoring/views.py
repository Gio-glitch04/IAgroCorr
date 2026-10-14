import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from .models import Lote, ZonaUrbana, NivelRiesgo, GemeloGlobal, AreaProtegida, CuerpoDeAgua
from .rules_engine import evaluar_riesgo_lote


@login_required
def lotes_geojson(request):
    """
    Retorna los lotes del usuario en formato GeoJSON para Leaflet,
    enriquecidos con las métricas espaciales y el semáforo del DW.
    """
    if request.user.is_superuser:
        lotes = Lote.objects.filter(activo=True)
    else:
        lotes = Lote.objects.filter(productor=request.user, activo=True)
    features = []
    for l in lotes:
        ultima_med = l.historial_dw.order_by('-fecha_captura').first()
        dist_reserva = ultima_med.distancia_reserva_metros if ultima_med else None
        dist_agua = ultima_med.distancia_agua_metros if ultima_med else None
        score = 10
        alertas = []
        if ultima_med and isinstance(ultima_med.observaciones_json, dict):
            score = ultima_med.observaciones_json.get('score_riesgo', 10)
            alertas = ultima_med.observaciones_json.get('diagnostico', {}).get('alertas_criticas', [])

        features.append({
            "type": "Feature",
            "properties": {
                "id": l.id,
                "nombre": l.nombre,
                "cultivo": l.cultivo_actual,
                "riesgo": l.riesgo_actual,
                "superficie_ha": str(l.superficie_ha) if l.superficie_ha else None,
                "distancia_reserva_m": dist_reserva,
                "distancia_agua_m": dist_agua,
                "score_riesgo": score,
                "alertas": alertas
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

        # 4. EJECUCIÓN INMEDIATA DEL MOTOR DE REGLAS ESPACIALES POSTGIS
        eval_resultado = evaluar_riesgo_lote(nuevo_lote, actualizar_dw=True)

        return JsonResponse({
            "ok": True,
            "mensaje": f"¡Lote '{nuevo_lote.nombre}' guardado y clasificado como '{eval_resultado['semaforo']}' por el motor de reglas!",
            "lote": {
                "id": nuevo_lote.id,
                "nombre": nuevo_lote.nombre,
                "cultivo": nuevo_lote.cultivo_actual,
                "superficie_ha": str(nuevo_lote.superficie_ha) if nuevo_lote.superficie_ha else "0.0",
                "riesgo": eval_resultado["semaforo"],
                "score_riesgo": eval_resultado["score_riesgo"],
                "geometry": json.loads(nuevo_lote.geom.geojson),
                "evaluacion": eval_resultado
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Formato JSON inválido."}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Error interno: {str(e)}"}, status=500)


@login_required
def capas_ambientales_geojson(request):
    """
    Retorna la cartografía ambiental protegida en GeoJSON:
    - Reserva Natural Esteros del Iberá (Área Protegida)
    - Cursos de Agua y Red Fluvial (Ríos Paraná, Uruguay, Corriente, Santa Lucía, etc.)
    """
    features = []

    # Áreas Protegidas (Esteros del Iberá)
    reservas = AreaProtegida.objects.filter(activo=True)
    for r in reservas:
        features.append({
            "type": "Feature",
            "properties": {
                "id": r.id,
                "nombre": r.nombre,
                "categoria": r.categoria,
                "tipo_capa": "area_protegida",
                "buffer_m": r.buffer_amortiguamiento_metros,
            },
            "geometry": json.loads(r.geom.geojson)
        })

    # Cuerpos de Agua y Ríos
    aguas = CuerpoDeAgua.objects.filter(activo=True)
    for a in aguas:
        features.append({
            "type": "Feature",
            "properties": {
                "id": a.id,
                "nombre": a.nombre,
                "tipo": a.tipo,
                "tipo_capa": "cuerpo_agua",
                "buffer_m": a.buffer_seguridad_metros,
            },
            "geometry": json.loads(a.geom.geojson)
        })

    return JsonResponse({
        "type": "FeatureCollection",
        "features": features
    })


@login_required
def evaluar_lote_api(request, lote_id):
    """
    Ejecuta el motor de reglas espaciales en tiempo real para un lote específico
    y retorna el diagnóstico en formato JSON con distancias e infracciones.
    """
    if request.user.is_superuser:
        lote = get_object_or_404(Lote, id=lote_id, activo=True)
    else:
        lote = get_object_or_404(Lote, id=lote_id, productor=request.user, activo=True)

    resultado = evaluar_riesgo_lote(lote, actualizar_dw=True)
    return JsonResponse({
        "ok": True,
        "evaluacion": resultado
    })


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

