import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Lote

# Placeholder para endpoints de GeoJSON o vistas de monitoreo
@login_required
def lotes_geojson(request):
    """
    Retorna los lotes del usuario en formato JSON para Leaflet
    """
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
            # geom.geojson genera string GeoJSON, cargado de forma segura con json.loads
            "geometry": json.loads(l.geom.geojson)
        })
    return JsonResponse({
        "type": "FeatureCollection",
        "features": features
    })
