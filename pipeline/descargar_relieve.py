#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
descargar_relieve.py - Adquisición de relieve (DEM Copernicus 30m) y curvas de nivel.

Descarga los tiles Copernicus DEM GLO-30 (AWS Open Data, libre y sin clave) que
cubren el sandbox de la región, los fusiona, los recorta al bbox y genera
curvas de nivel con GDAL (intervalos configurables).

Fuente: https://registry.opendata.aws/copernicus-dem/ (DEM GLO-30 Public)
Tile:   s3://copernicus-dem-30m/Copernicus_DSM_COG_10_{LAT}_00_{LON}_00_DEM/
        Copernicus_DSM_COG_10_{LAT}_00_{LON}_00_DEM.tif   (1°x1°)

Uso:
    python descargar_relieve.py --region purace [--intervalo 50] [--maestro 250]

Salidas:
    geo/raw/dem/purace_dem_30m.tif   (DEM recortado al sandbox)
    geo/raw/curvas_50m.shp           (curvas cada intervalo)
    geo/raw/curvas_maestras_250m.shp (curvas maestras cada maestro)
"""
from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

try:
    from osgeo import gdal, ogr
    HAS_GDAL = True
except ImportError:  # pragma: no cover
    HAS_GDAL = False


BASE_URL = ("https://copernicus-dem-30m.s3.amazonaws.com/"
            "Copernicus_DSM_COG_10_{lat}_00_{lon}_00_DEM/"
            "Copernicus_DSM_COG_10_{lat}_00_{lon}_00_DEM.tif")

# Resolución aproximada del DEM Copernicus 30m en grados (global ~0.00027°)
RES_DEG = 0.00027


def _tiles_para_bbox(bbox: dict) -> list[str]:
    """Devuelve los tiles 1°x1° que intersecan el bbox.

    Convención del dataset: el tile N{lat}_W{lon} cubre [lat, lat+1] de latitud
    y [lon-1, lon] de longitud (para longitud negativa Oeste). Es decir, el
    tile lleva la esquina noreste del cuadrado de 1°.
    """
    b = bbox
    tiles: list[str] = []
    # lat: banda [L, L+1] interseca [south, north] con L = floor
    for lat in range(math.floor(b["south"]), math.floor(b["north"]) + 1):
        # lon: banda [-(L+1), -L] interseca [west, east]; etiqueta W{L+1}
        for lon in range(math.floor(-b["east"]), math.floor(-b["west"]) + 1):
            tiles.append(f"N{lat:02d}_W{abs(lon) + 1:03d}")
    return sorted(set(tiles))


def descargar_tile(tile: str, destino: Path) -> bool:
    """Descarga un tile Copernicus DEM con reintentos y DNS-friendly sleep."""
    lat, lon = tile.split("_")
    lon_num = int(lon.replace("W", "").replace("E", ""))
    lon_str = f"W{lon_num:03d}" if lon.startswith("W") else f"E{lon_num:03d}"
    url = BASE_URL.format(lat=lat, lon=lon_str)
    for intento in range(1, 6):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 (ERUM-Atlas pipeline)"})
            with urllib.request.urlopen(req, timeout=300) as resp, \
                    open(destino, "wb") as out:
                shutil.copyfileobj(resp, out)
            if destino.stat().st_size < 1_000_000:
                raise RuntimeError("tile demasiado pequeño")
            common.log.ok(f"DEM tile {tile} ({destino.stat().st_size:,} bytes)")
            return True
        except Exception as exc:  # noqa: BLE001
            common.log.warning(f"tile {tile} intento {intento}/5: {exc}")
            time.sleep(5 * intento)
    return False


def _clase_shp_para_capa(capa: ogr.Layer, shp: Path) -> None:
    """Copia el esquema de un shapefile a otro shapefile (para curvas)."""


def generar_relieve(region: dict, intervalo: int = 50,
                    maestro: int = 250) -> list[Path]:
    """Descarga DEM y genera curvas de nivel. Devuelve las salidas creadas."""
    if not HAS_GDAL:
        common.log.error("osgeo no disponible. Usa el Python de QGIS.")
        return []

    bbox = region["sandbox"]
    geo_raw = common.ruta_region(region, "geo_raw")
    dem_dir = geo_raw / "dem"
    dem_dir.mkdir(parents=True, exist_ok=True)

    salidas: list[Path] = []

    # 1) Tiles Copernicus
    tiles = _tiles_para_bbox(bbox)
    if not tiles:
        common.log.error(f"No hay tiles DEM para el bbox {bbox}")
        return []
    common.log.info(f"Tiles DEM necesarios: {tiles}")
    tiles_ok: list[Path] = []
    for tile in tiles:
        tif = dem_dir / f"{tile}.tif"
        if tif.exists() and tif.stat().st_size > 1_000_000:
            tiles_ok.append(tif)
            continue
        if descargar_tile(tile, tif):
            tiles_ok.append(tif)
    if not tiles_ok:
        common.log.error("Ningún tile DEM se pudo descargar")
        return []

    # 2) Mosaic + warp al sandbox
    vrt = dem_dir / "purace_dem.vrt"
    gdal.BuildVRT(str(vrt), [str(t) for t in tiles_ok])
    dem_rec = dem_dir / "purace_dem_30m.tif"
    if dem_rec.exists():
        dem_rec.unlink()
    w, s, e, n = bbox["west"], bbox["south"], bbox["east"], bbox["north"]
    gdal.Warp(
        str(dem_rec), str(vrt),
        dstSRS="EPSG:4326",
        outputBounds=[w, s, e, n],
        resampleAlg="bilinear",
        xRes=RES_DEG, yRes=RES_DEG,
        dstNodata=-9999,
        creationOptions=["COMPRESS=DEFLATE", "TILED=YES"],
    )
    if not dem_rec.exists():
        common.log.error("Warp del DEM falló")
        return []
    ds = gdal.Open(str(dem_rec))
    band = ds.GetRasterBand(1)
    mn, mx = band.ComputeRasterMinMax()
    common.log.ok(f"DEM {dem_rec.name}: {ds.RasterXSize}x{ds.RasterYSize} "
                  f"rango {round(mn)}–{round(mx)} m")
    ds = None

    # 3) Curvas de nivel
    gdal.UseExceptions()
    curvas = geo_raw / f"curvas_{intervalo}m.shp"
    _generar_contours_flujo(dem_rec, curvas, geo_raw, intervalo)
    salidas.append(curvas)

    # 4) Curvas maestras (cada `maestro` m)
    maestras = geo_raw / f"curvas_maestras_{maestro}m.shp"
    _generar_contours_flujo(dem_rec, maestras, geo_raw, maestro)
    salidas.append(maestras)

    return salidas


def _generar_contours_flujo(dem_rec: Path, shp: Path, geo_raw: Path,
                            intervalo: int) -> None:
    if not _generar_contour_cli(dem_rec, shp, intervalo):
        common.log.warning(f"No se generaron curvas {intervalo}m")


def _limpiar_shp(shp: Path) -> None:
    for suf in [".shp", ".shx", ".dbf", ".prj", ".cpg", ".qpj", ".qix"]:
        p = Path(str(shp) + suf)
        p.unlink(missing_ok=True)


def _generar_contour_cli(dem_tif: Path, shp: Path, intervalo: int) -> bool:
    """Genera curvas de nivel usando el CLI gdal_contour (fiable)."""
    exe = None
    for cand in [
        r"D:/Program Files/QGIS 3.44.7/bin/gdal_contour.exe",
        "gdal_contour",
    ]:
        if shutil.which(cand) or os.path.exists(cand):
            exe = cand
            break
    if exe is None:
        common.log.error("gdal_contour no encontrado")
        return False
    _limpiar_shp(shp)
    cmd = [exe, "-i", str(intervalo), "-a", "ELEV",
           str(dem_tif), str(shp), "-q"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        common.log.error(f"gdal_contour falló: {proc.stderr[-300:]}")
        return False
    _log_curvas(shp, intervalo)
    return True


def _log_curvas(shp: Path, intervalo: int) -> None:
    ds = ogr.Open(str(shp))
    if ds is None:
        common.log.warning(f"No se pudo leer {shp}")
        return
    l = ds.GetLayer(0)
    n = l.GetFeatureCount()
    common.log.ok(f"{shp.name}: {n} curvas cada {intervalo} m")


def main() -> None:
    ap = argparse.ArgumentParser(description="Relieve: DEM Copernicus + curvas")
    ap.add_argument("--region", default="purace")
    ap.add_argument("--intervalo", type=int, default=50)
    ap.add_argument("--maestro", type=int, default=250)
    args = ap.parse_args()

    region = common.obtener_region(args.region)
    common.log.info(f"Región: {region['nombre']}")
    generar_relieve(region, args.intervalo, args.maestro)


if __name__ == "__main__":
    main()
