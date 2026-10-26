from django.urls import path
from .views import (
    lotes_geojson,
    zonas_urbanas_geojson,
    crear_lote_api,
    eliminar_lote_api,
    gemelos_globales_api,
    capas_ambientales_geojson,
    evaluar_lote_api,
)

app_name = 'monitoring'

urlpatterns = [
    path('api/lotes-geojson/', lotes_geojson, name='lotes_geojson'),
    path('api/zonas-urbanas-geojson/', zonas_urbanas_geojson, name='zonas_urbanas_geojson'),
    path('api/capas-ambientales-geojson/', capas_ambientales_geojson, name='capas_ambientales_geojson'),
    path('api/crear-lote/', crear_lote_api, name='crear_lote_api'),
    path('api/eliminar-lote/<int:lote_id>/', eliminar_lote_api, name='eliminar_lote_api'),
    path('api/evaluar-lote/<int:lote_id>/', evaluar_lote_api, name='evaluar_lote_api'),
    path('api/gemelos-globales/', gemelos_globales_api, name='gemelos_globales_api'),
]


