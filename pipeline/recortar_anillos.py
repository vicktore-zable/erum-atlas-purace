#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
recortar_anillos.py - Recorte de capas a los anillos operativos (5/15/30 km).

Usa los buffers de geo/raw/referencia_anillos.gpkg (generados por
normalizar.generar_anillos) para recortar cada capa normalizada.

Salidas (en geo/processed/):
    <capa>__clip_sandbox_5km.geojson
    <capa>__clip_sandbox_15km.geojson
    <capa>__clip_sandbox_30km.geojson

Uso:
    python recortar_anillos.py [--region purace] [--capa dane_municipios]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

try:
    from osgeo import gdal, ogr
    HAS_GDAL = True
except ImportError:  # pragma: no cover
    HAS_GDAL = False


def _clip_por_anillo(capa: Path, anillo: ogr.Geometry, salida: Path) -> int:
    """Recorta una capa por la geometría del anillo. Devuelve nº features."""
    gdal.UseExceptions()
    ds_in = gdal.OpenEx(str(capa), gdal.OF_VECTOR)
    layer = ds_in.GetLayer(0)
    srs = layer.GetSpatialRef()

    salida.parent.mkdir(parents=True, exist_ok=True)
    drv = ogr.GetDriverByName("GeoJSON")
    ds_out = drv.CreateDataSource(str(salida))
    out_layer = ds_out.CreateLayer(layer.GetName(), srs, layer.GetGeomType())
    ldef = layer.GetLayerDefn()
    for i in range(ldef.GetFieldCount()):
        out_layer.CreateField(ldef.GetFieldDefn(i))

    if layer.GetGeometryColumn():
        clip = anillo
    else:
        clip = anillo

    n = 0
    for feat in layer:
        geom = feat.GetGeometryRef()
        if geom is None:
            continue
        inter = geom.Intersection(clip)
        if inter is None or inter.IsEmpty():
            continue
        new_feat = ogr.Feature(out_layer.GetLayerDefn())
        for i in range(ldef.GetFieldCount()):
            new_feat.SetField(i, feat.GetField(i))
        new_feat.SetGeometry(inter)
        out_layer.CreateFeature(new_feat)
        n += 1
    ds_in = None
    ds_out = None
    return n


def _anillos_desde_gpkg(gpkg: Path) -> list[tuple[str, ogr.Geometry]]:
    gdal.UseExceptions()
    ds = gdal.OpenEx(str(gpkg), gdal.OF_VECTOR)
    layer = ds.GetLayerByName("anillos_km")
    result = []
    for feat in layer:
        nombre = feat.GetField("nombre")
        geom = feat.GetGeometryRef().Clone()
        result.append((nombre, geom))
    ds = None
    return result


def recortar(region: dict, solo_capa: str | None = None) -> list[Path]:
    geo_raw = common.ruta_region(region, "geo_raw")
    geo_processed = common.ruta_region(region, "geo_processed")
    geo_processed.mkdir(parents=True, exist_ok=True)

    gpkg = geo_raw / "referencia_anillos.gpkg"
    if not gpkg.exists():
        common.log.error(f"Falta {gpkg}. Ejecuta primero normalizar.py "
                         f"(genera los anillos).")
        return []
    anillos = _anillos_desde_gpkg(gpkg)

    # Solo capas base normalizadas (sin "__"); evita re-procesar recortes
    capas = sorted(p for p in geo_processed.glob("*.geojson")
                   if "__" not in p.name)
    if solo_capa:
        capas = [c for c in capas if solo_capa in c.name]

    resultados: list[Path] = []
    for capa in capas:
        for nombre, geom in anillos:
            salida = geo_processed / f"{capa.stem}__{nombre}.geojson"
            try:
                n = _clip_por_anillo(capa, geom, salida)
                if n == 0:
                    salida.unlink(missing_ok=True)
                    common.log.warning(f"{capa.name} ∩ {nombre}: sin features")
                else:
                    common.log.ok(f"{capa.name} ∩ {nombre}: {n} features")
                    resultados.append(salida)
            except Exception as exc:  # noqa: BLE001
                common.log.warning(f"Clip {capa.name} {nombre}: {exc}")
    return resultados


def main() -> None:
    ap = argparse.ArgumentParser(description="Recortar capas por anillos")
    ap.add_argument("--region", default="purace")
    ap.add_argument("--capa", default=None)
    args = ap.parse_args()

    region = common.obtener_region(args.region)
    recortar(region, args.capa)


if __name__ == "__main__":
    main()
