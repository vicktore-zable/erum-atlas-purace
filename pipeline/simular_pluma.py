#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simular_pluma.py - Orquesta la simulación de dispersión de ceniza volcánica.

Para cada hora (previsión) o temporada (climatología) y para cada escenario
eruptivo (altura de columna 5/8/12 km), corre `modelo_pluma.pluma_en_grilla`
sobre la grilla de 100 m del sandbox y guarda por hora:
  - TIF de concentración en superficie (mg/m³)
  - TIF de carga depositada (g/m²)
  - GeoJSON del contorno "sector probable" (umbral de deposición)

El viento se toma del nivel de presión más representativo de la altura de la
pluma (tabla ALT_PRESION). Para escenarios de 8 y 12 km se usa el viento medio
de los niveles altos (500-300 hPa); para 5 km el nivel ~550-500 hPa.

Uso:
    python simular_pluma.py --region purace --modo prev --hasta 24
    python simular_pluma.py --region purace --modo prev --hasta 72
    python simular_pluma.py --region purace --modo clima --temporada dic_feb

Salidas:
    geo/simulacion/prevision/H_5km/pluma_5km_*_concentracion.tif
    geo/simulacion/prevision/H_5km/pluma_5km_*_deposito.tif
    geo/simulacion/prevision/H_5km/pluma_5km_*_sector.geojson
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from glob import glob
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402
import modelo_pluma  # noqa: E402

# Escenarios eruptivos (altura de pluma en m, tasa de emisión kg/s)
ESCENARIOS = [
    {"id": "5km",  "altura_m": 5000,  "tasa_kg_s": 2e4,  "etiqueta": "Erupción moderada (5 km)"},
    {"id": "8km",  "altura_m": 8000,  "tasa_kg_s": 1e5,  "etiqueta": "Erupción fuerte (8 km)"},
    {"id": "12km", "altura_m": 12000, "tasa_kg_s": 5e5,  "etiqueta": "Erupción vulcánica (12 km)"},
]

# Altura aprox (m) por nivel de presión (ISA zona tropical)
ALT_PRESION = {
    1000: 0, 925: 800, 850: 1450, 700: 3000, 600: 4300,
    550: 4950, 500: 5700, 400: 7200, 300: 9200, 250: 10500,
}

UMBRAL_DEPOSITO_G_M2 = 10.0   # umbral para "sector probable" de caída
RESOLUCION_M = 100.0


def _grilla(region, radio_m: float | None = None):
    """Grilla regular ~100 m para la simulación.

    Por defecto cuadra el sandbox. Pasando radio_m (kilómetros a cada lado
    del cráter) centra el dominio en el cráter para capturar plumas que salen
    del sandbox en cualquier dirección.
    """
    bbox = region["sandbox"]
    k = 111000.0
    if radio_m:
        cnt = region["crater"]
        half = radio_m / k
        lon0, lon1 = cnt["lon"] - half, cnt["lon"] + half
        lat0, lat1 = cnt["lat"] - half, cnt["lat"] + half
        n_lon = max(int(round(2 * half * k * math.cos(
            (lat0 + lat1) / 2 * math.pi / 180) / RESOLUCION_M)), 2)
        n_lat = max(int(round(2 * half * k / RESOLUCION_M)), 2)
        return (np.linspace(lon0, lon1, n_lon),
                np.linspace(lat0, lat1, n_lat))
    n_lon = max(int(math.ceil(
        (bbox["east"] - bbox["west"]) * k * math.cos(
            (bbox["south"] + bbox["north"]) / 2 * math.pi / 180)
        / RESOLUCION_M)), 2)
    n_lat = max(int(math.ceil(
        (bbox["north"] - bbox["south"]) * k / RESOLUCION_M)), 2)
    return (np.linspace(bbox["west"], bbox["east"], n_lon),
            np.linspace(bbox["south"], bbox["north"], n_lat))


def _salvar_tif(matriz, path, lons, lats):
    from osgeo import gdal, osr
    drv = gdal.GetDriverByName("GTiff")
    ds = drv.Create(str(path), matriz.shape[1], matriz.shape[0],
                    1, gdal.GDT_Float32)
    srs = osr.SpatialReference(); srs.ImportFromEPSG(4326)
    ds.SetProjection(srs.ExportToWkt())
    ds.SetGeoTransform((float(lons[0]), float(lons[1] - lons[0]), 0.0,
                        float(lats[-1]), 0.0, float(lats[0] - lats[1])))
    b = ds.GetRasterBand(1)
    b.WriteArray(np.where(np.isfinite(matriz), matriz, -9999.0))
    b.SetNoDataValue(-9999.0)
    ds = None
    return path


