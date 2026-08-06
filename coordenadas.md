Sí. Para **Puracé** ya puedes definir un **sandbox operativo WGS84** suficientemente sólido para automatizar cortes de shapes, geoservicios y exportaciones compatibles con Garmin. [www2.sgc.gov](https://www2.sgc.gov.co/sgc/volcanes/VolcanPurace/Documents/Mapa_Amenaza_Purace_web.pdf)

## Sandbox propuesto

La referencia más útil es el mapa de amenaza del SGC, que ubica el volcán Puracé en **2°18'50" N, 76°23'50" W**, y el plan nacional de preparación agrega que el volcán está a unos **26–27 km al SE de Popayán** y a alrededor de **10 km al SE de la cabecera de Puracé-Coconuco**. Además, el plan de respuesta indica un **perímetro radial de 5 km alrededor del cráter** y cuencas que drenan hacia la ladera norte del cono volcánico como componentes clave del área de atención. [www2.sgc.gov](https://www2.sgc.gov.co/sgc/volcanes/VolcanPurace/Documents/Memoria_MapaAmenaza_Purace.pdf)

## Caja de trabajo WGS84

Para automatización operativa, te conviene trabajar con una caja amplia en WGS84 que cubra el volcán, las rutas de evacuación, la cabecera de Puracé-Coconuco y la franja hacia Popayán. Como punto de partida práctico, usa este bounding box:

- **West:** -76.60
- **South:** 1.95
- **East:** -76.22
- **North:** 2.32

Esa caja incluye el cráter, el entorno cercano, áreas de drenaje y conexión vial para evacuación, sin irte a un recorte excesivo. [portal.gestiondelriesgo.gov](https://portal.gestiondelriesgo.gov.co/Documents/Planes-respuesta/PLAN-NACIONAL-DE-PREPARACION-Y-RESPUESTA-VOLCAN-PURACE.pdf)

## Buffer operativo recomendado

Para producción, te sugiero manejar **tres anillos** en vez de uno solo:

- **Zona núcleo:** radio 5 km desde el cráter, siguiendo el criterio del plan de respuesta. [portal.gestiondelriesgo.gov](https://portal.gestiondelriesgo.gov.co/Documents/Planes-respuesta/PLAN-NACIONAL-DE-PREPARACION-Y-RESPUESTA-VOLCAN-PURACE.pdf)
- **Zona operativa:** radio 15 km, para rutas, puntos de control, refugios y accesos.
- **Zona extendida:** radio 30 km, para análisis de impacto sobre Popayán, Puracé-Coconuco y corredores logísticos. [www2.sgc.gov](https://www2.sgc.gov.co/sgc/volcanes/VolcanPurace/Documents/Mapa_Amenaza_Purace_web.pdf)

Esto te permite automatizar cortes distintos según el uso: emergencia inmediata, análisis táctico y planeación regional.

## Coordenadas de referencia

Con lo que publica el SGC, los puntos de referencia más útiles son:

- **Cráter/centro volcánico del Puracé:** 2°18'50" N, 76°23'50" W. [www2.sgc.gov](https://www2.sgc.gov.co/sgc/volcanes/VolcanPurace/Documents/Memoria_MapaAmenaza_Purace.pdf)
- **Centro aproximado de la cadena volcánica / referencia de planificación:** 2°17'32" N, 76°22'41" W. [portal.gestiondelriesgo.gov](https://portal.gestiondelriesgo.gov.co/Documents/Planes-respuesta/PLAN-NACIONAL-DE-PREPARACION-Y-RESPUESTA-VOLCAN-PURACE.pdf)
- **Ubicación citada en el plan nacional:** 2°19'01" N, 76°23'53" W. [portal.gestiondelriesgo.gov](https://portal.gestiondelriesgo.gov.co/Documents/Planes-respuesta/PLAN-NACIONAL-DE-PREPARACION-Y-RESPUESTA-VOLCAN-PURACE.pdf)

Para Garmin y GPS de campo, convierte todo a **WGS84 decimal** y usa puntos, rutas y polígonos simplificados.

## Estructura para automatizar cortes

Te conviene generar tu repositorio por capas:

1. **clip_sandbox_5km**  
   Solo la zona crítica para operaciones inmediatas.

2. **clip_sandbox_15km**  
   Rutas, hidrología, población cercana, accesibilidad.

3. **clip_sandbox_30km**  
   Contexto regional, impacto extendido y planeación.

4. **clip_routes_garmin**  
   Solo líneas y waypoints compatibles con GPX/KML.

5. **clip_geoservices_wms_wfs**  
   Derivados de los geoservicios para publicación en Leaflet y Cesium.

## Recomendación práctica

Si quieres eficiencia real en campo, no intentes usar una sola capa gigante. Lo correcto es preparar:

- **GeoJSON operativo** para web.
- **KML/GPX** para Garmin.
- **SHP/MBTiles** para edición y mapas offline.
- **WMS/WFS cacheados** solo para consumo interno, no como base de operación.

## Mi recomendación final

Para Puracé, yo adoptaría este estándar:

- **Sandbox maestro:** bbox WGS84 `[-76.60, 1.95, -76.22, 2.32]`.
- **Zona crítica:** 5 km.
- **Zona táctica:** 15 km.
- **Zona extendida:** 30 km.

Eso te deja una geometría suficientemente robusta para automatizar recortes, publicar geoservicios y generar salidas compatibles con Garmin sin perder precisión operativa. [www2.sgc.gov](https://www2.sgc.gov.co/sgc/volcanes/VolcanPurace/Documents/Mapa_Amenaza_Purace_web.pdf)

Si quieres, el siguiente paso te lo puedo entregar como:
- **GeoJSON del sandbox en WGS84**, o
- **script QGIS/Python para recortar automáticamente capas y exportar SHP, KML y GPX**.