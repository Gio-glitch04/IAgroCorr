from django.urls import path
from .views import lotes_geojson, zonas_urbanas_geojson, crear_lote_api

app_name = 'monitoring'

urlpatterns = [
    path('api/lotes-geojson/', lotes_geojson, name='lotes_geojson'),
    path('api/zonas-urbanas-geojson/', zonas_urbanas_geojson, name='zonas_urbanas_geojson'),
    path('api/crear-lote/', crear_lote_api, name='crear_lote_api'),
]
