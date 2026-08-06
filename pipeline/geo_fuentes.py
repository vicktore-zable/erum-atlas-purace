#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
geo_fuentes.py - Registro centralizado de fuentes oficiales de datos.

Cada fuente define: id, nombre, institución, tipo de acceso (url/arcgis/pdf),
URL(s) de descarga, formato esperado, CRS origen, vigencia y nombre de salida.

Sprint 1: DANE (MGN/DIVIPOLA Cauca) + SGC (amenaza volcánica Puracé).
Arquitectura lista a escalar: añadir IGAC, INVIAS, IDEAM como nuevas entradas.
"""
from __future__ import annotations

import copy


def _u(url: str) -> str:
    return url


FUENTES = {
    # ------------------------------------------------------------------
    # DANE - MGN / DIVIPOLA (marco geoestadístico nacional)
    # ------------------------------------------------------------------
    "dane_mgn_departamento": {
        "id": "dane_mgn_departamento",
        "nombre": "MGN Departamentos",
        "institucion": "DANE",
        "tipo": "url_zip",
        "url": _u(
            "https://geoportal.dane.gov.co/descargas/mgn_2025/"
            "MGN2025_ADM_DPTO_POLITICO_(geojson).zip"
        ),
        "formato": "geojson",
        "crs_origen": 4686,
        "vigencia": "2025",
        "salida": "dane_departamentos",
        "zip_miembro_geojson": "MGN2025_ADM_DPTO_POLITICO_(geojson).geojson",
    },
    "dane_mgn_municipio": {
        "id": "dane_mgn_municipio",
        "nombre": "MGN Municipios",
        "institucion": "DANE",
        "tipo": "url_zip",
        "url": _u(
            "https://geoportal.dane.gov.co/descargas/mgn_2025/"
            "MGN2025_ADM_MPIO_GRAFICO_(geojson).zip"
        ),
        "formato": "geojson",
        "crs_origen": 4686,
        "vigencia": "2025",
        "salida": "dane_municipios",
        "zip_miembro_geojson": "MGN2025_ADM_MPIO_GRAFICO_(geojson).geojson",
    },
    "dane_mgn_vereda": {
        "id": "dane_mgn_vereda",
        "nombre": "Veredas DANE",
        "institucion": "DANE",
        "tipo": "url_zip",
        "url": _u(
            "https://geoportal.dane.gov.co/descargas/veredas/"
            "gjson_CRVeredas_2024.zip"
        ),
        "formato": "geojson",
        "crs_origen": 4686,
        "vigencia": "2024",
        "salida": "dane_veredas",
        "zip_miembro_geojson": "gjson_CRVeredas_2024.geojson",
    },
    "dane_mgn_cabecera": {
        "id": "dane_mgn_cabecera",
        "nombre": "MGN Cabeceras y centros poblados",
        "institucion": "DANE",
        "tipo": "url_zip",
        "url": _u(
            "https://geoportal.dane.gov.co/descargas/mgn_2025/"
            "MGN2025_URB_ZONA_URBANA_(geojson).zip"
        ),
        "formato": "geojson",
        "crs_origen": 4686,
        "vigencia": "2025",
        "salida": "dane_cabeceras",
        "zip_miembro_geojson": "MGN2025_URB_ZONA_URBANA_(geojson).geojson",
    },
    # ------------------------------------------------------------------
    # SGC - Amenaza volcánica Puracé (ArcGIS Server oficial)
    # ------------------------------------------------------------------
    "sgc_amenaza": {
        "id": "sgc_amenaza",
        "nombre": "Amenaza volcánica Puracé",
        "institucion": "SGC",
        "tipo": "arcgis",
        "url_base": _u(
            "https://srvags.sgc.gov.co/arcgis/rest/services/"
            "Amenaza_Volcanica/Amenaza_Volcanica/MapServer/3"
        ),
        "capa_id": 3,
        "grupo": "Puracé",
        "formato": "geojson",
        "crs_origen": 4686,
        "vigencia": "V1",
        "salida": "sgc_amenaza",
        "nota": (
            "Polígonos de amenaza (Alta/Media/Baja/Lahar) del grupo Puracé. "
            "Campos: VOLCAN, AMENAZA, FENOMENOS, LEYENDA_1..4, AREA_KM2."
        ),
    },
    "sgc_volcan_punto": {
        "id": "sgc_volcan_punto",
        "nombre": "Cráter/volcán Puracé",
        "institucion": "SGC",
        "tipo": "arcgis",
        "url_base": _u(
            "https://srvags.sgc.gov.co/arcgis/rest/services/"
            "Amenaza_Volcanica/Amenaza_Volcanica/MapServer/1"
        ),
        "capa_id": 1,
        "grupo": "Puracé",
        "formato": "geojson",
        "crs_origen": 4686,
        "vigencia": "V1",
        "salida": "sgc_volcan_punto",
        "nota": "Punto del volcán Puracé (cráter).",
    },
    "sgc_piroclastos": {
        "id": "sgc_piroclastos",
        "nombre": "Caída de piroclastos Puracé (zona de influencia)",
        "institucion": "SGC",
        "tipo": "arcgis",
        "url_base": _u(
            "https://srvags.sgc.gov.co/arcgis/rest/services/"
            "Amenaza_Volcanica/Amenaza_Volcanica/MapServer/2"
        ),
        "capa_id": 2,
        "grupo": "Puracé",
        "formato": "geojson",
        "crs_origen": 4686,
        "vigencia": "V1",
        "salida": "sgc_piroclastos",
        "nota": "Polilíneas de zona de influencia por caída de piroclastos.",
    },
}


def obtener_fuente(fuente_id: str) -> dict:
    """Devuelve una copia de la fuente (para evitar mutaciones)."""
    if fuente_id not in FUENTES:
        raise KeyError(f"Fuente no registrada: {fuente_id}")
    return copy.deepcopy(FUENTES[fuente_id])


def fuentes_por_institucion(institucion: str) -> list[dict]:
    """Devuelve todas las fuentes de una institución (ej: 'DANE')."""
    return [
        copy.deepcopy(f) for f in FUENTES.values()
        if f["institucion"].upper() == institucion.upper()
    ]


def listar_fuentes() -> list[str]:
    return sorted(FUENTES.keys())


if __name__ == "__main__":
    print("=== Fuentes registradas ===")
    for fid, f in FUENTES.items():
        print(f"- {fid}: {f['nombre']} [{f['institucion']}] -> {f['salida']}")
