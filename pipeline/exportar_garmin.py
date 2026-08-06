#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exportar_garmin.py - Exportación de capas para GPS Garmin (GPX) y KML.

Convierte capas a GPX (waypoints/rutas/tracks según tipo de geometría,
soportando capas mixtas) y a KML para Google Earth / campo.

Salidas (en geo/downloads/):
    <capa>.gpx
    <capa>.kml

Uso:
    python exportar_garmin.py [--region purace] [--formato gpx,kml]
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


def _es_punto(gt: int) -> bool:
    return gt in (ogr.wkbPoint, ogr.wkbPoint25D,
                  ogr.wkbMultiPoint, ogr.wkbMultiPoint25D)


def _es_linea(gt: int) -> bool:
    return gt in (ogr.wkbLineString, ogr.wkbLineString25D,
                  ogr.wkbMultiLineString, ogr.wkbMultiLineString25D)


def _es_poligono(gt: int) -> bool:
    return gt in (ogr.wkbPolygon, ogr.wkbPolygon25D,
                  ogr.wkbMultiPolygon, ogr.wkbMultiPolygon25D)


def _layer_gpx_nombre(gt: int) -> str:
    if _es_punto(gt):
        return "waypoints"
    if _es_linea(gt):
        return "tracks"
    return "waypoints"  # fallback


def _convertir_gpx(entrada: Path, salida: Path) -> bool:
    """Convierte a GPX manejando capas mixtas (puntos/rutas/tracks)."""
    gdal.UseExceptions()
    ds_in = gdal.OpenEx(str(entrada), gdal.OF_VECTOR)
    layer = ds_in.GetLayer(0)
    srs = layer.GetSpatialRef()
    ldef = layer.GetLayerDefn()

    drv = ogr.GetDriverByName("GPX")
    salida.parent.mkdir(parents=True, exist_ok=True)
    if salida.exists():
        drv.DeleteDataSource(str(salida))
    ds_out = drv.CreateDataSource(str(salida))
    if ds_out is None:
        ds_in = None
        return False

    # El driver GPX requiere capas con nombres específicos.
    # waypoints -> Punto; tracks -> MultiLineString (soporta varias líneas)
    capas = {}
    c = ds_out.CreateLayer("waypoints", srs, ogr.wkbPoint)
    c.CreateField(ogr.FieldDefn("name", ogr.OFTString))
    c.CreateField(ogr.FieldDefn("desc", ogr.OFTString))
    capas["waypoints"] = c
    c = ds_out.CreateLayer("tracks", srs, ogr.wkbMultiLineString)
    c.CreateField(ogr.FieldDefn("name", ogr.OFTString))
    c.CreateField(ogr.FieldDefn("desc", ogr.OFTString))
    capas["tracks"] = c

    for feat in layer:
        geom = feat.GetGeometryRef()
        if geom is None:
            continue
        gtype = geom.GetGeometryType()
        if _es_punto(gtype):
            target = "waypoints"
            g_final = geom.Clone()
        elif _es_poligono(gtype):
            # Garmin no soporta polígonos: usar centroide como waypoint
            target = "waypoints"
            g_final = geom.Centroid()
        elif _es_linea(gtype):
            target = "tracks"
            # Normalizar a MultiLineString (el driver GPX exige ese tipo)
            if gtype in (ogr.wkbLineString, ogr.wkbLineString25D):
                g_final = ogr.Geometry(ogr.wkbMultiLineString)
                g_final.AddGeometry(geom.Clone())
            else:
                g_final = geom.Clone()
        else:
            continue
        nf = ogr.Feature(capas[target].GetLayerDefn())
        nombre = feat.GetField(0) if ldef.GetFieldCount() else None
        nf.SetField("name", str(nombre) if nombre is not None else "")
        nf.SetGeometry(g_final)
        capas[target].CreateFeature(nf)
        nf = None

    ds_in = None
    ds_out = None
    return True


def _convertir_kml(entrada: Path, salida: Path) -> bool:
    gdal.UseExceptions()
    driver = ogr.GetDriverByName("KML")
    ds_in = gdal.OpenEx(str(entrada), gdal.OF_VECTOR)
    layer = ds_in.GetLayer(0)
    salida.parent.mkdir(parents=True, exist_ok=True)
    if salida.exists():
        driver.DeleteDataSource(str(salida))
    ds_out = driver.CreateDataSource(str(salida))
    if ds_out is None:
        ds_in = None
        return False
    out_layer = ds_out.CreateLayer(layer.GetName(), layer.GetSpatialRef(),
                                   layer.GetGeomType())
    ldef = layer.GetLayerDefn()
    for i in range(ldef.GetFieldCount()):
        out_layer.CreateField(ldef.GetFieldDefn(i))
    for feat in layer:
        out_layer.CreateFeature(feat)
    ds_in = None
    ds_out = None
    return True


def exportar(region: dict, formatos: list[str]) -> list[Path]:
    geo_processed = common.ruta_region(region, "geo_processed")
    downloads = common.ruta_region(region, "geo_downloads")
    downloads.mkdir(parents=True, exist_ok=True)

    resultados: list[Path] = []
    prefix = f"{region['id']}__"
    for capa in sorted(geo_processed.glob("*.geojson")):
        # Solo recortes canónicos (prefijo región, con "__"); evita duplicados
        if not capa.name.startswith(prefix) or "__" not in capa.name:
            continue
        for fmt in formatos:
            ext = "gpx" if fmt == "gpx" else "kml"
            salida = downloads / f"{capa.stem}.{ext}"
            ok = (_convertir_gpx(capa, salida) if fmt == "gpx"
                  else _convertir_kml(capa, salida))
            if ok and salida.exists() and salida.stat().st_size > 0:
                common.log.ok(f"{salida.name}")
                resultados.append(salida)
            else:
                salida.unlink(missing_ok=True)
    return resultados


def main() -> None:
    ap = argparse.ArgumentParser(description="Exportar GPX/KML para Garmin")
    ap.add_argument("--region", default="purace")
    ap.add_argument("--formato", default="gpx,kml")
    args = ap.parse_args()

    region = common.obtener_region(args.region)
    formatos = [f.strip().lower() for f in args.formato.split(",")]
    exportar(region, formatos)


if __name__ == "__main__":
    main()
