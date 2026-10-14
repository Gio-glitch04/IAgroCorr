import json
from datetime import date, timedelta
from django.contrib.gis.db.models.functions import Distance, Transform
from .models import (
    Lote,
    AreaProtegida,
    CuerpoDeAgua,
    ZonaUrbana,
    AplicacionInsumo,
    HechoMedicionAmbiental,
    NivelRiesgo,
    BandaToxicologica,
)


def evaluar_riesgo_lote(lote, fecha_evaluacion=None, actualizar_dw=True):
    """
    Motor de Reglas Espaciales en Tiempo Real para IAgroCorr.
    Evalúa distancias topológicas PostGIS (Esteros del Iberá, Cursos de Agua, Zonas Urbanas),
    bandas toxicológicas SENASA (Clases Ia, Ib, II, III, IV) e índices satelitales (NDVI/Humedad).

    Retorna un diccionario estructurado con:
    - semaforo: VERDE | AMARILLO | ROJO
    - score_riesgo: Escala 0 a 100
    - metricas_espaciales: Distancias en metros
    - alertas: Infracciones críticas
    - advertencias: Puntos de atención
    - conformidades: Parámetros dentro de norma
    """
    if fecha_evaluacion is None:
        fecha_evaluacion = date.today()

    lote_3857 = lote.geom.transform(3857, clone=True)

    # 1. CÁLCULO DE DISTANCIAS ESPACIALES EN POSTGIS (Proyección métrica EPSG:3857)
    # A) Distancia a Reserva Natural / Parque Esteros del Iberá
    reserva_cercana = AreaProtegida.objects.filter(activo=True).annotate(
        d=Distance(Transform('geom', 3857), lote_3857)
    ).order_by('d').first()
    dist_reserva_m = round(reserva_cercana.d.m, 1) if reserva_cercana else None
    nombre_reserva = reserva_cercana.nombre if reserva_cercana else "No identificada"

    # B) Distancia a Cursos de Agua (Ríos Paraná, Uruguay, Corriente, Santa Lucía, etc.)
    agua_cercana = CuerpoDeAgua.objects.filter(activo=True).annotate(
        d=Distance(Transform('geom', 3857), lote_3857)
    ).order_by('d').first()
    dist_agua_m = round(agua_cercana.d.m, 1) if agua_cercana else None
    nombre_agua = f"{agua_cercana.nombre} ({agua_cercana.tipo})" if agua_cercana else "No identificado"

    # C) Distancia a Zonas Urbanas de Exclusión
    urbana_cercana = ZonaUrbana.objects.annotate(
        d=Distance(Transform('geom', 3857), lote_3857)
    ).order_by('d').first()
    dist_urbana_m = round(urbana_cercana.d.m, 1) if urbana_cercana else None
    nombre_urbana = urbana_cercana.nombre if urbana_cercana else "No identificada"

    # 2. EVALUACIÓN DE FITOSANITARIOS Y BANDAS SENASA (Últimos 30 días)
    limite_fecha_aplicacion = fecha_evaluacion - timedelta(days=30)
    aplicaciones = lote.aplicaciones.filter(fecha_aplicacion__gte=limite_fecha_aplicacion).order_by('-fecha_aplicacion')

    tiene_banda_roja = False
    tiene_banda_amarilla = False
    tiene_banda_azul_verde = False
    resumen_aplicaciones = []

    for app in aplicaciones:
        resumen_aplicaciones.append({
            "ingrediente": app.ingrediente_activo,
            "dosis": f"{app.dosis_ha} {app.unidad_medida}",
            "banda": app.banda_toxicologica,
            "fecha": str(app.fecha_aplicacion)
        })
        if app.banda_toxicologica in [BandaToxicologica.CLASE_IA, BandaToxicologica.CLASE_IB]:
            tiene_banda_roja = True
        elif app.banda_toxicologica == BandaToxicologica.CLASE_II:
            tiene_banda_amarilla = True
        else:
            tiene_banda_azul_verde = True

    # 3. DATOS AGROCLIMÁTICOS Y SATELITALES DEL DW
    ultima_medicion = lote.historial_dw.order_by('-fecha_captura').first()
    ndvi_promedio = ultima_medicion.ndvi_promedio if ultima_medicion else None
    humedad_suelo_pct = ultima_medicion.humedad_suelo_pct if ultima_medicion else None
    precipitacion_mm = ultima_medicion.precipitacion_acumulada_mm if ultima_medicion else None

    # 4. MOTOR DE DECISIÓN DEL SEMÁFORO
    alertas = []
    advertencias = []
    conformidades = []
    score_riesgo = 10  # Base segura

    # --- REGLA 1: AMORTIGUAMIENTO ESTEROS DEL IBERÁ (Ley Provincial Corrientes) ---
    buffer_ibera = reserva_cercana.buffer_amortiguamiento_metros if reserva_cercana else 1000
    if dist_reserva_m is not None:
        if dist_reserva_m < buffer_ibera:
            if tiene_banda_roja or tiene_banda_amarilla:
                alertas.append(
                    f"INFRACCIÓN CRÍTICA IBERÁ: Lote ubicado a {dist_reserva_m}m de '{nombre_reserva}' "
                    f"(mínimo {buffer_ibera}m) con aplicación de fitosanitario Clase I/II registrada."
                )
                score_riesgo = max(score_riesgo, 95)
            elif tiene_banda_azul_verde:
                advertencias.append(
                    f"PRECAUCIÓN IBERÁ: Lote a {dist_reserva_m}m de '{nombre_reserva}' con aplicación de baja toxicidad. Monitorear derivas."
                )
                score_riesgo = max(score_riesgo, 65)
            else:
                advertencias.append(
                    f"ADVERTENCIA DE ZONA: Lote dentro del buffer de amortiguamiento ({dist_reserva_m}m < {buffer_ibera}m) de '{nombre_reserva}'."
                )
                score_riesgo = max(score_riesgo, 50)
        elif dist_reserva_m < 3000 and (tiene_banda_roja or tiene_banda_amarilla):
            advertencias.append(
                f"ZONA DE INFLUENCIA: Lote a {dist_reserva_m}m de '{nombre_reserva}' con uso de agroquímicos de banda moderada/alta."
            )
            score_riesgo = max(score_riesgo, 55)
        else:
            conformidades.append(f"Distancia segura respecto a '{nombre_reserva}' ({dist_reserva_m}m).")

    # --- REGLA 2: DERIVA HÍDRICA / CURSOS DE AGUA Y RÍOS ---
    buffer_agua = agua_cercana.buffer_seguridad_metros if agua_cercana else 200
    if dist_agua_m is not None:
        if dist_agua_m < buffer_agua:
            if tiene_banda_roja or tiene_banda_amarilla or tiene_banda_azul_verde:
                alertas.append(
                    f"INFRACCIÓN CRÍTICA FLUVIAL: Distancia a '{nombre_agua}' ({dist_agua_m}m) inferior a la zona de seguridad "
                    f"({buffer_agua}m) con aplicación de insumos. Alto riesgo de contaminación por deriva o escorrentía."
                )
                score_riesgo = max(score_riesgo, 90)
            else:
                advertencias.append(
                    f"PROXIMIDAD HÍDRICA: Lote a {dist_agua_m}m de '{nombre_agua}'. Obligatorio mantener faja vegetal de amortiguamiento."
                )
                score_riesgo = max(score_riesgo, 40)
        elif dist_agua_m < 500 and (tiene_banda_roja or tiene_banda_amarilla):
            advertencias.append(
                f"PRECAUCIÓN HÍDRICA: Distancia a '{nombre_agua}' ({dist_agua_m}m). Monitorear velocidad de viento para evitar derivas."
            )
            score_riesgo = max(score_riesgo, 60)
        else:
            conformidades.append(f"Margen hídrico seguro respecto a '{nombre_agua}' ({dist_agua_m}m).")

    # --- REGLA 3: AMORTIGUAMIENTO PERIURBANO ---
    buffer_urbano = urbana_cercana.radio_buffer_metros if urbana_cercana else 500
    if dist_urbana_m is not None:
        if dist_urbana_m < buffer_urbano and tiene_banda_roja:
            alertas.append(
                f"INFRACCIÓN PERIURBANA: Aplicación de fitosanitario Clase IA/IB a {dist_urbana_m}m de '{nombre_urbana}' "
                f"(distancia mínima exigida: {buffer_urbano}m)."
            )
            score_riesgo = max(score_riesgo, 92)
        elif dist_urbana_m < buffer_urbano * 2 and (tiene_banda_roja or tiene_banda_amarilla):
            advertencias.append(
                f"AMORTIGUAMIENTO PERIURBANO: Proximidad a '{nombre_urbana}' ({dist_urbana_m}m). Requiere aviso previo y veedor agronómico."
            )
            score_riesgo = max(score_riesgo, 65)

    # --- REGLA 4: ANOMALÍA AGROCLIMÁTICA Y ESTRÉS HÍDRICO (SENTINEL-2 / GEE) ---
    if humedad_suelo_pct is not None and ndvi_promedio is not None:
        if humedad_suelo_pct < 15.0 and ndvi_promedio < 0.40:
            alertas.append(
                f"ESTRÉS VEGETATIVO SEVERO: Humedad edáfica crítica ({humedad_suelo_pct}%) y vigor vegetal deprimido (NDVI {ndvi_promedio:.2f}). "
                f"Riesgo de pérdida de rendimiento o ignición de pasturas secas."
            )
            score_riesgo = max(score_riesgo, 85)
        elif humedad_suelo_pct < 20.0:
            advertencias.append(
                f"DÉFICIT HÍDRICO: Humedad de suelo superficial ({humedad_suelo_pct}%) por debajo del umbral óptimo (25%)."
            )
            score_riesgo = max(score_riesgo, 45)
        elif ndvi_promedio >= 0.65:
            conformidades.append(f"Vigor vegetativo óptimo registrado por Sentinel-2 (NDVI: {ndvi_promedio:.2f}).")

    # 5. DETERMINACIÓN FINAL DEL SEMÁFORO
    if alertas or score_riesgo >= 80:
        semaforo_final = NivelRiesgo.ROJO
    elif advertencias or score_riesgo >= 40:
        semaforo_final = NivelRiesgo.AMARILLO
    else:
        semaforo_final = NivelRiesgo.VERDE

    resultado = {
        "lote_id": lote.id,
        "lote_nombre": lote.nombre,
        "cultivo": lote.cultivo_actual,
        "superficie_ha": float(lote.superficie_ha) if lote.superficie_ha else 0.0,
        "fecha_evaluacion": str(fecha_evaluacion),
        "semaforo": semaforo_final,
        "score_riesgo": score_riesgo,
        "metricas_espaciales": {
            "distancia_reserva_metros": dist_reserva_m,
            "reserva_mas_cercana": nombre_reserva,
            "distancia_agua_metros": dist_agua_m,
            "cuerpo_agua_mas_cercano": nombre_agua,
            "distancia_urbana_metros": dist_urbana_m,
            "zona_urbana_mas_cercana": nombre_urbana,
        },
        "senasa_aplicaciones": {
            "total_recientes_30d": len(resumen_aplicaciones),
            "tiene_banda_roja": tiene_banda_roja,
            "tiene_banda_amarilla": tiene_banda_amarilla,
            "detalle": resumen_aplicaciones
        },
        "satelite_dw": {
            "ndvi_promedio": ndvi_promedio,
            "humedad_suelo_pct": humedad_suelo_pct,
            "precipitacion_mm": precipitacion_mm
        },
        "diagnostico": {
            "alertas_criticas": alertas,
            "advertencias_preventivas": advertencias,
            "conformidades_normativas": conformidades
        }
    }

    # 6. PERSISTENCIA EN POSTGIS Y DATA WAREHOUSE
    if actualizar_dw:
        # Actualizar el riesgo instantáneo del lote para la visualización en el mapa Leaflet
        if lote.riesgo_actual != semaforo_final:
            lote.riesgo_actual = semaforo_final
            lote.save(update_fields=['riesgo_actual'])

        # Registrar o actualizar el hecho en el DW con las distancias exactas y observaciones
        HechoMedicionAmbiental.objects.update_or_create(
            lote=lote,
            fecha_captura=fecha_evaluacion,
            defaults={
                'distancia_reserva_metros': dist_reserva_m,
                'distancia_agua_metros': dist_agua_m,
                'ndvi_promedio': ndvi_promedio,
                'humedad_suelo_pct': humedad_suelo_pct,
                'precipitacion_acumulada_mm': precipitacion_mm,
                'semaforo_resultado': semaforo_final,
                'observaciones_json': resultado
            }
        )

    return resultado
