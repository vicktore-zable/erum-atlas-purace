#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
common.py - Utilidades compartidas del pipeline ERUM Atlas.

Proporciona:
  - Carga de config/regiones.yaml
  - Resolución de rutas absolutas (independiente del cwd)
  - Logging a consola + archivo
  - Helpers de descarga HTTP robustos (reintentos, timeout)
"""
from __future__ import annotations

import logging
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Rutas del proyecto
# ---------------------------------------------------------------------------
PROYECTO_ROOT = Path(__file__).resolve().parent.parent  # <proyecto>/pipeline/.. -> <proyecto>/
CONFIG_PATH = PROYECTO_ROOT / "config" / "regiones.yaml"


class Log:
    """Logger ligero: consola + archivo geo/pipeline.log."""

    def __init__(self) -> None:
        self._logger = logging.getLogger("erum_pipeline")
        self._logger.setLevel(logging.INFO)
        if not self._logger.handlers:
            fmt = logging.Formatter(
                "%(asctime)s | %(levelname)-7s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(fmt)
            self._logger.addHandler(sh)
            log_dir = PROYECTO_ROOT / "geo"
            log_dir.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_dir / "pipeline.log",
                                     encoding="utf-8")
            fh.setFormatter(fmt)
            self._logger.addHandler(fh)
        # Asegurar UTF-8 en consola (Windows cp1252 no imprime ✔)
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    def info(self, msg: str) -> None:
        self._logger.info(msg)

    def warning(self, msg: str) -> None:
        self._logger.warning(msg)

    def error(self, msg: str) -> None:
        self._logger.error(msg)

    def ok(self, msg: str) -> None:
        self._logger.info(f"✔ {msg}")


log = Log()


def cargar_regiones() -> dict[str, Any]:
    """Carga config/regiones.yaml y devuelve el dict completo."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"No existe {CONFIG_PATH}")
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data


def obtener_region(region_id: str = "purace") -> dict[str, Any]:
    """Devuelve la configuración de una región + rutas resueltas."""
    data = cargar_regiones()
    if region_id not in data["regiones"]:
        raise KeyError(f"Región no definida: {region_id}")
    region = dict(data["regiones"][region_id])
    region["id"] = region_id
    # Resolver rutas relativas a la raíz del proyecto
    rutas = data["rutas"]
    region["rutas"] = {
        k: (PROYECTO_ROOT / v).resolve() for k, v in rutas.items()
    }
    return region


def ruta_region(region: dict[str, Any], clave: str) -> Path:
    """Devuelve Path absoluto de una ruta de la región."""
    return region["rutas"][clave]


def descargar(url: str, destino: Path, timeout: int = 120,
              reintentos: int = 3) -> Path:
    """Descarga una URL a un archivo con reintentos y timeout."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    for intento in range(1, reintentos + 1):
        try:
            log.info(f"Descargando [{intento}/{reintentos}]: {url}")
            req = urllib.request.Request(
                url, headers={"User-Agent": "ERUM-Atlas/1.0 (pipeline QGIS)"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp, \
                    open(destino, "wb") as out:
                out.write(resp.read())
            tam = destino.stat().st_size if destino.exists() else 0
            if tam == 0:
                raise RuntimeError("Descarga vacía (0 bytes)")
            log.ok(f"Descargado {destino.name} ({tam:,} bytes)")
            return destino
        except Exception as exc:  # noqa: BLE001
            log.warning(f"Error descarga: {exc}")
            if intento < reintentos:
                time.sleep(2 * intento)
    raise RuntimeError(f"No se pudo descargar: {url}")
