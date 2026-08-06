#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
modelo_pluma.py - Núcleo de dispersión de ceniza volcánica (pluma gaussiana
con sedimentación gravitatoria de múltiples clases de partícula).

Enfoque (base de un modelo tipo Fall3D simplificado, p. ej. Suzuki/Wilson):

  Para cada clase de tamaño de partícula (con su velocidad terminal w_s):
      z_eff(x) = max(H_pluma - w_s * (x / u), 0)   <- pluma descendente

      C_clase = Q_clase / (pi * sigma_y * sigma_z * u)
                * exp(-y^2 / (2*sigma_y^2))
                * exp(-z_eff(x)^2 / (2*sigma_z^2))

  La concentración total es la suma sobre clases de tamaño. La deposición
  (g/m²) integra la concentración a lo largo del tiempo de residencia.

  La pluma se orienta según la dirección del viento a la altura de la columna.

Salidas (matrices 2D):
  - concentración en superficie (mg/m³)
  - carga depositada (g/m²)

Funciones de dispersión de Briggs (rural). Puro numpy, testable.
"""
from __future__ import annotations

import numpy as np

# Clases de partícula de ceniza: (diametro_um, velocidad_terminal_ms, fraccion_masa)
# Velocidades terminales típicas de ceniza volcánica (Wilson 1972 / Arrighi).
PARTICULAS_DEFAULT = [
    (20, 0.03, 0.25),    # ceniza muy fina
    (63, 0.27, 0.35),    # ceniza fina
    (125, 0.75, 0.20),   # ceniza fina media
    (250, 3.0, 0.15),    # ceniza gruesa
    (500, 8.0, 0.05),    # ceniza muy gruesa
]

BRIGGS = {
    1: (0.22, 1.0, 0.20, 1.0),
    2: (0.16, 1.0, 0.12, 1.0),
    3: (0.11, 0.91, 0.08, 0.91),
    4: (0.08, 0.80, 0.06, 0.71),
    5: (0.06, 0.71, 0.03, 0.58),
    6: (0.04, 0.67, 0.02, 0.55),
}


def clase_estabilidad(viento_ms: float, hora_local: int) -> int:
    """Clase de Pasquill-Gifford (1=A ... 6=F) por velocidad y hora local."""
    dia = 6 <= hora_local <= 18
    if viento_ms < 2:
        return 1 if dia else 6
    if viento_ms < 3:
        return 2 if dia else 6
    if viento_ms < 5:
        return 3 if dia else 5
    if viento_ms < 6:
        return 4 if dia else 4
    return 4 if dia else 3


def _sigma(x, clase):
    ay, by, cz, dz = BRIGGS.get(clase, BRIGGS[4])
    x = np.maximum(np.asarray(x, dtype=float), 10.0)
    return ay * x ** by, cz * x ** dz


def pluma_en_grilla(lons, lats, lon0, lat0,
                    dir_grados: float, viento_ms: float,
                    altura_columna_m: float,
                    tasa_emision_kg_s: float,
                    clase: int,
                    particulas=None,
                    deposicion: bool = True,
                    k_y: float = 1.0, k_z: float = 1.0):
    """Evalúa la pluma gaussiana descendente en una grilla lon/lat.

    Parámetros:
        lons, lats : arreglos 1D (malla producto).
        lon0, lat0 : cráter.
        dir_grados : rumbo desde donde viene el viento (0=N, 90=E).
        viento_ms  : velocidad media a la altura de la pluma (m/s).
        altura_columna_m : altura de la columna eruptiva (H).
        tasa_emision_kg_s : Q total (todas las clases).
        clase      : 1..6 Pasquill-Gifford.
        particulas : lista de (diam_um, w_s_ms, fraccion); default global.
        k_y, k_z   : factores de dispersión.

    Retorna (concentracion_mg_m3, deposito_g_m2).
    """
    R = 6371e3
    part = particulas or PARTICULAS_DEFAULT

    lon_g, lat_g = np.meshgrid(np.asarray(lons, float),
                               np.asarray(lats, float))
    dlon = (lon_g - lon0) * np.pi / 180.0
    dlat = (lat_g - lat0) * np.pi / 180.0
    x_m = R * dlon * np.cos(lat0 * np.pi / 180.0)   # este (+)
    y_m = R * dlat                                    # norte (+)

    # A favor del viento: el viento viene de `dir_grados`, por lo que sopla
    # hacia (dir_grados + 180). Vector unitario hacia donde sopla.
    theta = np.deg2rad(float(dir_grados) + 180.0)
    ux, uy = np.sin(theta), np.cos(theta)
    x_down = ux * x_m + uy * y_m
    y_cross = -uy * x_m + ux * y_m

    sy, sz = _sigma(np.maximum(x_down, 10.0), clase)
    sy = sy * k_y
    sz = sz * k_z
    u = max(float(viento_ms), 0.1)
    H = float(altura_columna_m)

    mascara = x_down > 0
    xd = np.where(mascara, np.maximum(x_down, 10.0), 1.0)

    C_total = np.zeros_like(x_m)
    Dep_total = np.zeros_like(x_m)

    for _, w_s, fraccion in part:
        Q = float(tasa_emision_kg_s) * fraccion * 1e6  # mg/s
        if Q <= 0:
            continue
        # Altura efectiva descendente: la partícula cae a w_s
        t_fall = xd / u
        z_eff = np.maximum(H - w_s * t_fall, 0.0)

        factor = Q / (np.pi * u * sy * sz)
        horiz = np.exp(-(y_cross ** 2) / (2 * sy ** 2))
        vert = np.exp(-(z_eff ** 2) / (2 * sz ** 2))
        C = factor * horiz * vert * mascara.astype(float)
        C_total += C

        if deposicion:
            t = np.where(mascara, xd / u, 0.0)
            Dep_total += C * w_s * t / 1e3   # g/m²

    C_total = np.where(np.isfinite(C_total), C_total, 0.0)
    Dep_total = np.where(np.isfinite(Dep_total), Dep_total, 0.0)
    return C_total, Dep_total


if __name__ == "__main__":
    lons = np.linspace(-76.60, -76.22, 120)
    lats = np.linspace(1.95, 2.32, 120)
    c, d = pluma_en_grilla(lons, lats, -76.397222, 2.313889,
                           dir_grados=130, viento_ms=8.5,
                           altura_columna_m=8000, tasa_emision_kg_s=1000,
                           clase=4)
    print("max C (mg/m3): %.2f  max dep (g/m2): %.1f" % (c.max(), d.max()))
    print("cells C>0:", int((c > 0).sum()), "de", c.size)
    # Posición del pico
    iy, ix = np.unravel_index(int(np.argmax(d)), d.shape)
    print("pico dep en lon=%.4f lat=%.4f" % (lons[ix], lats[iy]))
