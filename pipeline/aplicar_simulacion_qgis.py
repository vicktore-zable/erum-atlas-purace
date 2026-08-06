# -*- coding: utf-8 -*-
"""
aplicar_simulacion_qgis.py - Carga la simulación de dispersión de ceniza en
master_purace.qgz como capas temporales (concentración, depósito, sector) para
animar la previsión hora a hora con el control temporal de QGIS.

Grupos creados:
  Simulación ceniza (previsión)
    ├── H_5km
    │     ├── concentración (hora por hora, temporal)
    │     ├── depósito
    │     └── sector probable
    ├── H_8km ...
    └── H_12km ...
"""
import sys
from pathlib import Path

from qgis.core import (
    QgsApplication, QgsProject, QgsRasterLayer, QgsVectorLayer,
    QgsRasterShader, QgsColorRampShader, QgsSingleBandPseudoColorRenderer,
    QgsFillSymbol, QgsSingleSymbolRenderer, QgsCategorizedSymbolRenderer,
    QgsRendererCategory, QgsCoordinateReferenceSystem, QgsDateTimeRange,
    QgsProperty,
)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QDateTime, QCoreApplication

argv = [a.encode('utf-8') for a in sys.argv]
app = QgsApplication(argv, False)
QgsApplication.setPrefixPath(r'D:/Program Files/QGIS 3.44.7/apps/qgis', True)
QgsApplication.initQgis()

PROY = r'H:/Mi unidad/2026/erum/purace/master_purace.qgz'
SIM  = Path(r'H:/Mi unidad/2026/erum/purace/geo/simulacion/prevision')

p = QgsProject.instance()
ok = p.read(PROY)
print('leido:', ok)

# ---- Limpiar grupo anterior si existe ----
GRUPO = 'Simulacion ceniza (prevision)'
for l in list(p.mapLayers().values()):
    if l.name().startswith('simcen_'):
        p.removeMapLayer(l.id())
for g in list(p.layerTreeRoot().children()):
    if g.name() == GRUPO:
        p.layerTreeRoot().removeChildNode(g)


def qdt_from_tag(tag):
    # tag ej: 20260806_0000
    y, m, d = int(tag[0:4]), int(tag[4:6]), int(tag[6:8])
    hh, mm = int(tag[9:11]), int(tag[11:13])
    return QDateTime(y, m, d, hh, mm, 0)


def shader_deposito():
    """Ramp logarítmica de depósito (g/m2) hasta valores proximales 1e7."""
    shader = QgsColorRampShader()
    shader.setColorRampType(QgsColorRampShader.Interpolated)
    stops = [
        (0.1,   QColor('#ffffff')),
        (1.0,   QColor('#ffffcc')),
        (10.0,  QColor('#fed976')),
        (100.0, QColor('#fd8d3c')),
        (1000.0, QColor('#e31a1c')),
        (1e4,   QColor('#8e0152')),
        (1e5,   QColor('#4a0026')),
        (1e6,   QColor('#2b0016')),
        (1e7,   QColor('#15000a')),
    ]
    for val, c in stops:
        shader.colorRampItemList().append(
            QgsColorRampShader.ColorRampItem(val, c, f'{val:g}'))
    rs = QgsRasterShader()
    rs.setRasterShaderFunction(shader)
    return rs


def shader_concentracion():
    shader = QgsColorRampShader()
    shader.setColorRampType(QgsColorRampShader.Interpolated)
    stops = [
        (1e-14, QColor('#ffffff')),
        (1e-12, QColor('#ffffcc')),
        (1e-10, QColor('#fed976')),
        (1e-8,  QColor('#fc4e2a')),
        (1e-6,  QColor('#8e0152')),
        (1e-4,  QColor('#2b0016')),
    ]
    for val, c in stops:
        shader.colorRampItemList().append(
            QgsColorRampShader.ColorRampItem(val, c, f'{val:.0e}'))
    rs = QgsRasterShader()
    rs.setRasterShaderFunction(shader)
    return rs


