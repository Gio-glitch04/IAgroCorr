from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.gis.geos import MultiPolygon, Polygon
from monitoring.models import Lote, NivelRiesgo, HechoMedicionAmbiental, ZonaUrbana
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Puebla 3 lotes y las zonas urbanas de Corrientes con mediciones del DW'

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
        self.stdout.write(self.style.SUCCESS("[OK] Zonas urbanas de exclusion verificadas en PostGIS"))

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

        # Crear mediciones de prueba en el Fact Table del DW
        hoy = date.today()
        HechoMedicionAmbiental.objects.get_or_create(
            lote=lote_mercedes,
            fecha_captura=hoy - timedelta(days=2),
            defaults={
                'ndvi_promedio': 0.78,
                'humedad_suelo_pct': 34.5,
                'precipitacion_acumulada_mm': 45.0,
                'distancia_reserva_metros': 12500.0,
                'distancia_agua_metros': 850.0,
                'semaforo_resultado': NivelRiesgo.VERDE,
                'observaciones_json': {"estado": "Óptimo", "estres_hidrico": False}
            }
        )

        HechoMedicionAmbiental.objects.get_or_create(
            lote=lote_goya,
            fecha_captura=hoy - timedelta(days=3),
            defaults={
                'ndvi_promedio': 0.54,
                'humedad_suelo_pct': 16.2,
                'precipitacion_acumulada_mm': 12.0,
                'distancia_reserva_metros': 45000.0,
                'distancia_agua_metros': 1200.0,
                'semaforo_resultado': NivelRiesgo.AMARILLO,
                'observaciones_json': {"alerta": "Humedad de suelo baja por debajo del 20%"}
            }
        )

        HechoMedicionAmbiental.objects.get_or_create(
            lote=lote_virasoro,
            fecha_captura=hoy - timedelta(days=1),
            defaults={
                'ndvi_promedio': 0.38,
                'humedad_suelo_pct': 11.0,
                'precipitacion_acumulada_mm': 2.0,
                'distancia_reserva_metros': 68000.0,
                'distancia_agua_metros': 3100.0,
                'semaforo_resultado': NivelRiesgo.ROJO,
                'observaciones_json': {"alerta_critica": "Sequía severa y anomalía vegetativa detectada en Sentinel-2"}
            }
        )

        self.stdout.write(self.style.SUCCESS("¡Lotes demo y mediciones ambientales cargados con éxito para " + user.username + "!"))
