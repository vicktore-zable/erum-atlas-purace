# Simulación de dispersión de ceniza — ERUM Atlas · Puracé

Módulo de simulación de dispersión de ceniza volcánica para la previsión
operativa. Combina **viento meteorológico horario** (Open-Meteo) con un
**modelo de pluma gaussiana de múltiples clases de partículas** para estimar,
hora a hora, la concentración en superficie y la carga de ceniza depositada.

## Pipeline

```
descargar_viento.py ──► viento_prevision_72h.csv/.json   (perfil horario 10 niveles)
       │                                                    1000..250 hPa @ cráter
       ▼
simular_pluma.py ──► geo/simulacion/prevision/H_{5,8,12}km/
       │                ├─ *_concentracion.tif   (mg/m³, Float32 EPSG:4326)
       │                ├─ *_deposito.tif        (g/m²)
       │                └─ *_sector.geojson      (contorno "sector probable")
       ▼
aplicar_simulacion_qgis.py ──► master_purace.qgz  (capas temporales animables)
```

## Escenarios eruptivos (`simular_pluma.py`)

| Escenario | Altura columna | Tasa de emisión | Uso |
|---|---|---|---|
| `5km` | 5 000 m | 2×10⁴ kg/s | Erupción moderada |
| `8km` | 8 000 m | 1×10⁵ kg/s | Erupción fuerte |
| `12km` | 12 000 m | 5×10⁵ kg/s | Erupción vulcánica |

El viento de cada escenario se toma del **nivel de presión más cercano** a la
altura de la columna (`ALT_PRESION`): ~550-500 hPa para 5 km, ~400 hPa para
8 km, ~300 hPa para 12 km.

## Modelo de pluma (`pipeline/modelo_pluma.py`)

- Pluma gaussiana con **coeficientes de dispersión Briggs rurales** según
  clase de estabilidad Pasquill-Gifford (1-6).
- **Sedimentación gravitatoria multi-clase**: 5 diámetros de partícula
  (20/63/125/250/500 µm) con velocidades terminales 0.03-8.0 m/s y fracciones
  0.25/0.35/0.20/0.15/0.05. Cada clase se transporta a sotavento y deposita a
  su distancia de alcance.
- Convención de dirección: el viento meteorológico **viene de** `dir_grados`;
  la pluma viaja hacia `dir_grados + 180°`.

### Validación

- Smoke test en grilla amplia (120 km): 5 km → max 883 g/m², 8 km → 19 000
  g/m², 12 km → 4.9×10⁶ g/m² (facies proximal gruesa, físicamente esperada
  para columna sostenida VEI-4).
- En dominio sandbox las plumas de 5/8 km **no** depositaban: los vientos
  previstos (115-125°→WNW, 236°→NE) las llevaban fuera del cuadro. Por eso la
  simulación usa `--radio 60000` (dominio de 120 km centrado en el cráter).

## Ejecución

```bash
# Previsión 24 h (3 escenarios × 24 h × 3 productos = 216 archivos)
python pipeline/simular_pluma.py --region purace --modo prev --hasta 24 --radio 60000

# Previsión 72 h
python pipeline/simular_pluma.py --region purace --modo prev --hasta 72 --radio 60000

# Escenarios climatológicos (rosa de vientos dic_feb / jun_ago)
python pipeline/simular_pluma.py --region purace --modo clima --temporada dic_feb --radio 60000
```

## Capas temporales en QGIS

`pipeline/aplicar_simulacion_qgis.py` carga en `master_purace.qgz` el grupo
**Simulacion ceniza (prevision)** con 216 capas (24 h × 3 escenarios × 3
productos), cada una con su rango temporal fijo:

```
Simulacion ceniza (prevision)
├── H_5km   → 24× concentración + 24× depósito + 24× sector
├── H_8km   → idem
└── H_12km  → idem
```

Para animar: **Vista ▸ Panel ▸ Control temporal** (o el reloj ⏱), y **play**.
El rango del proyecto queda en 2026-08-06 00:00 → 2026-08-07 00:00 (24 h).

### Estilos aplicados

| Producto | Rampa |
|---|---|
| Depósito (g/m²) | Logarítmica 0.1 → 10⁷: blanco→amarillo→naranja→rojo→morado→negro (cubre hasta la facies proximal) |
| Concentración (mg/m³) | Logarítmica 10⁻¹⁴ → 10⁻⁴ |
| Sector probable | Fill del color del escenario al 12% + borde 1.1 mm (`#f47d1b` 5km, `#e31a1c` 8km, `#8e0152` 12km) |

## Limitaciones

- Modelo gaussiano estacionario por hora: no simula pulso eruptivo ni
  evolución intra-hora; adecuado para orientar, no para decisión legal.
- Sin micro-física ni remoción húmeda (lluvia); los valores absolutos son
  orientativos. La columna se asume vertical y sin shear de viento vertical.
- Los valores proximales 10⁵-10⁷ g/m² del escenario 12 km representan la
  facies gruesa cerca del vent; la mayor parte del área útil está en el rango
  0.1-1000 g/m².
