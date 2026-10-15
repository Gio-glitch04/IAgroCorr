from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.gis.geos import MultiPolygon, Polygon, Point, LineString
from monitoring.models import (
    Lote,
    NivelRiesgo,
    HechoMedicionAmbiental,
    ZonaUrbana,
    GemeloGlobal,
    AreaProtegida,
    CuerpoDeAgua,
    AplicacionInsumo,
    BandaToxicologica,
)
from monitoring.rules_engine import evaluar_riesgo_lote
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Puebla capas ambientales (Iberá, ríos, ejidos), lotes demo y evalúa el motor de semáforos espaciales'

    def handle(self, *args, **options):
        # 0. ZONAS URBANAS DE EXCLUSIÓN
        zonas = [
            ("Ejido Urbano Corrientes Capital", "Capital", [
                (-58.87, -27.44), (-58.78, -27.44), (-58.78, -27.52), (-58.87, -27.52), (-58.87, -27.44)
            ]),
            ("Ejido Urbano Goya", "Goya", [
                (-59.29, -29.12), (-59.23, -29.12), (-59.23, -29.17), (-59.29, -29.17), (-59.29, -29.12)
            ]),
            ("Ejido Urbano Mercedes", "Mercedes", [
                (-58.10, -29.16), (-58.05, -29.16), (-58.05, -29.21), (-58.10, -29.21), (-58.10, -29.16)
            ]),
            ("Ejido Urbano Paso de los Libres", "Paso de los Libres", [
                (-57.12, -29.69), (-57.05, -29.69), (-57.05, -29.74), (-57.12, -29.74), (-57.12, -29.69)
            ]),
            ("Ejido Urbano Gobernador Virasoro", "Santo Tomé", [
                (-56.06, -28.03), (-56.00, -28.03), (-56.00, -28.08), (-56.06, -28.08), (-56.06, -28.03)
            ]),
        ]
        for nombre_z, depto_z, coords_z in zonas:
            ZonaUrbana.objects.get_or_create(
                nombre=nombre_z,
                defaults={
                    'departamento': depto_z,
                    'geom': MultiPolygon(Polygon(coords_z)),
                    'radio_buffer_metros': 500
                }
            )
        self.stdout.write(self.style.SUCCESS("[OK] Zonas urbanas de exclusión verificadas en PostGIS"))

        # 0.1 ÁREA PROTEGIDA / PARQUE Y RESERVA NATURAL ESTEROS DEL IBERÁ
        poly_ibera = Polygon([
            (-57.85, -28.05),
            (-57.20, -27.85),
            (-56.70, -28.30),
            (-56.80, -28.80),
            (-57.40, -28.95),
            (-57.90, -28.70),
            (-58.15, -28.35),
            (-57.85, -28.05)
        ])
        AreaProtegida.objects.update_or_create(
            nombre="Parque y Reserva Natural Provincial Esteros del Iberá",
            defaults={
                "categoria": "Parque Provincial y Sitio Ramsar",
                "geom": MultiPolygon(poly_ibera),
                "buffer_amortiguamiento_metros": 1000,
                "activo": True
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Reserva Natural Esteros del Iberá georreferenciada en PostGIS"))

        # 0.2 CUERPOS DE AGUA Y RED HIDROLÓGICA PRINCIPAL DE CORRIENTES
        cuerpos_agua = [
            ("Río Paraná", "Río Principal", LineString([
                (-58.85, -27.35), (-58.85, -27.48), (-58.80, -27.90), (-59.15, -28.50), (-59.36, -29.14), (-59.65, -30.00)
            ], srid=4326), 500),
            ("Río Uruguay", "Río Principal", LineString([
                (-55.65, -28.05), (-56.00, -28.55), (-56.70, -29.30), (-57.10, -29.75), (-57.65, -30.30)
            ], srid=4326), 500),
            ("Río Corriente", "Río Principal", LineString([
                (-57.70, -28.85), (-58.20, -29.05), (-58.35, -29.30), (-58.80, -29.65), (-59.55, -30.15)
            ], srid=4326), 300),
            ("Río Santa Lucía", "Río Secundario / Hortícola", LineString([
                (-57.80, -27.90), (-58.30, -28.35), (-58.75, -28.80), (-59.10, -29.05), (-59.18, -29.14)
            ], srid=4326), 200),
            ("Riacho Goya / Cuenca Fluvial", "Curso Hídrico Sensible", LineString([
                (-59.30, -29.0985), (-59.25, -29.0985), (-59.20, -29.0985)
            ], srid=4326), 200),

            ("Laguna Iberá", "Laguna", Polygon([
                (-57.25, -28.50), (-57.10, -28.50), (-57.10, -28.65), (-57.25, -28.65), (-57.25, -28.50)
            ], srid=4326), 300),
        ]

        for nombre_ca, tipo_ca, geom_ca, buffer_ca in cuerpos_agua:
            CuerpoDeAgua.objects.update_or_create(
                nombre=nombre_ca,
                defaults={
                    "tipo": tipo_ca,
                    "geom": geom_ca,
                    "buffer_seguridad_metros": buffer_ca,
                    "activo": True
                }
            )
        self.stdout.write(self.style.SUCCESS("[OK] Cursos de agua (Paraná, Uruguay, Corriente, Santa Lucía, Laguna Iberá) indexados en PostGIS"))

        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("No hay usuarios registrados. Crea uno con createsuperuser primero."))
            return


        # 1. Lote en Mercedes (Arrozal / Cuenca Iberá)
        poly_mercedes = Polygon([
            (-58.05, -29.15),
            (-57.98, -29.15),
            (-57.98, -29.22),
            (-58.05, -29.22),
            (-58.05, -29.15)
        ])
        lote_mercedes, created = Lote.objects.get_or_create(
            nombre="Lote Mercedes Centro - Arroz",
            productor=user,
            defaults={
                'cultivo_actual': "Arroz",
                'superficie_ha': 480.50,
                'geom': MultiPolygon(poly_mercedes),
                'riesgo_actual': NivelRiesgo.VERDE,
                'activo': True
            }
        )

        # 2. Lote en Goya (Hortícola / Tabaco)
        poly_goya = Polygon([
            (-59.28, -29.10),
            (-59.22, -29.10),
            (-59.22, -29.16),
            (-59.28, -29.16),
            (-59.28, -29.10)
        ])
        lote_goya, created = Lote.objects.get_or_create(
            nombre="Parcela Goya Sur - Tabaco",
            productor=user,
            defaults={
                'cultivo_actual': "Tabaco / Hortícola",
                'superficie_ha': 185.00,
                'geom': MultiPolygon(poly_goya),
                'riesgo_actual': NivelRiesgo.AMARILLO,
                'activo': True
            }
        )

        # 3. Lote en Gobernador Virasoro (Forestal / Yerba Mate)
        poly_virasoro = Polygon([
            (-56.05, -28.02),
            (-55.97, -28.02),
            (-55.97, -28.09),
            (-56.05, -28.09),
            (-56.05, -28.02)
        ])
        lote_virasoro, created = Lote.objects.get_or_create(
            nombre="Lote Virasoro Este - Forestal",
            productor=user,
            defaults={
                'cultivo_actual': "Forestal (Pino Taeda)",
                'superficie_ha': 650.00,
                'geom': MultiPolygon(poly_virasoro),
                'riesgo_actual': NivelRiesgo.ROJO,
                'activo': True
            }
        )

        # Ingestión de Aplicaciones de Insumos (Bandas Toxicológicas SENASA)
        hoy = date.today()
        AplicacionInsumo.objects.filter(lote__in=[lote_mercedes, lote_goya, lote_virasoro]).delete()

        # Lote Mercedes: Insumos de bajo impacto / Banda Verde SENASA
        AplicacionInsumo.objects.create(
            lote=lote_mercedes,
            fecha_aplicacion=hoy - timedelta(days=12),
            ingrediente_activo="Bioestimulante Orgánico / Fosfito",
            dosis_ha=1.5,
            unidad_medida="L/ha",
            banda_toxicologica=BandaToxicologica.CLASE_IV
        )

        # Lote Goya: Insumo peligroso Clase IA (Banda Roja) aplicado cerca de cuenca hídrica
        AplicacionInsumo.objects.create(
            lote=lote_goya,
            fecha_aplicacion=hoy - timedelta(days=4),
            ingrediente_activo="Clorpirifos 48% EC (Insecticida)",
            dosis_ha=1.8,
            unidad_medida="L/ha",
            banda_toxicologica=BandaToxicologica.CLASE_IA
        )

        # Lote Virasoro: Insumo moderado Clase II (Banda Amarilla)
        AplicacionInsumo.objects.create(
            lote=lote_virasoro,
            fecha_aplicacion=hoy - timedelta(days=8),
            ingrediente_activo="Cipermetrina 25% (Piretroide)",
            dosis_ha=0.4,
            unidad_medida="L/ha",
            banda_toxicologica=BandaToxicologica.CLASE_II
        )

        # Mediciones Satelitales Base (Sentinel-2 / GEE) en Fact Table
        HechoMedicionAmbiental.objects.update_or_create(
            lote=lote_mercedes,
            fecha_captura=hoy - timedelta(days=2),
            defaults={
                'ndvi_promedio': 0.78,
                'humedad_suelo_pct': 34.5,
                'precipitacion_acumulada_mm': 45.0,
                'semaforo_resultado': NivelRiesgo.VERDE,
            }
        )

        HechoMedicionAmbiental.objects.update_or_create(
            lote=lote_goya,
            fecha_captura=hoy - timedelta(days=3),
            defaults={
                'ndvi_promedio': 0.54,
                'humedad_suelo_pct': 18.0,
                'precipitacion_acumulada_mm': 12.0,
                'semaforo_resultado': NivelRiesgo.AMARILLO,
            }
        )

        HechoMedicionAmbiental.objects.update_or_create(
            lote=lote_virasoro,
            fecha_captura=hoy - timedelta(days=1),
            defaults={
                'ndvi_promedio': 0.38,
                'humedad_suelo_pct': 11.0,
                'precipitacion_acumulada_mm': 2.0,
                'semaforo_resultado': NivelRiesgo.ROJO,
            }
        )

        # 3. EJECUCIÓN DEL MOTOR DE REGLAS ESPACIALES EN TIEMPO REAL
        self.stdout.write(self.style.NOTICE("-> Evaluando motor de reglas de semáforo espacial en PostGIS..."))
        for lote_eval in [lote_mercedes, lote_goya, lote_virasoro]:
            resultado = evaluar_riesgo_lote(lote_eval, fecha_evaluacion=hoy, actualizar_dw=True)
            self.stdout.write(self.style.SUCCESS(
                f"   [Semáforo {resultado['semaforo']}] {lote_eval.nombre}: Score {resultado['score_riesgo']}/100 "
                f"| Dist. Iberá: {resultado['metricas_espaciales']['distancia_reserva_metros']}m "
                f"| Dist. Agua: {resultado['metricas_espaciales']['distancia_agua_metros']}m"
            ))


        # 4. GEMELOS GLOBALES (Firmas agroclimáticas análogas)
        gemelos_data = [
            {
                "nombre": "Región de Uruguaiana / Itaqui, Brasil",
                "pais": "Brasil",
                "geom": Point(-56.80, -29.75, srid=4326),
                "similitud_pct": 95,
                "humedad_anual_pct": 76,
                "ndvi_min": 0.65,
                "ndvi_max": 0.80,
                "ndvi_promedio": 0.725,
                "cultivos_principales": "Arroz bajo riego, Ganadería bovina",
                "descripcion_climatica": "Subtropical húmedo sin estación seca, régimen térmico y edáfico análogo a la cuenca del Río Uruguay.",
                "orden": 1,
            },
            {
                "nombre": "Cuenca de la Laguna Merín, Uruguay",
                "pais": "Uruguay",
                "geom": Point(-54.15, -33.23, srid=4326),
                "similitud_pct": 88,
                "humedad_anual_pct": 72,
                "ndvi_min": 0.60,
                "ndvi_max": 0.75,
                "ndvi_promedio": 0.675,
                "cultivos_principales": "Arroz, Pasturas naturales, Soja",
                "descripcion_climatica": "Templado húmedo pampeano con alta radiación solar estival y suelos hidromórficos de alta retención.",
                "orden": 2,
            },
            {
                "nombre": "Delta del Río Mississippi, EE.UU.",
                "pais": "EE.UU.",
                "geom": Point(-91.25, 33.55, srid=4326),
                "similitud_pct": 85,
                "humedad_anual_pct": 74,
                "ndvi_min": 0.55,
                "ndvi_max": 0.70,
                "ndvi_promedio": 0.625,
                "cultivos_principales": "Soja, Algodón, Arroz, Maíz",
                "descripcion_climatica": "Subtropical húmedo con llanuras aluviales y régimen hidrológico comparable a humedales correntinos.",
                "orden": 3,
            },
            {
                "nombre": "Provincia de Hunan, China",
                "pais": "China",
                "geom": Point(112.30, 29.20, srid=4326),
                "similitud_pct": 82,
                "humedad_anual_pct": 80,
                "ndvi_min": 0.60,
                "ndvi_max": 0.85,
                "ndvi_promedio": 0.725,
                "cultivos_principales": "Arrozales intensivos de doble ciclo, Té",
                "descripcion_climatica": "Monzónico subtropical con veranos cálidos, lluvias estivales intensas y elevada humedad constante.",
                "orden": 4,
            },
            {
                "nombre": "KwaZulu-Natal, Sudáfrica",
                "pais": "Sudáfrica",
                "geom": Point(31.50, -28.80, srid=4326),
                "similitud_pct": 78,
                "humedad_anual_pct": 68,
                "ndvi_min": 0.50,
                "ndvi_max": 0.70,
                "ndvi_promedio": 0.60,
                "cultivos_principales": "Caña de azúcar, Cítricos, Pasturas subtropicales",
                "descripcion_climatica": "Subtropical costero y valles húmedos con régimen estacional de precipitaciones y topografía ondulada.",
                "orden": 5,
            },
        ]

        for g in gemelos_data:
            GemeloGlobal.objects.update_or_create(
                nombre=g["nombre"],
                defaults={
                    "pais": g["pais"],
                    "geom": g["geom"],
                    "similitud_pct": g["similitud_pct"],
                    "humedad_anual_pct": g["humedad_anual_pct"],
                    "ndvi_min": g["ndvi_min"],
                    "ndvi_max": g["ndvi_max"],
                    "ndvi_promedio": g["ndvi_promedio"],
                    "cultivos_principales": g["cultivos_principales"],
                    "descripcion_climatica": g["descripcion_climatica"],
                    "orden": g["orden"],
                    "activo": True
                }
            )

        self.stdout.write(self.style.SUCCESS("[OK] 5 Gemelos Globales cargados/actualizados con exito en PostGIS."))
        self.stdout.write(self.style.SUCCESS("¡Lotes demo, mediciones ambientales y gemelos globales cargados con éxito para " + user.username + "!"))

