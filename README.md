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

Configuración en `config/regiones.yaml`.

## Estructura

```text
config/regiones.yaml      # región, sandbox, cráter, anillos, rutas
pipeline/                 # scripts de descarga, normalización, simulación
geo/
  raw/                    # datos originales (DANE, SGC, DEM, curvas)
  processed/              # capas normalizadas/recortadas
  downloads/              # exportaciones GPX/KML para Garmin
  viento/                 # perfiles de viento Open-Meteo (CSV/JSON)
  simulacion/             # salidas de la pluma (TIF + GeoJSON por hora)
qgis/                     # documentación del proyecto QGIS
master_purace.qgz         # proyecto QGIS con capas + estilos + animación
```

## Pipeline de datos

| Paso | Script | Salida |
|---|---|---|
| Descargar DANE (departamentos, municipios, cabeceras, veredas) | `descargar_dane.py` | `geo/raw/*.geojson` |
| Descargar amenaza SGC (vector oficial) | `descargar_sgc.py` | `geo/raw/sgc_*.geojson` |
| Descargar relieve Copernicus DEM 30m + curvas | `descargar_relieve.py` | `geo/raw/dem/`, `curvas_50m.shp`, `curvas_maestras_250m.shp` |
| Normalizar (uppercase, atributos, CRS) | `normalizar.py` | `geo/processed/` |
| Recortar por anillos 5/15/30 km | `recortar_anillos.py` | `geo/processed/*_anillo*.geojson` |
| Exportar GeoJSON + índice | `exportar_geojson.py` | `geo/downloads/` |
| Exportar GPX/KML (Garmin) | `exportar_garmin.py` | `geo/downloads/*.gpx/kml` |
| Orquestar todo | `run_pipeline.py --solo ...` | — |

## Simulación de dispersión de ceniza

```
descargar_viento.py ──► viento_prevision_72h.csv/.json  (perfil horario 10 niveles)
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
|---|---|---|
| `5km` | 5 000 m | 2×10⁴ kg/s (moderada) |
| `8km` | 8 000 m | 1×10⁵ kg/s (fuerte) |
| `12km` | 12 000 m | 5×10⁵ kg/s (vulcánica) |

El viento se toma del nivel de presión más cercano a la altura de la columna
(`ALT_PRESION` en `simular_pluma.py`).

### Modelo

Pluma gaussiana con **coeficientes Briggs rurales** (Pasquill-Gifford 1-6) y
**sedimentación gravitatoria multi-clase** de 5 diámetros de partícula
(20–500 µm, fracciones 0.25/0.35/0.20/0.15/0.05). La pluma viaja hacia
`dir_viento + 180°`. Fuente de viento: Open-Meteo API (gratis, sin clave).

### Ejecución

```bash
python pipeline/simular_pluma.py --region purace --modo prev --hasta 24 --radio 60000
python pipeline/simular_pluma.py --region purace --modo prev --hasta 72 --radio 60000
python pipeline/simular_pluma.py --region purace --modo clima --temporada dic_feb --radio 60000
```

`--radio` define la semiextensión del dominio en metros centrado en el cráter
(120 km de lado cubre plumas en cualquier dirección). Sin `--radio`, se usa el
sandbox.

### Animación en QGIS

`pipeline/aplicar_simulacion_qgis.py` carga el grupo **Simulacion ceniza
(prevision)** (216 capas temporales para 24 h × 3 escenarios × 3 productos).
Animar con **Vista ▸ Panel ▸ Control temporal ▸ play**.

Detalles en `qgis/03_simulacion_viento.md`.

## Proyecto QGIS

`master_purace.qgz` (backup en `master_purace.qgz.bak`) incluye 11 capas de
contexto estilizadas (DANE, SGC amenaza categorizada, anillos graduados,
piroclastos, cráter) más el grupo de simulación. Se configura con:

- `pipeline/aplicar_estilos_qgis.py` — capas base y estilos.
- `pipeline/aplicar_simulacion_qgis.py` — capas temporales de ceniza.

Documentación en `qgis/01_adquisicion.md`, `qgis/02_estilos.md`,
`qgis/03_simulacion_viento.md`.

## Entorno

- Python del QGIS 3.44.7: `D:\Program Files\QGIS 3.44.7\apps\Python312\python.exe`
  (PyQGIS + GDAL disponibles).
- PyQGIS headless: `QgsApplication(argv, False)` +
  `setPrefixPath('D:/Program Files/QGIS 3.44.7/apps/qgis', True)`.
- Curvas de nivel: CLI `gdal_contour.exe -i 50 -a ELEV` (la API
  `ContourGenerate` no está disponible).
- Fuentes externas: DANE Geoportal, SGC mapa de amenaza (vector oficial),
  Copernicus DEM 30m (AWS), Open-Meteo.

## Seguridad

`credenciales.md` contiene contraseñas reales de FTP/SSH. **Está en
`.gitignore` y no debe subirse al repositorio.** Para portar a otro equipo,
usar variables de entorno o un gestor de secretos.
