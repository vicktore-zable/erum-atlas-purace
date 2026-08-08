# ERUM Atlas · Puracé — Pipeline geoespacial y simulación

Sandbox operativo del **volcán Puracé** (Cauca, Colombia) para el proyecto
ERUM Atlas: pipeline de datos DANE/SGC, relieve, proyecto QGIS estilizado y
simulación de dispersión de ceniza volcánica.

## Contexto

- **Volcán Puracé:** 2°18'50" N, 76°23'50" W; ~26 km al SE de Popayán,
  ~10 km al SE de Puracé-Coconuco.
- **Sandbox WGS84 (EPSG:4326):** `-76.60, 1.95, -76.22, 2.32` (West, South,
  East, North).
- **Anillos operativos:** 5 km (núcleo), 15 km (operativo), 30 km (impacto
  regional).
- **CRS:** datos en EPSG:4326; proyección local de análisis EPSG:3116
  (Colombia Oeste / Bogotá).
- **Municipios afectados:** 11 municipios en radio de 100km (Cauca y Huila).

Configuración en `config/regiones.yaml`.

## Estructura

```text
config/regiones.yaml              # región, sandbox, cráter, anillos, rutas
pipeline/                         # scripts de descarga, normalización, simulación
geo/
  raw/                            # datos originales (DANE, SGC, DEM, curvas)
  processed/                      # capas normalizadas/recortadas
    vig2025/                      # VIG2025 recortado a 11 municipios (23 GeoJSON)
    mgn2025/                      # MGN 2025 recortado (9 GeoJSON)
    municipios_afectados.geojson  # Polígono de los 11 municipios
  wind/                           # Vectores de viento (24 GeoJSON)
  ash_contours/                   # Contornos ceniza (144 GeoJSON)
  simulacion/                     # salidas de la pluma (TIF + GeoJSON por hora)
  downloads/                      # exportaciones GPX/KML para Garmin
qgis/                             # documentación del proyecto QGIS
docs/                             # documentación adicional
public_html/                      # visor web Leaflet + Cesium
master_purace.qgz                 # proyecto QGIS con capas + estilos + animación
```

## Pipeline de datos

| Paso | Script | Salida |
|------|--------|--------|
| Descargar DANE | `descargar_dane.py` | `geo/raw/*.geojson` |
| Descargar SGC | `descargar_sgc.py` | `geo/raw/sgc_*.geojson` |
| Descargar relieve | `descargar_relieve.py` | `geo/raw/dem/`, curvas |
| Normalizar | `normalizar.py` | `geo/processed/` |
| Recortar por anillos | `recortar_anillos.py` | `geo/processed/*_anillo*.geojson` |
| Recortar VIG2025 | `recortar_vig2025_geopandas.py` | `geo/processed/vig2025/` |
| Exportar GeoJSON | `exportar_geojson.py` | `geo/downloads/` |
| Exportar GPX/KML | `exportar_garmin.py` | `geo/downloads/*.gpx/kml` |
| Simular pluma | `simular_pluma.py` | `geo/simulacion/` |
| Generar viento | `generate_wind_vectors.py` | `geo/wind/` |
| Vectorializar ceniza | `vectorize_ash.py` | `geo/ash_contours/` |

## Simulación de dispersión de ceniza

```
descargar_viento.py ──► viento_prevision_72h.csv/.json
       ▼
simular_pluma.py ──► geo/simulacion/prevision/H_{5,8,12}km/
       │                ├─ *_concentracion.tif   (mg/m³)
       │                ├─ *_deposito.tif        (g/m²)
       │                └─ *_sector.geojson      (sector probable)
       ▼
aplicar_simulacion_qgis.py ──► master_purace.qgz (capas temporales animables)
```

### Escenarios eruptivos

| Escenario | Altura columna | Tasa de emisión |
|-----------|----------------|-----------------|
| `5km` | 5 000 m | 2×10⁴ kg/s (moderada) |
| `8km` | 8 000 m | 1×10⁵ kg/s (fuerte) |
| `12km` | 12 000 m | 5×10⁵ kg/s (vulcánica) |

### Ejecución

```bash
python pipeline/simular_pluma.py --region purace --modo prev --hasta 24 --radio 60000
python pipeline/simular_pluma.py --region purace --modo prev --hasta 72 --radio 60000
```

## Proyecto QGIS

`master_purace.qgz` incluye:

### Capas (26)

