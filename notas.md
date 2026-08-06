Perfecto: entonces tu caso no es VPS, sino **hosting compartido Hostinger** con **Apache + PHP + MySQL**, y eso cambia la arquitectura. En ese entorno sí puedes montar el portal, el CRUD de noticias, el login y los visores Leaflet/Cesium, pero con una estrategia **100% estática para los mapas pesados** y backend PHP para autenticación, CMS y entrega de archivos. [hostinger](https://www.hostinger.com/support/features/supported-technologies-and-functions/)

## Implicación técnica

En hosting compartido debes asumir tres límites prácticos: no hay procesos largos en segundo plano como en un VPS, el control del servidor es parcial, y el stack debe ser liviano. Hostinger sí soporta PHP, PDO/pdo_mysql, MySQL y cron jobs desde hPanel, así que puedes automatizar sincronizaciones y generar archivos offline mediante tareas programadas. Para Cesium, lo más seguro es servir todo como archivos estáticos desde Apache y evitar depender de servicios externos en tiempo de ejecución. [support.hostinger](https://support.hostinger.com/en/articles/1583709-do-you-offer-pdo-and-pdo_mysql-in-hostinger)

## Arquitectura ajustada

La arquitectura recomendada para tu hosting compartido es:

- **Frontend público** en HTML/CSS/JS con Leaflet y Cesium cargados como assets estáticos.
- **Backend PHP** para login, sesiones, CRUD de noticias, catálogo de capas, descargas y bitácora.
- **MySQL** para usuarios, publicaciones, capas, fuentes, permisos y auditoría.
- **Carpeta geo/** para GeoJSON, KML, MBTiles y metadatos.
- **Cron jobs PHP** para actualizar datasets, regenerar índices y hacer backups. [hostinger](https://www.hostinger.com/es/support/1583465-como-configurar-un-cron-job-en-hostinger/)

### Estructura de carpetas

```text
public_html/
  index.php
  login.php
  logout.php
  admin/
    dashboard.php
    noticias/
    capas/
    usuarios/
    descargas/
  api/
    auth.php
    noticias.php
    capas.php
    descargas.php
    logs.php
  assets/
    css/
    js/
    img/
  maps/
    leaflet/
    cesium/
  geo/
    raw/
    processed/
    vector_tiles/
    kml/
    downloads/
  includes/
    config.php
    db.php
    auth.php
    csrf.php
    functions.php
  cron/
    update_layers.php
    backup.php
    sync_news.php
```

## Sistema de login

El login debe ser en PHP con sesiones seguras y control de roles, porque en hosting compartido eso es más estable que montar una autenticación compleja en Node. Usa `password_hash()` y `password_verify()` para contraseñas, `PDO` para consultas, regeneración de sesión al autenticar y token CSRF en formularios. Los roles mínimos deberían ser: `admin`, `editor`, `gis`, `viewer` y `emergency`. [hostinger](https://www.hostinger.com/support/features/supported-technologies-and-functions/)

### Tablas clave

- `users`
- `roles`
- `user_roles`
- `sessions` o logs de acceso
- `password_resets`

## CRUD de noticias

El módulo de noticias puede ser totalmente PHP + MySQL. Cada noticia debe soportar título, resumen, contenido, imagen destacada, adjuntos PDF, estado editorial, fecha de publicación, autor y relación con una capa geográfica o evento operativo. Si lo deseas, también puedes manejar categorías como “alerta”, “boletín”, “vía”, “hidrología”, “viento” y “operación”.

### Tablas sugeridas

```sql
news_posts
news_categories
news_media
news_tags
news_post_tags
news_publication_log
```

### Funciones del CRUD

- Crear, editar, publicar, programar y archivar noticias.
- Subir imagen y documentos.
- Vincular una noticia con una capa, un municipio o un evento.
- Mostrar historial de cambios.
- Generar vistas públicas y privadas.

## Módulo de mapas Leaflet

Leaflet debe ser tu visor 2D principal. En hosting compartido funciona muy bien porque solo requiere JS, CSS y archivos GeoJSON/tiles servidos por Apache. Puedes cargar capas de vías, límites, hidrografía y amenaza directamente desde `/geo/processed/*.geojson` o desde tiles vectoriales estáticos. [github](https://github.com/allartk/leaflet.offline)

### Funcionalidades Leaflet

- Base map configurable.
- Capas con estilo por categoría.
- Búsqueda de municipios y puntos críticos.
- Medición de distancias y áreas.
- Dibujo de puntos/rutas.
- Descarga de capas visibles.
- Modo offline PWA.

### Datos ideales para Leaflet

- GeoJSON de INVIAS.
- GeoJSON de DANE.
- GeoJSON de IGAC/IDEAM.
- Zonas de amenaza volcánica.
- Puntos de mando, refugios y albergues.

## Módulo Cesium 3D

Cesium también puede correr en hosting compartido si lo dejas como aplicación estática y sirves tus archivos locales. El punto importante es no depender de internet para imágenes, terrain o 3D tiles, y cargar los recursos desde tu mismo dominio. Si quieres 3D real, puedes usar terreno local, polígonos extruidos y capas de infraestructura o puntos críticos. [github](https://github.com/CesiumGS/cesium/blob/main/Documentation/OfflineGuide/README.md)

### En Cesium puedes cargar

- GeoJSON local.
- KML local.
- Tiles vectoriales o 3D Tiles locales.
- Modelos glTF/GLB.
- Terreno local pre-generado.
- Imágenes raster en cache local.

## Offline real

Para que el sistema funcione offline, la estrategia debe ser preventiva: generar todo antes, alojarlo en el mismo Hostinger y hacer que el navegador lo cachee. En una red sin internet, el portal podrá funcionar si el usuario ya abrió la app y si el PWA cacheó los recursos o si están en un dispositivo local con acceso al hosting interno. No conviene depender de WMS en campo; mejor descargar, convertir y publicar GeoJSON, KML y MBTiles. [github](https://github.com/CesiumGS/cesium/blob/main/Documentation/OfflineGuide/README.md)

### Flujo offline recomendado

1. Descargar origen.
2. Convertir a EPSG:4326.
3. Limpiar geometrías.
4. Generar GeoJSON/KML.
5. Generar MBTiles vectorial si aplica.
6. Subir a `/geo/downloads/`.
7. Registrar en MySQL.
8. Exponer desde el portal.

## Descarga y conversión de datos

Los enlaces oficiales que deberías usar como origen siguen siendo estos: DANE para datos geoestadísticos, IGAC para cartografía base, INVIAS para red vial, e IDEAM para pronóstico y alertas. A partir de esas fuentes, el backend puede almacenar una “copia de operación” en formatos listos para descargar: GeoJSON, KML, MBTiles y ZIP. [geoportal.dane.gov](https://geoportal.dane.gov.co/servicios/descarga-y-metadatos/datos-geoestadisticos/)

### Repositorio de descargas

```text
geo/downloads/
  invias_roads.geojson
  invias_roads.kml
  invias_roads.mbtiles
  dane_municipios.geojson
  igac_hydro.geojson
  ideam_wind.csv
  purace_hazard.geojson
```

## Base de datos mínima

Tu MySQL podría tener este núcleo:

- `users`
- `roles`
- `news_posts`
- `news_attachments`
- `map_layers`
- `layer_files`
- `layer_sources`
- `downloads_log`
- `audit_log`
- `system_settings`

Eso te permite manejar noticias, capas, archivos y permisos sin mezclar todo en una sola tabla.

## Cron jobs en Hostinger

Hostinger permite crear tareas programadas desde hPanel y elegir tipo PHP o personalizado, así que puedes automatizar sincronización de capas, copias de seguridad y regeneración de índices. En hosting compartido, el cron debe ser corto y robusto; evita procesos largos o conversiones pesadas en tiempo real. [hostinger](https://www.hostinger.com/co/tutoriales/cron-job)

### Cron recomendados

- `update_layers.php`
- `backup_db.php`
- `sync_news.php`
- `generate_sitemap.php`
- `cleanup_temp.php`

## Stack final recomendado

| Capa | Tecnología |
|---|---|
| Servidor web | Apache de Hostinger  [hostinger](https://www.hostinger.com/support/features/supported-technologies-and-functions/) |
| Backend | PHP 8.x + PDO + sesiones |
| Base de datos | MySQL |
| Mapa 2D | Leaflet |
| Mapa 3D | CesiumJS |
| Offline | GeoJSON, KML, MBTiles, PWA |
| Automatización | Cron jobs Hostinger  [hostinger](https://www.hostinger.com/es/support/1583465-como-configurar-un-cron-job-en-hostinger/) |
| Despliegue | hPanel + FTP/Git + PHP |

## Ruta de implementación

Primero montaría el núcleo PHP/MySQL con login, CRUD y catálogo de capas. Luego integraría Leaflet con capas GeoJSON estáticas, y en paralelo dejaría Cesium apuntando a archivos locales dentro de tu dominio. Después agregaría el pipeline de descargas y el módulo de cron para mantener actualizado el repositorio operativo. 

Aquí tienes un inventario base de **fuentes y recursos** para tu proyecto, enfocado en operación geográfica, mapas offline, visor web y repositorio documental. Lo estructuré por tipo de fuente para que puedas pasarlo casi directo a una matriz de activos del proyecto. [geoportal.dane.gov](https://geoportal.dane.gov.co/)

## Fuentes oficiales de datos

### DANE
El Geoportal del DANE ofrece consulta, visualización, análisis y descarga de información georreferenciada, incluyendo MGN, DIVIPOLA, veredas y otros marcos territoriales. La página de descarga geoestadística publica datos en Shapefile, GeoJSON, KML y Geopackage, con versiones por vigencia y nivel geográfico. [geoportal.dane.gov](https://geoportal.dane.gov.co/servicios/descarga-y-metadatos/datos-geoestadisticos/)
Recursos clave: [Geoportal DANE](https://geoportal.dane.gov.co/), [Descarga datos geoestadísticos](https://geoportal.dane.gov.co/servicios/descarga-y-metadatos/datos-geoestadisticos/), [Geovisor MGN](https://geoportal.dane.gov.co/geovisores/territorio/mgn-marco-geoestadistico-nacional/). [geoportal.dane.gov](https://geoportal.dane.gov.co/geovisores/territorio/mgn-marco-geoestadistico-nacional/)

### IGAC
El IGAC publica datos abiertos de cartografía base, conjuntos catastrales, puntos geodésicos, red Magna-Eco, suelos, capacidad de uso, conflictos de uso y otros insumos territoriales. Esto te sirve para base topográfica, referencia espacial, capas de soporte y análisis territorial. [geoportal.igac.gov](https://geoportal.igac.gov.co/contenido/datos-abiertos-igac)
Recursos clave: [Datos Abiertos IGAC](https://geoportal.igac.gov.co/contenido/datos-abiertos-igac), [Geoportal IGAC](https://geoportal.igac.gov.co/). [geoportal.igac.gov](https://geoportal.igac.gov.co/)

### INVIAS
INVIAS expone su información vial en ArcGIS REST, especialmente a través del servicio OpenData de su MapServer, útil para red vial nacional y otras capas relacionadas. Esta es una fuente fuerte para construir tu inventario vial y luego convertir a GeoJSON, KML o tiles vectoriales. [hermes.invias.gov](https://hermes.invias.gov.co/arcgis/rest/services/OpenData/ServiciosOpenData/MapServer)
Recursos clave: [INVIAS OpenData MapServer](https://hermes.invias.gov.co/arcgis/rest/services/OpenData/ServiciosOpenData/MapServer). [hermes.invias.gov](https://hermes.invias.gov.co/arcgis/rest/services/OpenData/ServiciosOpenData/MapServer)

### IDEAM
IDEAM publica datos abiertos de pronósticos y alertas del tiempo, que puedes usar para viento, precipitación y análisis operativo meteorológico. Para tu caso, esto es clave para dispersión de ceniza, accesos y decisiones de operación en campo. [pronosticosyalertas.gov](http://www.pronosticosyalertas.gov.co/datos-abiertos-ideam)
Recursos clave: [Datos abiertos IDEAM](http://www.pronosticosyalertas.gov.co/datos-abiertos-ideam). [pronosticosyalertas.gov](http://www.pronosticosyalertas.gov.co/datos-abiertos-ideam)

### SGC
El SGC publica el mapa de amenaza volcánica del Puracé, con zonas de amenaza y soporte cartográfico oficial. Es una fuente obligatoria para la capa de amenaza y exclusión operativa en tu visor. [www2.sgc.gov](https://www2.sgc.gov.co/sgc/volcanes/VolcanPurace/Documents/Mapa_Amenaza_Purace_V1.pdf)
Recursos clave: [Mapa de amenaza Puracé PDF](https://www2.sgc.gov.co/sgc/volcanes/VolcanPurace/Documents/Mapa_Amenaza_Purace_V1.pdf). [www2.sgc.gov](https://www2.sgc.gov.co/sgc/volcanes/VolcanPurace/Documents/Mapa_Amenaza_Purace_V1.pdf)

## Recursos geoespaciales derivados

### Descargables directos
Debes priorizar formatos que sirvan tanto para edición como para publicación: Shapefile, GeoJSON, KML y Geopackage. Para un sistema mixto Leaflet/Cesium, GeoJSON y KML son los más prácticos como “capa maestra ligera”, mientras que MBTiles sirve para visualización rápida offline. [geoportal.dane.gov](https://geoportal.dane.gov.co/descargas/descarga_mgn/Manual_MGN.pdf)

### Tiles vectoriales
Para capas grandes como vías o hidrología, genera tiles vectoriales a partir de GeoJSON usando Tippecanoe y publícalos como MBTiles o tiles `.pbf`. Ese recurso es especialmente útil para Leaflet y para reducir el peso de datos en móviles o redes lentas. [bathyl](https://www.bathyl.com/en/blog/mbtiles-for-offline-maps)

### Terreno y 3D
Para Cesium necesitarás terreno local o al menos capas 3D servidas desde tu propio host, además de GeoJSON/KML para overlays. En una solución offline, el inventario debe incluir también DEM o terreno procesado si quieres que el 3D sea funcional sin internet. [community.cesium](https://community.cesium.com/t/cesium-completely-offline-mode/36153)

## Inventario operativo sugerido

| Recurso | Fuente | Formato preferido | Uso |
|---|---|---|---|
| MGN / DIVIPOLA | DANE  [geoportal.dane.gov](https://geoportal.dane.gov.co/servicios/descarga-y-metadatos/datos-geoestadisticos/) | GeoJSON / SHP / KML | Límites y referencia territorial |
| Veredas / sectores | DANE  [geoportal.dane.gov](https://geoportal.dane.gov.co/servicios/descarga-y-metadatos/datos-geoestadisticos/) | SHP / GeoJSON | Desagregación operativa |
| Cartografía base | IGAC  [geoportal.igac.gov](https://geoportal.igac.gov.co/contenido/datos-abiertos-igac) | SHP / GPKG / GeoJSON | Base topográfica y contexto |
| Hidrografía / cuencas | IGAC / IDEAM  [geoportal.igac.gov](https://geoportal.igac.gov.co/contenido/datos-abiertos-igac) | SHP / GeoJSON | Riesgo y drenajes |
| Red vial | INVIAS  [hermes.invias.gov](https://hermes.invias.gov.co/arcgis/rest/services/OpenData/ServiciosOpenData/MapServer) | GeoJSON / MBTiles | Rutas de acceso y evacuación |
| Viento y clima | IDEAM  [pronosticosyalertas.gov](http://www.pronosticosyalertas.gov.co/datos-abiertos-ideam) | CSV / raster / GeoJSON derivado | Operación y ceniza |
| Amenaza volcánica | SGC  [www2.sgc.gov](https://www2.sgc.gov.co/sgc/volcanes/VolcanPurace/Documents/Mapa_Amenaza_Purace_V1.pdf) | PDF georreferenciable / vector derivado | Zonas de amenaza |
| Tiles vectoriales | Procesados internamente  [github](https://github.com/mapbox/tippecanoe) | MBTiles / PBF | Leaflet offline |
| 3D terrain / overlays | Procesados internamente  [gis.stackexchange](https://gis.stackexchange.com/questions/154218/is-there-a-way-to-get-offline-tile-data-for-cesium) | Terrain / GeoJSON / KML | Cesium offline |

## Inventario documental

Además de los datos geográficos, conviene guardar estos recursos documentales:

- Manual de descarga y uso del MGN del DANE. [geoportal.dane.gov](https://geoportal.dane.gov.co/descargas/descarga_mgn/Manual_MGN.pdf)
- Metadatos oficiales de cada descarga. [geoportal.dane.gov](https://geoportal.dane.gov.co/servicios/descarga-y-metadatos/datos-geoestadisticos/)
- Boletines y alertas operativas del SGC. [www2.sgc.gov](https://www2.sgc.gov.co/sgc/volcanes/VolcanPurace/Documents/Mapa_Amenaza_Purace_V1.pdf)
- Documentos técnicos de amenaza, planes de respuesta y protocolos de emergencia.
- Registro interno de transformación de datos: origen, fecha, CRS, procesamiento y versión.

## Inventario para tu repositorio

Te conviene organizar el inventario por carpetas lógicas:

```text
/01_fuentes_oficiales/
  dane/
  igac/
  invias/
  ideam/
  sgc/

/02_descargas_raw/
  shp/
  geojson/
  kml/
  csv/
  pdf/

/03_procesados/
  vector_tiles/
  mbtiles/
  cleaned_geojson/
  styles/

/04_publicacion/
  leaflet/
  cesium/
  docs/
  noticias/

/05_operacion/
  logs/
  backups/
  auditorio/
```

## Prioridad de implementación

Primero catalogaría DANE, IGAC, INVIAS, IDEAM y SGC como fuentes de primer nivel, porque cubren territorio, vías, clima y amenaza. Luego produciría derivados internos para Leaflet/Cesium y finalmente un inventario de descargas listo para operación offline. [github](https://github.com/mapbox/tippecanoe)


