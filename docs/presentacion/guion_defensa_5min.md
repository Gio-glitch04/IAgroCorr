# Guion de defensa preliminar (5 minutos, un orador)

Orador: Giovanni Oscar Piazza. Unas 666 palabras habladas, a un ritmo de ~135 palabras por minuto.

## 01. Carátula · 0:20 (Acum: 0:20)

Buenas tardes, miembros del tribunal. Soy Giovanni Piazza y, junto a mi compañero Julio César Pintos, con la dirección del profesor Aldo Mettini, presentamos IAgroCorr: una plataforma Web GIS de inteligencia territorial que une imágenes satelitales, cartografía oficial e inteligencia artificial para mejorar las decisiones productivas en Corrientes y proteger sus humedales.

## 02. Estado del Arte y Brecha · 0:35 (Acum: 0:55)

Partimos de una paradoja: sobran datos, pero no se usan. Earth Engine y Sentinel-2 procesan petabytes de índices como el NDVI, que un productor no puede leer en crudo. Para trabajar esa geografía con precisión usamos PostGIS, con índices espaciales y topología exacta, y aplicamos GeoIA, que considera espacio, tiempo y vecindad. El vacío es regional: el software comercial piensa en el rinde pampeano y no protege los humedales del NEA.

## 03. Fundamentación y Objetivos · 0:30 (Acum: 1:25)

¿Por qué Corrientes? Porque el arroz, la forestación, el tabaco y los cítricos conviven con los Esteros del Iberá, sitio Ramsar, y con grandes ríos. Nuestro objetivo general es una plataforma que integre datos satelitales, cartografía oficial y aprendizaje automático para decidir mejor y gestionar riesgos ambientales. Los seis objetivos específicos se agrupan en tres pilares: un data warehouse espacial con su plataforma web, un semáforo de anomalías y un motor de gemelos climáticos.

## 04. Carátula · 0:30 (Acum: 1:55)

Combinamos Design Science Research para construir y evaluar el artefacto, Scrum adaptado con sprints quincenales y CRISP-DM para el ciclo de datos. Y no programamos a ciegas: hicimos cinco entrevistas, con INTA Corrientes, Servisoft y mentores AgTech. De ahí salieron tres requisitos: IA explicable, no una caja negra; una interfaz simple; y privacidad estricta del lote.

## 05. Arquitectura, Stack y Pipeline ETL · 0:35 (Acum: 2:30)

La arquitectura es híbrida. Uno: Earth Engine filtra las nubes y resume cada lote en la nube, así recibimos un JSON liviano en vez de imágenes de gigabytes, y sumamos en vivo las capas WMS del INTA. Dos: GeoDjango y PostGIS armonizan las geometrías y calculan áreas y distancias exactas. Tres: los modelos se entrenan en Google Colab con Scikit-learn. Y cuatro: todo corre en Docker, reproducible con un solo comando.

## 06. Arquitectura Híbrida de IA · 0:35 (Acum: 3:05)

Entrenamos modelos propios porque Corrientes tiene un clima subtropical particular y casi no hay lotes etiquetados con plagas. La IA tiene tres capas. Un sistema experto espacial, ya en producción, que cruza cada lote con los buffers del Iberá, los ríos y las bandas toxicológicas de SENASA, totalmente explicable. Un Isolation Forest que detecta caídas de vigor, calibrado con la sequía 2022-2023. Y un K-Means que encuentra gemelos climáticos, validado con Silhouette y la clasificación de Köppen.

## 07. Resultados Operativos Hoy · 0:45 (Acum: 3:50)

Y esto ya funciona hoy, en beta, en iagrocorr punto com punto ar. Primero, el productor dibuja su lote en el mapa, el sistema calcula las hectáreas al instante y lo bloquea si invade un ejido urbano. Segundo, el semáforo evalúa en milisegundos la distancia a áreas protegidas y ríos junto con el agroquímico aplicado: un arrozal en Mercedes da verde, un lote a menos de quinientos metros de un río da amarillo y una banda roja o un NDVI bajo da rojo, siempre con un diagnóstico explicable. Tercero, los gemelos globales: Uruguaiana, en Brasil, tiene un noventa y cinco por ciento de similitud. [No abrir la demo en vivo: no hay tiempo].

## 08. Propiedad Intelectual y Confidencialidad · 0:20 (Acum: 4:10)

En propiedad intelectual nos encuadramos en la Resolución 641 del 98 de la UNNE. Los derechos de autor del software son de los estudiantes, reconociendo la dirección del profesor orientador. Una eventual patente o marca se tramitaría por la universidad, y pedimos un año de reserva de publicación.

## 09. Estado Actual y Pasos a Diciembre · 0:30 (Acum: 4:40)

Hoy tenemos un setenta y cinco por ciento de avance: el diseño y la infraestructura están casi terminados, y falta automatizar el ETL y entrenar los modelos. Lo cerramos en tres sprints: en la primera quincena de noviembre, los conectores reales; en la segunda, la integración de la IA; y en diciembre, las pruebas y la entrega del informe final.

## 10. Conclusiones y Futuros Trabajos · 0:20 (Total: 5:00 / 5:00)

Para cerrar: IAgroCorr demuestra que con estándares abiertos e IA explicable se pueden convertir datos públicos dispersos en decisiones sustentables. A futuro proponemos una versión offline con alertas por WhatsApp, sumar radar Sentinel-1 para los días nublados y un piloto a campo con el INTA. Muchas gracias; quedo a disposición del tribunal.
