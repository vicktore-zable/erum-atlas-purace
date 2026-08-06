#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
descargar_viento.py - Perfil de viento por niveles de presión (horario) para
simulación de dispersión de ceniza volcánica Puracé.

Dos modos:
  * Previsión (operativo): viento horario Open-Meteo para las próximas horas.
  * Climatología: viento pasado (Open-Meteo archive) agrupado por temporada
    para dibujar rosa de vientos y escenarios de amenaza (modo clima).

El cráter está ~4650 m s.n.m., por lo que el perfil se toma en múltiples
niveles de presión (1000..250 hPa) que cubren la troposfera.

Uso:
    python descargar_viento.py --region purace [--modo pre|clima]
                               [--horizonte 24] [--hasta 72]

Salidas:
    geo/viento/viento_prevision_YYYYMMDD_HHmmss.json  (+ .csv)
    geo/viento/rosa_vientos_{temporada}.csv           (modo clima)
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

NIVELES = [1000, 925, 850, 700, 600, 550, 500, 400, 300, 250]
URL_FORECAST = "https://api.open-meteo.com/v1/forecast"
URL_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"


def _fetch_json(url: str, intentos: int = 5) -> dict | None:
    for i in range(1, intentos + 1):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 (ERUM-Atlas)"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            common.log.warning(f"intento {i}/{intentos}: {exc}")
            time.sleep(3 * i)
    return None


def _vars(niveles) -> tuple[list[str], list[str], list[str]]:
    vs = [f"wind_speed_{n}hPa" for n in niveles]
    vd = [f"wind_direction_{n}hPa" for n in niveles]
    vt = [f"temperature_{n}hPa" for n in niveles]
    return vs, vd, vt


