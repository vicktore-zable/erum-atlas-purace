#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
descargar_hidrologia.py - Descarga hidrografía de OpenStreetMap vía Overpass.

Descarga del bbox de Puracé:
  - waterway=river / waterway=stream / waterway=canal (ríos, quebradas, canales)
  - natural=spring (fuentes hídricas)
  - natural=water (cuerpos de agua: lagos, embalses, etc.)
  - waterway=dam / man_made=dam (represas)

Incluye lógica de reintentos con backoff exponencial para manejar
rate-limits del servidor Overpass (429/504).

Salida:
  geo/raw/overpass_waterways.geojson  (ríos + quebradas + canales)
  geo/raw/overpass_springs.geojson    (fuentes)
  geo/raw/overpass_waterbodies.geojson (cuerpos de agua)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "ERUM-Atlas/1.0 (purace hydrography pipeline)"
TIMEOUT_REQ = 120


def _bbox_overpass(region: dict, margen_km: float = 30.0) -> str:
    """Devuelve bbox string 'south,west,north,east' con margen extra."""
    sb = region["sandbox"]
    import math
    k = 111000.0
    lat_center = (sb["south"] + sb["north"]) / 2
    dlat = margen_km * 1000 / k
    dlon = margen_km * 1000 / (k * math.cos(lat_center * math.pi / 180))
    return (f"{round(sb['south'] - dlat, 2)},{round(sb['west'] - dlon, 2)},"
            f"{round(sb['north'] + dlat, 2)},{round(sb['east'] + dlon, 2)}")


def _query_overpass(ql: str, retries: int = 5) -> dict | None:
    """Envía query Overpass con reintentos y backoff exponencial."""
    data = urllib.parse.urlencode({"data": ql}).encode("utf-8")
    for intento in range(1, retries + 1):
        try:
            common.log.info(f"Overpass [{intento}/{retries}]...")
            req = urllib.request.Request(
                OVERPASS_URL, data=data,
                headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT_REQ) as resp:
                raw = resp.read()
            result = json.loads(raw)
            nelems = len(result.get("elements", []))
            common.log.ok(f"Overpass: {nelems} elementos")
            return result
        except urllib.error.HTTPError as exc:
            common.log.warning(f"HTTP {exc.code}: {exc.reason}")
            if exc.code == 429:
                wait = 30 * intento  # rate limit: 30s, 60s, 90s...
                common.log.info(f"Rate limit: esperando {wait}s...")
                time.sleep(wait)
            elif exc.code >= 500:
                time.sleep(10 * intento)
            else:
                return None
        except Exception as exc:
            common.log.warning(f"Error Overpass: {exc}")
            time.sleep(5 * intento)
    common.log.error("Overpass agotó reintentos")
    return None


def _elem_a_feature(elem: dict, tags_key: str = "tags") -> dict:
    """Convierte un elemento Overpass a GeoJSON Feature."""
    tags = elem.get(tags_key, {})
    geom = None
    if elem["type"] == "node":
        geom = {"type": "Point", "coordinates": [elem["lon"], elem["lat"]]}
    elif elem["type"] == "way" and "geometry" in elem:
        coords = [[n["lon"], n["lat"]] for n in elem["geometry"]]
        if len(coords) >= 2:
            geom = {"type": "LineString", "coordinates": coords}
    elif elem["type"] == "relation" and "members" in elem:
        # Relations: concatenar ways miembros en un MultiLineString
        lines = []
        for mem in elem["members"]:
            if mem["type"] == "way" and "geometry" in mem:
                coords = [[n["lon"], n["lat"]] for n in mem["geometry"]]
                if len(coords) >= 2:
                    lines.append(coords)
        if lines:
            geom = {"type": "MultiLineString", "coordinates": lines}
    if geom is None:
        return None
    props = {"osm_id": elem["id"], "osm_type": elem["type"]}
    for k, v in tags.items():
        if k.startswith("osm_"):
            continue
        props[k] = str(v) if v is not None else None
    return {"type": "Feature", "geometry": geom, "properties": props}


def _guardar_geojson(features: list[dict], path: Path, nombre: str):
    fc = {"type": "FeatureCollection", "features": features}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fc, ensure_ascii=False, indent=1), encoding="utf-8")
    common.log.ok(f"{nombre}: {len(features)} features → {path.name}")


def descargar_waterways(bbox: str, region: dict) -> Path:
    """Ríos, quebradas y canales."""
    ql = f"""
[out:json][timeout:90][bbox:{bbox}];
(
  way["waterway"="river"];
  way["waterway"="stream"];
  way["waterway"="canal"];
  relation["waterway"="river"];
);
out geom;
"""
    result = _query_overpass(ql)
    if not result:
        return None
    features = []
    for elem in result.get("elements", []):
        feat = _elem_a_feature(elem)
        if feat:
            features.append(feat)
    out = common.ruta_region(region, "geo_raw") / "overpass_waterways.geojson"
    _guardar_geojson(features, out, "Waterways OSM")
    return out


def descargar_springs(bbox: str, region: dict) -> Path:
    """Fuentes hídricas (manantiales)."""
    ql = f"""
[out:json][timeout:60][bbox:{bbox}];
(
  node["natural"="spring"];
  way["natural"="spring"];
);
out body;
"""
    result = _query_overpass(ql)
    if not result:
        return None
    features = []
    for elem in result.get("elements", []):
        feat = _elem_a_feature(elem)
        if feat:
            features.append(feat)
    out = common.ruta_region(region, "geo_raw") / "overpass_springs.geojson"
    _guardar_geojson(features, out, "Fuentes hídricas OSM")
    return out


def descargar_waterbodies(bbox: str, region: dict) -> Path:
    """Cuerpos de agua (lagos, embalses, etc.)."""
    ql = f"""
[out:json][timeout:60][bbox:{bbox}];
(
  way["natural"="water"];
  relation["natural"="water"];
  way["water"="reservoir"];
  way["water"="lake"];
  way["water"="pond"];
);
out geom;
"""
    result = _query_overpass(ql)
    if not result:
        return None
    features = []
    for elem in result.get("elements", []):
        feat = _elem_a_feature(elem)
        if feat:
            features.append(feat)
    out = common.ruta_region(region, "geo_raw") / "overpass_waterbodies.geojson"
    _guardar_geojson(features, out, "Cuerpos de agua OSM")
    return out


def main():
    ap = argparse.ArgumentParser(description="Descarga hidrografía OSM (Overpass)")
    ap.add_argument("--region", default="purace")
    ap.add_argument("--margen", type=float, default=30.0,
                    help="Margen extra km sobre el sandbox (default: 30)")
    args = ap.parse_args()

    region = common.obtener_region(args.region)
    bbox = _bbox_overpass(region, args.margen)
    common.log.info(f"BBox Overpass: {bbox}")

    time.sleep(5)  # Brief pause before first query
    common.log.info("=== Descargando waterways ===")
    descargar_waterways(bbox, region)
    time.sleep(5)

    common.log.info("=== Descargando springs ===")
    descargar_springs(bbox, region)
    time.sleep(5)

    common.log.info("=== Descargando waterbodies ===")
    descargar_waterbodies(bbox, region)

    common.log.ok("Hidrografía OSM descargada")


if __name__ == "__main__":
    main()
