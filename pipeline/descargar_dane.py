#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
descargar_dane.py - Adquisición automática de datos DANE (MGN/DIVIPOLA).

Sprint 1: descarga los ZIP de GeoJSON oficiales del geoportal DANE
(vigencia 2025 MGN, 2024 veredas), los descomprime a geo/raw/ y genera
un GeoJSON recortado a la región (bbox del sandbox) cuando aplica.

Uso:
    python descargar_dane.py [--region purace] [--solo municipio,vereda]

Salidas (en geo/raw/):
    dane_departamentos.geojson
    dane_municipios.geojson
    dane_veredas.geojson
    dane_cabeceras.geojson
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

# Permitir importar common/geo_fuentes desde este directorio
sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402
import geo_fuentes  # noqa: E402

ORDEN = ["dane_mgn_departamento", "dane_mgn_municipio",
         "dane_mgn_vereda", "dane_mgn_cabecera"]


def _extraer_geojson_zip(zip_path: Path, miembro: str | None,
                         destino: Path) -> Path | None:
    """Extrae el .geojson de un zip del DANE y lo deja en destino."""
    with zipfile.ZipFile(zip_path) as zf:
        nombres = zf.namelist()
        geojsons = [n for n in nombres if n.lower().endswith(".geojson")]
        if miembro and miembro in nombres:
            elegido = miembro
        elif geojsons:
            elegido = geojsons[0]
        else:
            common.log.warning(f"Sin .geojson en {zip_path.name}: {nombres}")
            return None
        with zf.open(elegido) as src, open(destino, "wb") as out:
            shutil.copyfileobj(src, out)
    return destino


def _filtrar_por_bbox(path: Path, bbox: dict) -> Path | None:
    """Deja solo features dentro del bbox (para capas nacionales grandes)."""
    try:
        with open(path, encoding="utf-8") as fh:
            gj = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        common.log.warning(f"No se pudo leer {path.name}: {exc}")
        return None

    w, s, e, n = bbox["west"], bbox["south"], bbox["east"], bbox["north"]
    features = gj.get("features", [])
    dentro = []
    for f in features:
        geom = f.get("geometry")
        if not geom:
            continue
        # Bbox de la geometría (simple, soporta Point/LineString/Polygon)
        coords = geom.get("coordinates")
        c = coords[0] if geom.get("type") in ("LineString", "Polygon",
                                               "MultiPoint") and coords \
            else coords
        # Recorrido genérico para extraer todos los pares lon/lat
        lons, lats = [], []
        def recorrer(o):
            if isinstance(o, (int, float)):
                return
            if isinstance(o, list):
                if len(o) >= 2 and all(isinstance(v, (int, float)) for v in o[:2]):
                    lons.append(o[0]); lats.append(o[1])
                else:
                    for item in o:
                        recorrer(item)
        recorrer(coords)
        if not lons:
            continue
        if (max(lons) >= w and min(lons) <= e and
                max(lats) >= s and min(lats) <= n):
            dentro.append(f)

    if len(dentro) == len(features):
        return path  # ya todo dentro
    gj["features"] = dentro
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(gj, fh, ensure_ascii=False)
    common.log.info(f"{path.name}: {len(dentro)}/{len(features)} features "
                    f"dentro del sandbox")
    return path


def descargar_dane(region: dict, solo: list[str] | None = None) -> list[Path]:
    bbox = region["sandbox"]
    geo_raw = common.ruta_region(region, "geo_raw")
    geo_raw.mkdir(parents=True, exist_ok=True)

    ids = [f for f in ORDEN if solo is None or f in solo]
    resultados: list[Path] = []
    for fid in ids:
        fuente = geo_fuentes.obtener_fuente(fid)
        zip_tmp = geo_raw / f"{fuente['salida']}_descarga.zip"
        destino = geo_raw / f"{fuente['salida']}.geojson"
        try:
            common.descargar(fuente["url"], zip_tmp)
            ok = _extraer_geojson_zip(zip_tmp, fuente.get("zip_miembro_geojson"),
                                      destino)
            zip_tmp.unlink(missing_ok=True)
            if ok:
                _filtrar_por_bbox(destino, bbox)
                resultados.append(destino)
        except Exception as exc:  # noqa: BLE001
            common.log.warning(f"Falló {fid}: {exc}")
            common.log.warning(
                "Si la descarga falla, baja manualmente el GeoJSON desde "
                "https://geoportal.dane.gov.co/servicios/descarga-y-metadatos/"
                "datos-geoestadisticos/ y colócalo en geo/raw/."
            )
    return resultados


def main() -> None:
    ap = argparse.ArgumentParser(description="Descarga DANE MGN (ZIP GeoJSON)")
    ap.add_argument("--region", default="purace")
    ap.add_argument("--solo", default=None,
                    help="IDs separados por coma (municipio,vereda)")
    args = ap.parse_args()

    region = common.obtener_region(args.region)
    common.log.info(f"Región: {region['nombre']} "
                    f"bbox={region['sandbox']}")
    solo = [s.strip() for s in args.solo.split(",")] if args.solo else None
    descargar_dane(region, solo)


if __name__ == "__main__":
    main()