def _salvar_sector(region, matriz, lons, lats, umbral, path, props):
    yy, xx = np.where(matriz > umbral)
    if len(xx):
        minx, maxx = lons[xx].min(), lons[xx].max()
        miny, maxy = lats[yy].min(), lats[yy].max()
        geom = {"type": "Polygon",
                "coordinates": [[[minx, miny], [maxx, miny],
                                 [maxx, maxy], [minx, maxy], [minx, miny]]]}
        area_km2 = (maxx - minx) * (maxy - miny) * 111.0 * 111.0
    else:
        geom = None
        area_km2 = 0.0
    feat = {"type": "Feature", "geometry": geom, "properties": {
        **props,
        "max_deposito_g_m2": round(float(matriz.max()), 2),
        "area_sector_km2": round(area_km2, 2),
    }}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps({"type": "FeatureCollection", "features": [feat]},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def _viento_para_altura(por_nivel: dict, niveles, altura_m: float):
    """dir/vel del nivel más cercano a la altura de la pluma."""
    mejor = None
    for n in niveles:
        d = abs(ALT_PRESION.get(n, 5000) - altura_m)
        if mejor is None or d < mejor[0]:
            mejor = (d, n)
    n = mejor[1]
    return por_nivel.get(n, (0.0, 0.0))


def _parse_viento(vf: Path):
    data = json.loads(vf.read_text(encoding="utf-8"))
    niveles = data["niveles_presion_hPa"]
    times = data["times"]
    # por_hora[time] = {nivel: (dir, vel)}
    por_hora = {}
    for fila in data["filas"]:
        t, n, d, v, _t = fila
        por_hora.setdefault(t, {})[n] = (float(d), float(v))
    return times, niveles, por_hora


def simular_prevision(region, viento_json: Path, hasta: int,
                      geo_sim: Path, radio_m: float | None = None) -> list[Path]:
    times, niveles, por_hora = _parse_viento(viento_json)
    lons, lats = _grilla(region, radio_m)
    salidas: list[Path] = []
    crat = region["crater"]
    n_times = min(len(times), hasta)

    for i in range(n_times):
        t = times[i]
        perfil = por_hora.get(t, {})
        if not perfil:
            continue
        hh = int(t[11:13]) if len(t) >= 16 else 12
        for esc in ESCENARIOS:
            dir_g, vel = _viento_para_altura(perfil, niveles, esc["altura_m"])
            if vel < 0.1:
                continue
            clase = modelo_pluma.clase_estabilidad(vel, hh)
            C, Dep = modelo_pluma.pluma_en_grilla(
                lons, lats, crat["lon"], crat["lat"],
                dir_grados=dir_g, viento_ms=vel,
                altura_columna_m=esc["altura_m"],
                tasa_emision_kg_s=esc["tasa_kg_s"], clase=clase)
            tag = t.replace(":", "").replace("-", "").replace("T", "_")
            dir_out = geo_sim / "prevision" / f"H_{esc['id']}"
            dir_out.mkdir(parents=True, exist_ok=True)
            base = f"pluma_{esc['id']}_{tag}"
            tif_c = _salvar_tif(C, dir_out / f"{base}_concentracion.tif",
                                lons, lats)
            tif_d = _salvar_tif(Dep, dir_out / f"{base}_deposito.tif",
                                lons, lats)
            gj = _salvar_sector(region, Dep, lons, lats,
                                UMBRAL_DEPOSITO_G_M2,
                                dir_out / f"{base}_sector.geojson", {
                                    "escenario": esc["id"],
                                    "hora_utc": t,
                                    "dir_viento_deg": dir_g,
                                    "vel_viento_ms": round(vel, 2),
                                    "clase_pasquill": clase,
                                })
            salidas += [tif_c, tif_d, gj]
    common.log.ok(f"Previsión {n_times}h x {len(ESCENARIOS)} escenarios: "
                  f"{len(salidas)} archivos")
    return salidas


def simular_climatologia(region, temporada: str, geo_sim: Path,
                         radio_m: float | None = None) -> list[Path]:
    """Escenarios con viento dominante de una temporada (rosa)."""
    geo_viento = common.ruta_region(region, "geo_viento")
    rosa = geo_viento / f"rosa_vientos_{temporada}.csv"
    if not rosa.exists():
        common.log.error(f"No existe {rosa}. Corre descargar_viento.py --modo clima")
        return []
    # Leer rosa y promediar dirección dominante por nivel
    import csv as _csv
    por_nivel = {}
    with open(rosa, encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            n = int(row["nivel_hPa"])
            cuenta = int(row["cuenta"])
            por_nivel.setdefault(n, []).append(
                (float(row["dir_grados_inicial"]), cuenta))
    niveles = sorted(por_nivel)
    # Dirección dominante = octante con más cuenta; velocidad prom asociada
    dominante = {}
    for n in niveles:
        mejores = sorted(por_nivel[n], key=lambda x: -x[1])
        dominante[n] = (mejores[0][0] + 22.5) % 360
    lons, lats = _grilla(region, radio_m)
    salidas = []
    crat = region["crater"]
    for esc in ESCENARIOS:
        dir_g, _ = _viento_para_altura(
            {n: (dominante[n], 8.0) for n in dominante}, niveles,
            esc["altura_m"])
        # Velocidad representativa por altura
        perfil = {}
        for n in niveles:
            with open(rosa, encoding="utf-8") as fh:
                rows = list(_csv.DictReader(fh))
            vels = [float(r["velocidad_prom_ms"]) for r in rows
                    if int(r["nivel_hPa"]) == n]
            perfil[n] = (dominante[n], (sum(vels) / len(vels)) if vels else 8.0)
        dir_g, vel = _viento_para_altura(perfil, niveles, esc["altura_m"])
        C, Dep = modelo_pluma.pluma_en_grilla(
            lons, lats, crat["lon"], crat["lat"], dir_grados=dir_g,
            viento_ms=vel, altura_columna_m=esc["altura_m"],
            tasa_emision_kg_s=esc["tasa_kg_s"], clase=3)
        dir_out = geo_sim / "escenarios" / temporada
        dir_out.mkdir(parents=True, exist_ok=True)
        base = f"escenario_{temporada}_{esc['id']}"
        tif_c = _salvar_tif(C, dir_out / f"{base}_concentracion.tif", lons, lats)
        tif_d = _salvar_tif(Dep, dir_out / f"{base}_deposito.tif", lons, lats)
        gj = _salvar_sector(region, Dep, lons, lats, UMBRAL_DEPOSITO_G_M2,
                            dir_out / f"{base}_sector.geojson", {
                                "escenario": esc["id"], "temporada": temporada,
                                "dir_viento_deg": dir_g, "vel_viento_ms": vel,
                            })
        salidas += [tif_c, tif_d, gj]
    common.log.ok(f"Climatología {temporada}: {len(salidas)} archivos")
    return salidas


def main() -> None:
    ap = argparse.ArgumentParser(description="Simulación dispersión de ceniza")
    ap.add_argument("--region", default="purace")
    ap.add_argument("--modo", choices=["prev", "clima"], default="prev")
    ap.add_argument("--hasta", type=int, default=24)
    ap.add_argument("--temporada", default="dic_feb")
    ap.add_argument("--viento", default=None)
    ap.add_argument("--radio", type=float, default=None,
                    help="Semiextensión del dominio (m) centrado en el cráter. "
                         "Omitir = sandbox.")
    args = ap.parse_args()

    region = common.obtener_region(args.region)
    geo_sim = common.ruta_region(region, "geo_simulacion")
    geo_viento = common.ruta_region(region, "geo_viento")

    if args.modo == "prev":
        if args.viento:
            vf = Path(args.viento)
        else:
            cand = sorted(glob(str(geo_viento / "viento_prevision_*.json")))
            vf = Path(cand[-1]) if cand else None
        if not vf or not vf.exists():
            common.log.error("No hay JSON de viento. Ejecuta descargar_viento.py")
            sys.exit(1)
        simular_prevision(region, vf, args.hasta, geo_sim, args.radio)
    else:
        simular_climatologia(region, args.temporada, geo_sim, args.radio)


if __name__ == "__main__":
    main()