def estilizar_raster(layer, shader):
    renderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader)
    layer.setRenderer(renderer)


def sector_estilo(layer, categoria):
    """Capa sector: categorizada por escenario con fill transparente + borde."""
    c = QColor(categoria['color']); c.setAlpha(30)
    sym = QgsFillSymbol.createSimple({
        'color': c.name(), 'color_border': categoria['color'],
        'width_border': '1.1', 'style': 'solid'})
    cats = [QgsRendererCategory(categoria['valor'], sym, 'Sector probable')]
    renderer = QgsCategorizedSymbolRenderer(categoria['campo'], cats)
    layer.setRenderer(renderer)


def activar_temporal(layer, inicio, fin):
    tp = layer.temporalProperties()
    tp.setIsActive(True)
    tp.setFixedTemporalRange(QgsDateTimeRange(inicio, fin))


ESC_COLOR = {'5km': '#f47d1b', '8km': '#e31a1c', '12km': '#8e0152'}
tree_root = p.layerTreeRoot()
grupo = tree_root.addGroup(GRUPO)

for esc, hexc in ESC_COLOR.items():
    sub = grupo.addGroup(f'H_{esc}')
    carpeta = SIM / f'H_{esc}'
    if not carpeta.exists():
        print('  sin carpeta:', carpeta)
        continue
    tifs_c = sorted(carpeta.glob('*_concentracion.tif'))
    tifs_d = sorted(carpeta.glob('*_deposito.tif'))
    geojs  = sorted(carpeta.glob('*_sector.geojson'))
    # Añadir por orden cronológico
    for tif in tifs_c:
        tag = '_'.join(tif.stem.split('_')[-3:-1])  # ..._20260806_0000_concentracion
        ini = qdt_from_tag(tag)
        fin = ini.addSecs(3600)
        l = QgsRasterLayer(str(tif), f'simcen_{esc}_conc_{tag}', 'gdal')
        if l.isValid():
            estilizar_raster(l, shader_concentracion())
            activar_temporal(l, ini, fin)
            p.addMapLayer(l, False)
            sub.addLayer(l)
    for tif in tifs_d:
        tag = '_'.join(tif.stem.split('_')[-3:-1])
        ini = qdt_from_tag(tag)
        fin = ini.addSecs(3600)
        l = QgsRasterLayer(str(tif), f'simcen_{esc}_dep_{tag}', 'gdal')
        if l.isValid():
            estilizar_raster(l, shader_deposito())
            activar_temporal(l, ini, fin)
            p.addMapLayer(l, False)
            sub.addLayer(l)
    for gj in geojs:
        tag = '_'.join(gj.stem.split('_')[-3:-1])
        ini = qdt_from_tag(tag)
        fin = ini.addSecs(3600)
        l = QgsVectorLayer(str(gj), f'simcen_{esc}_sec_{tag}', 'ogr')
        if l.isValid():
            sector_estilo(l, {'campo': 'escenario', 'valor': esc, 'color': hexc})
            activar_temporal(l, ini, fin)
            p.addMapLayer(l, False)
            sub.addLayer(l)
    print(f'  H_{esc}: {len(tifs_c)} conc, {len(tifs_d)} dep, {len(geojs)} sec')

# ---- Rango temporal del proyecto ----
ts = p.timeSettings()
if tifs_c:
    primero = qdt_from_tag('_'.join(tifs_c[0].stem.split('_')[-3:-1]))
    ultimo = qdt_from_tag('_'.join(tifs_c[-1].stem.split('_')[-3:-1])).addSecs(3600)
    ts.setTemporalRange(QgsDateTimeRange(primero, ultimo))
    print('rango temporal proyecto:', primero.toString('yyyy-MM-dd hh:mm'),
          '->', ultimo.toString('yyyy-MM-dd hh:mm'))

# ---- CRS del proyecto ----
p.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))

p.write()
print('\nGUARDADO OK:', PROY)
print('capas finales:', [l.name() for l in p.mapLayers().values()])

QgsApplication.exitQgis()
print('DONE')