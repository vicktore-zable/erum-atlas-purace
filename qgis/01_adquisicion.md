# Guía de Adquisición de Datos — ERUM Atlas · Puracé

Sprint 1: DANE (MGN/DIVIPOLA) + SGC (amenaza volcánica Puracé).
Pipeline automatizado en `pipeline/`, documentación para QGIS en esta guía.

---

## 1. Resumen del sandbox (WGS84)

| Parámetro | Valor |
|---|---|
| Bounding box | `[-76.60, 1.95, -76.22, 2.32]` |
| Cráter Puracé | `2.313889°N, -76.397222°W` |
| Anillo núcleo | 5 km (operaciones inmediatas) |
| Anillo táctico | 15 km (rutas, refugios, accesos) |
| Anillo extendido | 30 km (impacto regional) |

> Definido en `coordenadas.md`; materializado en `config/regiones.yaml`.

---

## 2. Ejecutar el pipeline automático

El pipeline corre en **QGIS (Python 3.12 + GDAL)**. Desde la consola Python de
QGIS (menú *Extensiones → Consola Python*) o desde terminal:

```bash
# Desde la carpeta pipeline/
python run_pipeline.py --region purace
```

### Paso a paso (equivalente manual)

| Paso | Comando | Qué produce |
|---|---|---|
| 1. Adquisición DANE | `python descargar_dane.py --region purace` | `geo/raw/dane_*.geojson` (recortadas al sandbox) |
| 2. Adquisición SGC | `python descargar_sgc.py --region purace` | Vectores amenaza/piroclastos/volcán + PDF referencia |
| 3. Normalizar | `python normalizar.py --region purace` | Capas EPSG:4326 en `geo/processed/` |
| 4. Recortar anillos | `python recortar_anillos.py --region purace` | `*__clip_sandbox_{5,15,30}km.geojson` |
| 5. Exportar web | `python exportar_geojson.py --region purace` | Nombres canónicos + `index.json` |
| 6. Exportar Garmin | `python exportar_garmin.py --region purace` | `geo/downloads/*.gpx` + `*.kml` |

> **Windows**: usa el Python de QGIS (`C:\Program Files\QGIS 3.x\bin\python-qgis.bat`).

---

## 3. Fuentes oficiales (Sprint 1)

### DANE — MGN / DIVIPOLA
Descarga oficial desde el geoportal DANE (catálogo dinámico):

| Capa | Vigencia | URL directa (GeoJSON ZIP) | Nº features en sandbox |
|---|---|---|---|
| Departamentos | 2025 | `https://geoportal.dane.gov.co/descargas/mgn_2025/MGN2025_ADM_DPTO_POLITICO_(geojson).zip` | 3 |
| Municipios | 2025 | `https://geoportal.dane.gov.co/descargas/mgn_2025/MGN2025_ADM_MPIO_GRAFICO_(geojson).zip` | 11 |
| Veredas | 2024 | `https://geoportal.dane.gov.co/descargas/veredas/gjson_CRVeredas_2024.zip` | 72 |
| Cabeceras y centros poblados | 2025 | `https://geoportal.dane.gov.co/descargas/mgn_2025/MGN2025_URB_ZONA_URBANA_(geojson).zip` | 4 |

Catálogo dinámico: `https://geoportal.dane.gov.co/laboratorio/serviciosjson/geoportal2019/geoportal-datos-geoestadisticos.php`

CRS origen del DANE: **MAGNA-SIRGAS (EPSG:4686)** → el pipeline reproyecta a EPSG:4326.

### SGC — Amenaza volcánica Puracé (vectorial oficial)
El SGC publica la amenaza volcánica como **capas vectoriales** en su ArcGIS Server
(sin necesidad de georreferenciar el PDF). El pipeline las extrae automáticamente.

