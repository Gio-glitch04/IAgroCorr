from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

# ==========================================
# ENUMS / CHOICES
# ==========================================

class NivelRiesgo(models.TextChoices):
    VERDE = 'VERDE', _('Seguro / Óptimo')
    AMARILLO = 'AMARILLO', _('Precaución / Atención')
    ROJO = 'ROJO', _('Riesgo Crítico')


class BandaToxicologica(models.TextChoices):
    CLASE_IA = 'IA', _('Clase Ia - Sumamente Peligroso (Roja)')
    CLASE_IB = 'IB', _('Clase Ib - Muy Peligroso (Roja)')
    CLASE_II = 'II', _('Clase II - Moderadamente Peligroso (Amarilla)')
    CLASE_III = 'III', _('Clase III - Poco Peligroso (Azul)')
    CLASE_IV = 'IV', _('Clase IV - Normalmente no ofrece peligro (Verde)')


# ==========================================
# 1. TABLAS DE DIMENSIONES (ABM Operativo)
# ==========================================

class ZonaUrbana(models.Model):
    """
    Capa de Exclusión Territorial: Representa el ejido urbano donde está
    restringida o prohibida la actividad agropecuaria intensiva / pulverizaciones.
    """
    nombre = models.CharField(max_length=150, help_text="Ej: Ejido Urbano Mercedes")
    departamento = models.CharField(max_length=100, blank=True, null=True, help_text="Ej: Mercedes, Goya, Capital")
    geom = models.MultiPolygonField(srid=4326)
    radio_buffer_metros = models.IntegerField(default=0, help_text="Metros de amortiguamiento periurbano")

    class Meta:
        verbose_name = "Zona Urbana / Exclusión"
        verbose_name_plural = "Zonas Urbanas (Exclusiones)"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.departamento or 'Corrientes'})"


class Lote(models.Model):
    """
    Dimensión Espacial: Representa el polígono físico del terreno en Corrientes/NEA.
    """
    productor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lotes')
    nombre = models.CharField(max_length=100, help_text="Ej: Parcela Norte Maíz")
    cultivo_actual = models.CharField(max_length=100, blank=True, null=True, help_text="Ej: Arroz, Soja, Forestal")
    superficie_ha = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Hectáreas estimadas")
    
    # MultiPolygonField soporta polígonos simples y complejos/fragmentados en WGS84
    geom = models.MultiPolygonField(srid=4326) 
    
    # Campo cacheado para semáforo instantáneo en el dashboard Leaflet
    riesgo_actual = models.CharField(
        max_length=20, 
        choices=NivelRiesgo.choices,
        default=NivelRiesgo.VERDE,
        db_index=True
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        ordering = ['-fecha_registro']

    def clean(self):
        super().clean()
        if self.geom:
            zonas_conflicto = ZonaUrbana.objects.filter(geom__intersects=self.geom)
            if zonas_conflicto.exists():
                nombres = ", ".join([z.nombre for z in zonas_conflicto])
                raise ValidationError(
                    f"Restricción Territorial: El lote intersecta con la zona urbana '{nombres}'. "
                    f"No se permite delimitar lotes agrícolas dentro de ejidos urbanos."
                )

    def __str__(self):
        return f"{self.nombre} ({self.productor.username})"


class AplicacionInsumo(models.Model):
    """
    Dimensión de Eventos Agronómicos: Ingestión de aplicaciones de fitosanitarios y fertilizantes.
    """
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='aplicaciones')
    fecha_aplicacion = models.DateField(db_index=True)
    ingrediente_activo = models.CharField(max_length=150, help_text="Ej: Glifosato, 2,4-D, Cipermetrina")
    dosis_ha = models.DecimalField(max_digits=8, decimal_places=2, help_text="Cantidad por hectárea")
    unidad_medida = models.CharField(max_length=20, default="L/ha", help_text="Ej: L/ha, kg/ha")
    
    # Clasificación toxicológica oficial SENASA
    banda_toxicologica = models.CharField(
        max_length=5,
        choices=BandaToxicologica.choices,
        default=BandaToxicologica.CLASE_IV
    )

    class Meta:
        verbose_name = "Aplicación de Insumo"
        verbose_name_plural = "Aplicaciones de Insumos"
        ordering = ['-fecha_aplicacion']

    def __str__(self):
        return f"{self.ingrediente_activo} - {self.lote.nombre} ({self.fecha_aplicacion})"


# ==========================================
# 2. TABLA DE HECHOS (Data Warehouse / Fact Table)
# ==========================================

