# Estilos del proyecto QGIS — ERUM Atlas · Puracé

Se aplicaron con `pipeline/aplicar_estilos_qgis.py` sobre `master_purace.qgz`
(backup previo en `master_purace.qgz.bak`). Proyecto en **EPSG:4326**.

## Capas cargadas (desde `geo/processed/`, completas sin clip)

| Capa | Tipo | Estilo |
|---|---|---|
| DANE Departamentos | Polígono | Solo borde gris oscuro `#4d4d4d` 1.2 mm, sin relleno |
| DANE Municipios | Polígono | Relleno crema `#f7f3e9` 65% opacidad, borde `#7f7f7f` 0.6 mm + etiqueta nombre (escala ≤ 1:1.5M) |
| DANE Veredas | Polígono | Borde gris claro `#bdbdbd` 0.25 mm punteado, sin relleno (contexto fino) |
| DANE Cabeceras | Punto | Círculo morado `#6a3d9a` 5 px, borde blanco + etiqueta (escala ≤ 1:1.2M) |
| SGC Amenaza volcánica | Polígono | **Categorizado** por `AMENAZA` (ver tabla abajo), opacidad 80% |
| SGC Piroclastos | Línea | Discontinua naranja `#e84a25` 1.6 mm, 90% opacidad |
| SGC Volcán Puracé (cráter) | Punto | Estrella roja `#e60000` 9 px, borde blanco + etiqueta |
| referencia_anillos — anillos_km | Polígono | **Graduado** por `radio_km`: 5/15/30 km |
| referencia_anillos — puntos_referencia | Punto | Círculo azul `#2166ac` 4 px, borde blanco |

## Categorías de amenaza volcánica

| Categoría | Color | Uso |
|---|---|---|
| Alta | `#d7191c` rojo | Amenaza Alta (fill 190/255) |
| Media | `#fdae61` naranja | Amenaza Media |
| Baja | `#ffffbf` amarillo | Amenaza Baja |
| (default) | `#cccccc` | Lahar u otros fenómenos |

Paleta secuencial Carto (rojo→naranja→amarillo): **red-green colorblind-safe** y
jerarquía de peligro intuitiva. Fill ~75% para legibilidad sobre el mapa base.

## Orden de dibujo (de abajo hacia arriba en el panel de capas)

1. Teselas OpenStreetMap / Esri Boundaries Places (alternables)
2. DANE Veredas
3. DANE Municipios
4. DANE Departamentos
5. referencia_anillos — anillos_km
6. SGC Piroclastos
7. SGC Amenaza volcánica
8. DANE Cabeceras
9. SGC Volcán Puracé (cráter)

> El cráter siempre queda por encima de la amenaza para que el punto de origen
> sea visible; las cabeceras sobre la amenaza para localización operativa.

## Anillos (graduado por `radio_km`)

| Rango | Etiqueta | Color |
|---|---|---|
| 0–5 km | 5 km | `#d7191c` rojo (op. 40/255) |
| 5–15 km | 15 km | `#f47d1b` naranja |
| 15–30 km | 30 km | `#2b9c3f` verde |

## Notas

- Los PDF SGC originales se **eliminaron** del proyecto (sin georeferenciación, no
  renderizaban). El vector oficial ya viene del pipeline (`sgc_amenaza.geojson`).
- Re-ejecutable: `pipeline/aplicar_estilos_qgis.py` (restaurar `.bak` primero si
  se quiere partir de cero).
- El script es idempotente sobre un proyecto limpio; los nombres de capa son fijos.