| Capa | Tipo | Contenido | Archivo salida |
|---|---|---|---|
| 1 — Volcan | Punto | Cráter Puracé | `sgc_volcan_punto.geojson` |
| 2 — Caida_Piroclastos | Línea | Zona influencia piroclastos | `sgc_piroclastos.geojson` |
| 3 — Amenaza_Volcanica_P | Polígono | Zonas Alta/Media/Baja/Lahar | `sgc_amenaza.geojson` |

Endpoint ArcGIS:
`https://srvags.sgc.gov.co/arcgis/rest/services/Amenaza_Volcanica/Amenaza_Volcanica/MapServer`

> **Nota técnica**: el `FeatureServer/query` devuelve HTTP 400; el pipeline usa
> `MapServer/3/query` (sin paginación) que funciona correctamente. Los datos son
> EPSG:4686 MAGNA-SIRGAS, reproyectados a EPSG:4326 por `normalizar.py`.

El PDF del SGC se descarga como **documento de referencia** (`geo/raw/sgc_amenaza_purace.pdf`),
no es necesario vectorizarlo: el vector oficial ya lo trae el pipeline.

---

## 4. Validación de los vectores SGC en QGIS

Las capas SGC llegan vectoriales desde el pipeline (no hay digitalización manual).
Verificar en QGIS:

1. **Abrir el proyecto** con *Capa → Añadir capa vectorial* y cargar:
   - `geo/processed/sgc_amenaza.geojson` (polígonos de amenaza)
   - `geo/processed/sgc_piroclastos.geojson` (líneas de influencia)
   - `geo/processed/sgc_volcan_punto.geojson` (cráter)

2. **Chequear coherencia espacial**:
   - El punto del cráter debe caer en `2.313889, -76.397222` (aprox).
   - Los 4 polígonos de amenaza (Alta/Media/Baja/Lahar) deben contener al cráter.
   - Las líneas de piroclastos deben irradiar desde el cráter.

3. **Verificar campos**: `AMENAZA` (Alta/Media/Baja), `FENOMENOS` (p. ej. Lahar),
   `VOLCAN` (Puracé).

4. **Estilo sugerido**:
   - ALTA → rojo intenso, MEDIA → naranja, BAJA → amarillo, Lahar → rojo oscuro con
     rayado. Tip: *Estilos → Categorizado* sobre el campo `AMENAZA`.

5. Si se detectan desviaciones >100 m respecto al cráter de referencia, revisar el
   CRS del pipeline (`EPSG:4686 → EPSG:4326` en `normalizar.py`).

---

## 5. Proyecto QGIS maestro

Abrir `qgis/proyectos/purace_base.qgz` (se crea en el paso 6) y cargar las capas
de `geo/processed/purace__*__clip_sandbox_15km.geojson` como base táctica.

Simbología sugerida:

| Capa | Color | Uso |
|---|---|---|
| dane_departamentos | gris claro | contexto |
| dane_municipios | azul pálido | límites |
| dane_veredas | amarillo suave | desagregación |
| dane_cabeceras | punto morado | cabeceras |
| anillos (gpkg) | rojo 5km / naranja 15km / verde 30km | zonificación |
| sgc_amenaza | rojo ALTA / naranja MEDIA / amarillo BAJA | amenaza |
| sgc_piroclastos | línea naranja punteada | influencia piroclastos |
| sgc_volcan_punto | estrella roja | cráter |

---

## 6. Checklist de entrega Sprint 1

- [ ] `pipeline/*.py` + `config/regiones.yaml` en el repo
- [ ] `geo/raw/`: DANE 4 capas + vectores SGC + PDF referencia + anillos GPKG
- [ ] `geo/processed/`: capas EPSG:4326 + recortes 5/15/30 km + `index.json`
- [ ] `geo/downloads/`: GPX + KML por anillo (incl. SGC)
- [ ] Vectores SGC validados en QGIS (coherencia cráter)
- [ ] Proyecto `purace_base.qgz` creado
- [ ] Capas cargadas y validadas visualmente en QGIS
