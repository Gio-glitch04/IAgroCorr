from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import Lote, AplicacionInsumo, HechoMedicionAmbiental, ZonaUrbana, GemeloGlobal, AreaProtegida, CuerpoDeAgua


@admin.register(AreaProtegida)
class AreaProtegidaAdmin(GISModelAdmin):
    list_display = ('nombre', 'categoria', 'buffer_amortiguamiento_metros', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('nombre', 'categoria')
    gis_widget_kwargs = {
        'attrs': {
            'default_zoom': 9,
            'default_lat': -28.30,
            'default_lon': -57.40, # Esteros del Iberá
        }
    }


@admin.register(CuerpoDeAgua)
class CuerpoDeAguaAdmin(GISModelAdmin):
    list_display = ('nombre', 'tipo', 'buffer_seguridad_metros', 'activo')
    list_filter = ('tipo', 'activo')
    search_fields = ('nombre', 'tipo')
    gis_widget_kwargs = {
        'attrs': {
            'default_zoom': 9,
            'default_lat': -28.70,
            'default_lon': -58.00,
        }
    }


@admin.register(ZonaUrbana)
class ZonaUrbanaAdmin(GISModelAdmin):
    list_display = ('nombre', 'departamento', 'radio_buffer_metros')
    search_fields = ('nombre', 'departamento')
    gis_widget_kwargs = {
        'attrs': {
            'default_zoom': 10,
            'default_lat': -28.70,
            'default_lon': -58.00,
        }
    }



@admin.register(Lote)
class LoteAdmin(GISModelAdmin):
    list_display = ('nombre', 'productor', 'cultivo_actual', 'superficie_ha', 'riesgo_actual', 'activo')
    list_filter = ('riesgo_actual', 'activo', 'cultivo_actual')
    search_fields = ('nombre', 'productor__username', 'productor__email')
    gis_widget_kwargs = {
        'attrs': {
            'default_zoom': 11,
            'default_lat': -28.70,
            'default_lon': -58.00, # Centro referencial Corrientes
        }
    }


@admin.register(GemeloGlobal)
class GemeloGlobalAdmin(GISModelAdmin):
    list_display = ('nombre', 'pais', 'similitud_pct', 'humedad_anual_pct', 'ndvi_promedio', 'orden', 'activo')
    list_filter = ('pais', 'activo')
    search_fields = ('nombre', 'pais', 'cultivos_principales')
    gis_widget_kwargs = {
        'attrs': {
            'default_zoom': 2,
            'default_lat': 10.0,
            'default_lon': 0.0, # Vista global
        }
    }


@admin.register(AplicacionInsumo)
class AplicacionInsumoAdmin(admin.ModelAdmin):
    list_display = ('lote', 'fecha_aplicacion', 'ingrediente_activo', 'dosis_ha', 'unidad_medida', 'banda_toxicologica')
    list_filter = ('banda_toxicologica', 'fecha_aplicacion')
    search_fields = ('ingrediente_activo', 'lote__nombre')


@admin.register(HechoMedicionAmbiental)
class HechoMedicionAmbientalAdmin(admin.ModelAdmin):
    list_display = ('lote', 'fecha_captura', 'semaforo_resultado', 'ndvi_promedio', 'humedad_suelo_pct', 'precipitacion_acumulada_mm')
    list_filter = ('semaforo_resultado', 'fecha_captura')
    search_fields = ('lote__nombre',)
    date_hierarchy = 'fecha_captura'

