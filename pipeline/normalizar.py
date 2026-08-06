#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normalizar.py - Normalización de capas a EPSG:4326 + limpieza de geometrías.

Funciones:
  - normalizar_capa(entrada, salida, epsg_origen, epsg_destino=4326)
      Reproyecta, elimina geometrías nulas/vacías, repara inválidas.
  - generar_anillos(region)
      Crea los buffers 5/15/30 km alrededor del cráter como capa de
      referencia (geometrías circulares en 4326).

Uso:
    python normalizar.py [--region purace] [--capa dane_municipios]
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

try:
    from osgeo import gdal, ogr, osr
    HAS_GDAL = True
except ImportError:  # pragma: no cover
    HAS_GDAL = False


def _epsg(codigo: int):
    """Crea un SpatialReference para EPSG."""
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(codigo)
    return srs


def normalizar_capa(entrada: Path, salida: Path,
                    epsg_origen: int | None = None,
                    epsg_destino: int = 4326) -> Path | None:
    """Reproyecta y limpia una capa vectorial. Devuelve la salida o None."""
    if not HAS_GDAL:
        common.log.error("osgeo (GDAL) no disponible. Usa el Python de QGIS.")
        return None
    if not entrada.exists():
        common.log.error(f"No existe {entrada}")
        return None

    gdal.UseExceptions()
    ds_in = gdal.OpenEx(str(entrada), gdal.OF_VECTOR)
    if ds_in is None:
        common.log.error(f"No se pudo abrir {entrada} con GDAL")
        return None

    layer = ds_in.GetLayer(0)
    src_srs = layer.GetSpatialRef()
    if src_srs is None and epsg_origen:
        src_srs = _epsg(epsg_origen)
    if src_srs is None:
        common.log.warning(f"{entrada.name}: sin CRS de origen; se asume "
                           f"EPSG:{epsg_origen or 4326}")
        src_srs = _epsg(epsg_origen or 4326)

    dst_srs = _epsg(epsg_destino)
    ctf = osr.CoordinateTransformation(src_srs, dst_srs)

    salida.parent.mkdir(parents=True, exist_ok=True)
    drv = ogr.GetDriverByName("GeoJSON")
    ds_out = drv.CreateDataSource(str(salida))
    # Copiar esquema de capa
    out_layer = ds_out.CreateLayer(
        layer.GetName(), dst_srs, layer.GetGeomType()
    )
    ldef = layer.GetLayerDefn()
    for i in range(ldef.GetFieldCount()):
        fdef = ldef.GetFieldDefn(i)
        out_layer.CreateField(fdef)

    cont_in, cont_out, cont_invalidos = 0, 0, 0
    for feat in layer:
        cont_in += 1
        geom = feat.GetGeometryRef()
        if geom is None or geom.IsEmpty():
            continue
        if src_srs.GetAuthorityCode(None) and int(src_srs.GetAuthorityCode(None)) != epsg_destino:
            geom.Transform(ctf)
        if not geom.IsValid():
            geom = geom.MakeValid()
            cont_invalidos += 1
        if geom is None or geom.IsEmpty():
            continue
        new_feat = ogr.Feature(out_layer.GetLayerDefn())
        for i in range(ldef.GetFieldCount()):
            new_feat.SetField(i, feat.GetField(i))
        new_feat.SetGeometry(geom)
        out_layer.CreateFeature(new_feat)
        cont_out += 1
        new_feat = None

    ds_in = None
    ds_out = None
    common.log.ok(f"{entrada.name}: {cont_out}/{cont_in} features "
                  f"(reparadas={cont_invalidos}) -> {salida.name}")
    if cont_out == 0:
        salida.unlink(missing_ok=True)
        return None
    return salida


