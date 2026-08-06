#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exportar_geojson.py - Copia las capas finales a geo/processed con nombres
canónicos para publicación web (Leaflet/Cesium) y genera el índice de
metadatos (geo/index.json).

Nombres de salida (estructura lista a escalar):
    <region>__<capa>__<anillo>.geojson    (ej: purace__dane_municipios__clip_sandbox_5km.geojson)

Uso:
    python exportar_geojson.py [--region purace]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

try:
    from osgeo import gdal
    HAS_GDAL = True
except ImportError:  # pragma: no cover
    HAS_GDAL = False


def _info_capa(path: Path) -> dict:
    gdal.UseExceptions()
    ds = gdal.OpenEx(str(path), gdal.OF_VECTOR)
    layer = ds.GetLayer(0)
    info = {
        "nombre": layer.GetName(),
        "features": layer.GetFeatureCount(),
        "crs": layer.GetSpatialRef().GetAuthorityCode(None)
        if layer.GetSpatialRef() else None,
        "extent": layer.GetExtent(),
        "tamanio_bytes": path.stat().st_size,
        "modificado": path.stat().st_mtime,
    }
    ds = None
    return info


def exportar(region: dict) -> list[Path]:
    region_id = region["id"]
    geo_processed = common.ruta_region(region, "geo_processed")
    geo_processed.mkdir(parents=True, exist_ok=True)

    exportados: list[Path] = []
    indice: list[dict] = []
    prefix = f"{region_id}__"
    for capa in sorted(geo_processed.glob("*.geojson")):
        # Solo recortes (contienen "__") que aún no tengan prefijo de región
        if "__" not in capa.name or capa.name.startswith(prefix):
            continue
        # Renombrar a nombre canónico <region>__<capa>__<anillo>.geojson
        # (evita duplicados entre versiones)
        nuevo = geo_processed / f"{prefix}{capa.name}"
        if nuevo.exists():
            nuevo.unlink()
        capa.rename(nuevo)
        try:
            info = _info_capa(nuevo)
            info["archivo"] = nuevo.name
            indice.append(info)
            exportados.append(nuevo)
            common.log.ok(f"{nuevo.name} -> {info['features']} features")
        except Exception as exc:  # noqa: BLE001
            common.log.warning(f"Metadatos {nuevo.name}: {exc}")

    if indice:
        indice_path = geo_processed / "index.json"
        indice_path.write_text(
            json.dumps({
                "region": region_id,
                "generado": datetime.now().isoformat(),
                "capas": indice,
            }, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        common.log.ok(f"Índice de capas en {indice_path}")
    return exportados


def main() -> None:
    ap = argparse.ArgumentParser(description="Exportar capas finales a GeoJSON")
    ap.add_argument("--region", default="purace")
    args = ap.parse_args()

    region = common.obtener_region(args.region)
    exportar(region)


if __name__ == "__main__":
    main()
