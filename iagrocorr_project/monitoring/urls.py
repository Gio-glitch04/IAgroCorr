from django.urls import path
from .views import lotes_geojson

app_name = 'monitoring'

urlpatterns = [
    path('api/lotes-geojson/', lotes_geojson, name='lotes_geojson'),
]
