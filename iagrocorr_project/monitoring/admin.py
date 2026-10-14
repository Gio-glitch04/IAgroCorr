from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import Lote, AplicacionInsumo, HechoMedicionAmbiental


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