def _guardar(geo_viento: Path, sufijo: str, tiempos: list,
             niveles: list, filas: list[list]) -> Path:
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    js = geo_viento / f"viento_{sufijo}_{ts}.json"
    registro = {
        "fuente": "Open-Meteo",
        "modo": sufijo,
        "niveles_presion_hPa": niveles,
        "muestras": len(filas),
        "generado": ts,
        "tiempos": tiempos,
        "filas": filas,
    }
    js.write_text(json.dumps(registro, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    common.log.ok(f"JSON viento: {js.name} ({len(filas)} muestras)")
    return js


def _csv_viento(geo_viento: Path, nombre: str, tiempos: list,
                niveles: list, filas: list[list]) -> Path:
    """filas: [time, dir, vel, temp] repetidos por nivel."""
    csv_path = geo_viento / nombre
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["time_utc", "nivel_hPa", "dir_grados",
                    "velocidad_ms", "temp_c"])
        for fila in filas:
            # Cada fila puede ser [t, nivel, dir, vel, temp] o tupla
            w.writerow(fila)
    common.log.ok(f"CSV viento: {csv_path.name}")
    return csv_path


def descargar_prevision(region: dict, hasta: int) -> Path:
    """Viento previsto (modo operativo) hasta 'hasta' horas adelante."""
    geo_viento = common.ruta_region(region, "geo_viento")
    geo_viento.mkdir(parents=True, exist_ok=True)

    lat = region["crater"]["lat"]
    lon = region["crater"]["lon"]
    nv = ",".join(str(n) for n in NIVELES)
    vs, vd, vt = _vars(NIVELES)

    url = (f"{URL_FORECAST}?latitude={lat}&longitude={lon}"
           f"&pressure_level={nv}&wind_speed_unit=ms&temperature_unit=celsius"
           f"&hourly={','.join(vs + vd + vt)}"
           f"&forecast_days=5&timezone=UTC")
    data = _fetch_json(url)
    if not data:
        common.log.error("No se pudo descargar previsión de viento")
        return None

    hourly = data.get("hourly", {})
    tiempos = hourly.get("time", [])[:hasta]
    filas: list[list] = []
    for i, t in enumerate(tiempos):
        for j, n in enumerate(NIVELES):
            filas.append([
                t, n,
                hourly.get(f"wind_direction_{n}hPa", [None])[i],
                hourly.get(f"wind_speed_{n}hPa", [None])[i],
                hourly.get(f"temperature_{n}hPa", [None])[i],
            ])

    sufijo = f"prevision_{hasta}h"
    _csv_viento(geo_viento, f"viento_{sufijo}.csv", tiempos, NIVELES, filas)
    js = geo_viento / f"viento_{sufijo}_{dt.datetime.now():%Y%m%d_%H%M%S}.json"
    js.write_text(json.dumps({
        "fuente": "Open-Meteo", "modo": "prevision", "horizonte_h": hasta,
        "niveles_presion_hPa": NIVELES, "lat": lat, "lon": lon,
        "times": tiempos, "filas": filas,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    common.log.ok(f"JSON: {js.name} ({len(tiempos)} horas)")
    return js


def descargar_climatologia(region: dict,
                            inicio: str = "2024-01-01",
                            fin: str = "2025-12-31") -> list[Path]:
    """Viento histórico agrupado por temporada (dic-feb, jun-ago)."""
    geo_viento = common.ruta_region(region, "geo_viento")
    geo_viento.mkdir(parents=True, exist_ok=True)
    lat, lon = region["crater"]["lat"], region["crater"]["lon"]
    nv = ",".join(str(n) for n in NIVELES)
    vs, vd, vt = _vars(NIVELES)

    url = (f"{URL_ARCHIVE}?latitude={lat}&longitude={lon}"
           f"&pressure_level={nv}&wind_speed_unit=ms&temperature_unit=celsius"
           f"&hourly={','.join(vs + vd + vt)}"
           f"&start_date={inicio}&end_date={fin}&timezone=UTC")
    data = _fetch_json(url, intentos=8)
    if not data:
        common.log.error("No se pudo descargar climatología")
        return []
    hourly = data.get("hourly", {})
    tiempos = hourly.get("time", [])
    # Agrupar por temporada
    categorias = []
    for t in tiempos:
        m = int(t[5:7])
        if m in (12, 1, 2):
            categorias.append("dic_feb")
        elif m in (6, 7, 8):
            categorias.append("jun_ago")
        else:
            categorias.append("otros")
    # Rosa de vientos por temporada y nivel (frecuencia por octante de dirección)
    salidas = []
    for temp in ("dic_feb", "jun_ago"):
        idx = [i for i, c in enumerate(categorias) if c == temp]
        if not idx:
            continue
        filas = []
        for j, n in enumerate(NIVELES):
            cont = defaultdict(int)
            vel_sum = defaultdict(float)
            for i in idx:
                d = hourly.get(f"wind_direction_{n}hPa", [None])[i]
                v = hourly.get(f"wind_speed_{n}hPa", [None])[i]
                if d is None or v is None:
                    continue
                # Octantes de dirección (cada 45º)
                oct = int(((float(d) % 360) + 22.5) // 45)
                cont[oct] += 1
                vel_sum[oct] += float(v)
            for o in sorted(cont):
                filas.setdefault(n, []).append([
                    f"octante_{o*45:03d}", o, cont[o],
                    round(vel_sum[o] / cont[o], 2)])
        csv_path = geo_viento / f"rosa_vientos_{temp}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["nivel_hPa", "octante", "dir_grados_inicial",
                        "cuenta", "velocidad_prom_ms"])
            for n in NIVELES:
                for f in filas.get(n, []):
                    w.writerow([n, f[1], f[0].replace("octante_", ""),
                                f[2], f[3]])
        salidas.append(csv_path)
        common.log.ok(f"Rosa vientos {temp}: {csv.name}")
    return salidas


def main() -> None:
    ap = argparse.ArgumentParser(description="Descarga perfiles de viento")
    ap.add_argument("--region", default="purace")
    ap.add_argument("--modo", choices=["pre", "clima"], default="pre")
    ap.add_argument("--hasta", type=int, default=72,
                    help="Nº de horas a guardar (previsión)")
    args = ap.parse_args()

    region = common.obtener_region(args.region)
    if args.modo == "pre":
        descargar_prevision(region, args.hasta)
    else:
        descargar_climatologia(region)


if __name__ == "__main__":
    main()