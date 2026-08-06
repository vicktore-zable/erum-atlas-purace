#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
descargar_sgc.py - Adquisición de la amenaza volcánica Puracé (SGC).

Extrae los vectores oficiales del ArcGIS Server del SGC (grupo Puracé)
vía MapServer/query. NOTA: el FeatureServer query falla (400), por eso se
usa el MapServer, que devuelve los features completos sin paginación.

Capas extraídas (geo/raw/):
    sgc_amenaza.geojson          - polígonos de amenaza (Alta/Media/Baja/Lahar)
    sgc_volcan_punto.geojson     - punto del cráter
    sgc_piroclastos.geojson      - polilíneas de influencia piroclastos

Además descarga el PDF oficial como documento de referencia
(no se digitaliza: el vector ya es oficial).

Uso:
    python descargar_sgc.py [--region purace]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402
import geo_fuentes  # noqa: E402


def _query_arcgis(url_base: str, out_sr: int = 4326) -> dict:
    """Consulta un feature layer del MapServer y devuelve features GeoJSON."""
    qs = urllib.parse.urlencode({
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": out_sr,
        "f": "pjson",
    })
    url = f"{url_base}/query?{qs}"
    common.log.info(f"Consultando {url_base.split('/')[-1]}")
    ultimo_error = None
    for intento in range(1, 4):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "ERUM-Atlas/1.0 (pipeline QGIS)"})
            with urllib.request.urlopen(req, timeout=240) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if "error" in data:
                raise RuntimeError(f"ArcGIS error: {data['error']}")
            return data
        except Exception as exc:  # noqa: BLE001
            ultimo_error = exc
            common.log.warning(f"  intento {intento}: {exc}")
            time.sleep(3 * intento)
    raise RuntimeError(f"No se pudo consultar {url}: {ultimo_error}")


def _esri_geometry_a_geojson(geom: dict) -> dict:
    """Convierte geometría ESRI JSON a GeoJSON."""
    gtype = geom.get("geometryType") or (geom.get("rings") and "esriGeometryPolygon"
                                         or geom.get("paths") and "esriGeometryPolyline"
                                         or geom.get("x") is not None and "esriGeometryPoint")
    if "rings" in geom:
        return {"type": "Polygon", "coordinates": geom["rings"]}
    if "paths" in geom:
        return {"type": "MultiLineString", "coordinates": geom["paths"]}
    if "x" in geom and "y" in geom:
        return {"type": "Point", "coordinates": [geom["x"], geom["y"]]}
    raise ValueError(f"Geometría ESRI no soportada: {list(geom.keys())}")


def _guardar_geojson(datos: dict, destino: Path) -> int:
    """Convierte respuesta de query a FeatureCollection GeoJSON."""
    features = []
    for f in datos.get("features", []):
        attrs = f.get("attributes", {})
        props = {k: v for k, v in attrs.items()}
        geom_esri = f.get("geometry")
        gj_geom = _esri_geometry_a_geojson(geom_esri) if geom_esri else None
        features.append({"type": "Feature",
                         "properties": props,
                         "geometry": gj_geom})
    fc = {"type": "FeatureCollection", "features": features}
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    return len(features)


def descargar_sgc(region: dict) -> list[Path]:
    geo_raw = common.ruta_region(region, "geo_raw")
    geo_raw.mkdir(parents=True, exist_ok=True)

    resultado: list[Path] = []
    for fid in ("sgc_amenaza", "sgc_volcan_punto", "sgc_piroclastos"):
        fuente = geo_fuentes.obtener_fuente(fid)
        destino = geo_raw / f"{fuente['salida']}.geojson"
        try:
            datos = _query_arcgis(fuente["url_base"])
            n = _guardar_geojson(datos, destino)
            common.log.ok(f"{destino.name}: {n} features")
            resultado.append(destino)
        except Exception as exc:  # noqa: BLE001
            common.log.error(f"Falló {fid}: {exc}")

    # PDF como documento de referencia (no se digitaliza)
    pdf = geo_raw / "sgc_amenaza_purace.pdf"
    try:
        from geo_fuentes import obtener_fuente  # noqa: PLC0415
        # URL manual (referencia documental)
        common.descargar(
            "https://www2.sgc.gov.co/sgc/volcanes/VolcanPurace/Documents/"
            "Mapa_Amenaza_Purace_V1.pdf", pdf)
    except Exception as exc:  # noqa: BLE001
        common.log.warning(f"PDF de referencia no descargado: {exc}")

    return resultado


def main() -> None:
    ap = argparse.ArgumentParser(description="Descarga SGC amenaza Puracé")
    ap.add_argument("--region", default="purace")
    args = ap.parse_args()

    region = common.obtener_region(args.region)
    descargar_sgc(region)


if __name__ == "__main__":
    main()
