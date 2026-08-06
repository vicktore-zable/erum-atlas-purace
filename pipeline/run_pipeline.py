#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_pipeline.py - Orquestador del pipeline ERUM Atlas (Sprint 1).

Ejecuta en orden:
  1. descargar_dane.py   (adquisición DANE MGN)
  2. descargar_sgc.py    (adquisición SGC amenaza Puracé + anillos)
  3. normalizar.py       (EPSG:4326 + limpieza)
  4. recortar_anillos.py (clip 5/15/30 km)
  5. exportar_geojson.py (nombres canónicos + index.json)
  6. exportar_garmin.py  (GPX/KML)

Uso:
    python run_pipeline.py [--region purace] [--solo descarga,norm,clip,exp]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

SCRIPT_DIR = Path(__file__).resolve().parent


def _run(script: str, region: str, *extra: str) -> None:
    cmd = [sys.executable, str(SCRIPT_DIR / script), "--region", region, *extra]
    common.log.info(">> " + " ".join(cmd))
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        raise SystemExit(f"Fallo en {script} (código {proc.returncode})")


def main() -> None:
    ap = argparse.ArgumentParser(description="Orquesta el pipeline completo")
    ap.add_argument("--region", default="purace")
    ap.add_argument("--solo", default="all",
                    help="Subconjunto: all|descarga,norm,clip,exp")
    args = ap.parse_args()

    pasos = args.solo.split(",")
    region = args.region
    if "descarga" in pasos or args.solo == "all":
        _run("descargar_dane.py", region)
        _run("descargar_sgc.py", region)
    if "norm" in pasos or args.solo == "all":
        _run("normalizar.py", region)
    if "clip" in pasos or args.solo == "all":
        _run("recortar_anillos.py", region)
    if "exp" in pasos or args.solo == "all":
        _run("exportar_geojson.py", region)
        _run("exportar_garmin.py", region)

    common.log.ok("Pipeline completado. Revisa geo/processed/ y geo/downloads/")


if __name__ == "__main__":
    main()