| Grupo | Capas |
|-------|-------|
| Base Maps | OpenStreetMap, Esri Satellite, Colombia |
| Administrativo | Departamentos, Municipios, Veredas, Cabeceras |
| Vulcanología | SGC Amenaza, SGC Piroclastos, SGC Volcán Puracé |
| Vías | Vías DANE MGN (9,446 features) |
| Urbano | Líneas urbanas, Toponimia, Nomenclatura, Manzanas |
| Rural | Cultura, Hidrografía, Curvas de nivel |
| Sectorización DANE | Secciones, Sectores, Zonas, Clase terreno |

### Estilos

- **SGC Amenaza:** categorizado Alta→rojo, Media→naranja, Baja→amarillo
- **Vías:** categorizado por tipo (motorway, trunk, primary, secondary, tertiary)
- **Hidrografía:** línea azul
- **Curvas de nivel:** línea gris
- **Veredas:** borde gris claro punteado

### Documentación

- `docs/qgis_master_purace.md` — Documentación completa
- `qgis/01_adquisicion.md` — Guía de adquisición de datos
- `qgis/02_estilos.md` — Documentación de estilos
- `qgis/03_simulacion_viento.md` — Documentación de simulación

## Visor Web

### Leaflet 2D + Cesium 3D

```bash
# Iniciar servidor
cd public_html && python -m http.server 8080

# Abrir en navegador
http://localhost:8080
```

### Funcionalidades

- Visor dual: Leaflet 2D / Cesium 3D / Split
- Panel de capas con checkboxes
- Popups informativos
- Terrain 3D (Cesium)
- Sincronización entre visores

## Datos en G:\SIG

### DANE MGN 2025

**Ruta:** `G:\SIG\01_FUENTES_OFICIALES\DANE\MGN2025_00_COLOMBIA\MGN_2025_COLOMBIA\`

| Directorio | Contenido |
|------------|-----------|
| ADMINISTRATIVO | Departamentos, Municipios |
| COLOMBIA | Límite nacional |
| MGN | Secciones, Sectores, Zonas urbanas |
| RURAL | Cultura, Hidrografía, Hipso (curvas) |
| URBANO | Líneas, Toponimia, Nomenclatura, Manzanas |
| VIAS | Red vial nacional (323,797 features) |
| SIMBOLOS | 252 símbolos SVG |

### IGAC

**Ruta:** `G:\SIG\01_FUENTES_OFICIALES\IGAC\VECTOR\`

| Capa | Archivo |
|------|---------|
| Vías 1:100K | `vias 1-100000.shp` |
| Vías Colombia 1:500K | `vias colombia 1-500000.shp` |
| Ríos | `rios_simples.shp` |
| Orografía | `orografia.shp` |
| Cabeceras | `cabeceras_municipales-igac.shp` |
| Sitios de interés | `sitios de interes.shp` |

## Municipios Afectados (11)

| # | Municipio | Departamento | DIVIPOLA | Distancia |
|---|-----------|--------------|----------|-----------|
| 1 | Puracé | Cauca | 19585 | 6.4 km |
| 2 | Popayán | Cauca | 19001 | 25.9 km |
| 3 | Sotará - Páispamba | Cauca | 19760 | 26.5 km |
| 4 | Isnos | Huila | 41359 | 34.2 km |
| 5 | Saladoblanco | Huila | 41660 | 37.0 km |
| 6 | San Agustín | Huila | 41668 | 38.4 km |
| 7 | La Argentina | Huila | 41378 | 38.5 km |
| 8 | Inzá | Cauca | 19355 | 41.9 km |
| 9 | La Vega | Cauca | 19397 | 48.5 km |
| 10 | Pitalito | Huila | 41551 | 60.0 km |
| 11 | San Sebastián | Cauca | 19693 | 65.7 km |

## Entorno

- Python del QGIS 3.44.7: `D:\Program Files\QGIS 3.44.7\apps\Python312\python.exe`
- PyQGIS headless: `QgsApplication(argv, False)` + `setPrefixPath('D:/Program Files/QGIS 3.44.7/apps/qgis', True)`
- Curvas de nivel: CLI `gdal_contour.exe -i 50 -a ELEV`
- Fuentes externas: DANE Geoportal, SGC ArcGIS, Copernicus DEM, Open-Meteo

## Seguridad

`credenciales.md` contiene contraseñas reales de FTP/SSH. **Está en
`.gitignore` y no debe subirse al repositorio.** Para portar a otro equipo,
usar variables de entorno o un gestor de secretos.