def _punto_en_epsg(lat: float, lon: float, epsg: int):
    """Crea un punto WKT en el EPSG dado a partir de lat/lon (WGS84)."""
    src = osr.SpatialReference()
    src.ImportFromEPSG(4326)
    dst = osr.SpatialReference()
    dst.ImportFromEPSG(epsg)
    ctf = osr.CoordinateTransformation(src, dst)
    x, y, _ = ctf.TransformPoint(lon, lat)
    pt = ogr.Geometry(ogr.wkbPoint)
    pt.AddPoint(x, y)
    return pt


def generar_anillos(region: dict) -> Path | None:
    """Crea buffers de radio 5/15/30 km alrededor del cráter en un GeoPackage."""
    if not HAS_GDAL:
        common.log.error("osgeo no disponible.")
        return None

    crat = region["crater"]
    epsg_proj = region.get("epsg_proyeccion_local", 3116)
    geo_raw = common.ruta_region(region, "geo_raw")
    geo_raw.mkdir(parents=True, exist_ok=True)
    salida = geo_raw / "referencia_anillos.gpkg"

    drv = ogr.GetDriverByName("GPKG")
    if salida.exists():
        drv.DeleteDataSource(str(salida))
    ds = drv.CreateDataSource(str(salida))

    # Capa de puntos de referencia
    src = osr.SpatialReference(); src.ImportFromEPSG(4326)
    pt_layer = ds.CreateLayer("puntos_referencia", src, ogr.wkbPoint)
    pt_layer.CreateField(ogr.FieldDefn("nombre", ogr.OFTString))
    for pr in region.get("puntos_referencia", []):
        f = ogr.Feature(pt_layer.GetLayerDefn())
        g = ogr.Geometry(ogr.wkbPoint)
        g.AddPoint(pr["lon"], pr["lat"])
        f.SetGeometry(g)
        f.SetField("nombre", pr["nombre"])
        pt_layer.CreateFeature(f)

    # Capa de anillos (buffers reproyectados a 4326)
    anillos_srs = _epsg(4326)
    ring_layer = ds.CreateLayer("anillos_km", anillos_srs, ogr.wkbPolygon)
    ring_layer.CreateField(ogr.FieldDefn("radio_km", ogr.OFTReal))
    ring_layer.CreateField(ogr.FieldDefn("nombre", ogr.OFTString))
    ring_layer.CreateField(ogr.FieldDefn("uso", ogr.OFTString))

    centro_proj = _punto_en_epsg(crat["lat"], crat["lon"], epsg_proj)
    for anillo in region["anillos"]:
        buf = centro_proj.Buffer(anillo["radio_km"] * 1000.0, 64)
        buf.Transform(osr.CoordinateTransformation(
            _epsg(epsg_proj), anillos_srs))
        f = ogr.Feature(ring_layer.GetLayerDefn())
        f.SetGeometry(buf)
        f.SetField("radio_km", float(anillo["radio_km"]))
        f.SetField("nombre", anillo["nombre"])
        f.SetField("uso", anillo["uso"])
        ring_layer.CreateFeature(f)

    ds = None
    common.log.ok(f"Anillos generados en {salida}")
    return salida


def main() -> None:
    ap = argparse.ArgumentParser(description="Normalizar capas a EPSG:4326")
    ap.add_argument("--region", default="purace")
    ap.add_argument("--capa", default=None,
                    help="ID de fuente (ej: dane_municipios). Por defecto todas.")
    args = ap.parse_args()

    region = common.obtener_region(args.region)
    geo_raw = common.ruta_region(region, "geo_raw")
    geo_processed = common.ruta_region(region, "geo_processed")
    geo_processed.mkdir(parents=True, exist_ok=True)

    import geo_fuentes  # noqa: PLC0415
    ids = [args.capa] if args.capa else geo_fuentes.listar_fuentes()
    for fid in ids:
        fuente = geo_fuentes.obtener_fuente(fid)
        if fuente["formato"] == "pdf":
            continue
        entrada = geo_raw / f"{fuente['salida']}.geojson"
        salida = geo_processed / f"{fuente['salida']}.geojson"
        normalizar_capa(entrada, salida, epsg_origen=fuente.get("crs_origen"))


if __name__ == "__main__":
    main()