class HechoMedicionAmbiental(models.Model):
    """
    Tabla de Hechos (Fact Table): Almacena las firmas agroclimáticas históricas
    (Google Earth Engine / Sentinel-2 / PostGIS). Inmutable, optimizada para series de tiempo.
    """
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='historial_dw')
    
    # Separación clave: fecha del fenómeno vs fecha técnica de procesamiento
    fecha_captura = models.DateField(help_text="Fecha de paso satelital o registro meteorológico")
    fecha_procesamiento = models.DateTimeField(auto_now_add=True, help_text="Momento en que el ETL procesó los datos")
    
    # --- Métricas GEE (Teledetección / Satélite) ---
    ndvi_promedio = models.FloatField(null=True, blank=True, help_text="Índice de Vigor Vegetativo (-1.0 a 1.0)")
    humedad_suelo_pct = models.FloatField(null=True, blank=True, help_text="Porcentaje de humedad en capa superficial")
    precipitacion_acumulada_mm = models.FloatField(null=True, blank=True, help_text="Lluvia acumulada 7/15 días")
    
    # --- Métricas Espaciales PostGIS (Regulaciones Corrientes / Esteros del Iberá) ---
    distancia_reserva_metros = models.FloatField(null=True, blank=True, help_text="Distancia a la cuenca o amortiguamiento del Iberá")
    distancia_agua_metros = models.FloatField(null=True, blank=True, help_text="Distancia al río, estero o curso de agua más cercano")
    
    # --- Salida del Motor de Reglas / Algoritmo ---
    semaforo_resultado = models.CharField(max_length=20, choices=NivelRiesgo.choices)
    
    # Diagnóstico detallado para auditoría y reportes PDF/Dashboard
    observaciones_json = models.JSONField(
        null=True, 
        blank=True, 
        help_text="Detalle de umbrales vulnerados (ej: {'viento_excesivo': true, 'distancia_critica': false})"
    )

    class Meta:
        verbose_name = "Medición Ambiental (Hecho)"
        verbose_name_plural = "Mediciones Ambientales (Hechos)"
        indexes = [
            models.Index(fields=['lote', '-fecha_captura']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['lote', 'fecha_captura'], name='unique_medicion_lote_fecha')
        ]

    def __str__(self):
        return f"{self.lote.nombre} [{self.fecha_captura}] -> {self.semaforo_resultado}"


# ==========================================
# 3. GEMELOS GLOBALES (Firmas Agroclimáticas Análogas)
# ==========================================

class GemeloGlobal(models.Model):
    """
    Dimensión Territorial Global: Regiones del mundo con firmas agroclimáticas
    análogas o comparables a Corrientes y la cuenca del NEA.
    """
    nombre = models.CharField(max_length=150, help_text="Ej: Región de Uruguaiana / Itaqui, Brasil")
    pais = models.CharField(max_length=100, help_text="Ej: Brasil, Uruguay, EE.UU., China, Sudáfrica")
    geom = models.PointField(srid=4326, help_text="Coordenadas geográficas WGS84 del centroide representativo")
    
    similitud_pct = models.IntegerField(help_text="Porcentaje de similitud agroclimática global (0-100)")
    humedad_anual_pct = models.IntegerField(help_text="Porcentaje de humedad anual promedio")
    
    ndvi_min = models.FloatField(help_text="NDVI mínimo histórico en ciclo activo")
    ndvi_max = models.FloatField(help_text="NDVI máximo histórico en ciclo activo")
    ndvi_promedio = models.FloatField(help_text="NDVI promedio representativo")
    
    cultivos_principales = models.CharField(max_length=200, blank=True, null=True, help_text="Ej: Arroz, Soja, Ganadería")
    descripcion_climatica = models.TextField(blank=True, null=True, help_text="Síntesis bioclimática y similitud agronómica")
    
    orden = models.IntegerField(default=0, help_text="Prioridad de visualización en la matriz")
    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Gemelo Global"
        verbose_name_plural = "Gemelos Globales"
        ordering = ['orden', '-similitud_pct']

    def __str__(self):
        return f"{self.nombre} ({self.pais}) - {self.similitud_pct}%"

    @property
    def ndvi_rango_texto(self):
        if self.ndvi_min is not None and self.ndvi_max is not None:
            return f"{self.ndvi_min:.2f} - {self.ndvi_max:.2f}"
        return "-"

    @property
    def ndvi_val_pct(self):
        if self.ndvi_promedio is not None:
            return round(self.ndvi_promedio * 100, 1)
        return 0.0

