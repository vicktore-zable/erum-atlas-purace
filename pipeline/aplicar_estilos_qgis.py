# -*- coding: utf-8 -*-
"""
Configura master_purace.qgz: limpia capas rotas, carga capas procesadas
(geo/processed/*.geojson) y aplica estilos de cartografía de riesgo.
"""
import sys
from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer,
    QgsCoordinateReferenceSystem, QgsFillSymbol, QgsLineSymbol,
    QgsMarkerSymbol, QgsSingleSymbolRenderer, QgsCategorizedSymbolRenderer,
    QgsRendererCategory, QgsPalLayerSettings, QgsVectorLayerSimpleLabeling,
    QgsTextFormat, QgsTextBufferSettings, QgsProperty, QgsGraduatedSymbolRenderer,
    QgsRendererRange, QgsSymbol,
)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QCoreApplication

argv = [a.encode('utf-8') for a in sys.argv]
app = QgsApplication(argv, False)
QgsApplication.setPrefixPath(r'D:/Program Files/QGIS 3.44.7/apps/qgis', True)
QgsApplication.initQgis()

PROY = r'H:/Mi unidad/2026/erum/purace/master_purace.qgz'
PROC = r'H:/Mi unidad/2026/erum/purace/geo/processed'
RAIZ = r'H:/Mi unidad/2026/erum/purace'

p = QgsProject.instance()
ok = p.read(PROY)
print('leido:', ok)

# ---- 1. Limpieza ----
for l in list(p.mapLayers().values()):
    name = l.name()
    if name.startswith('sgc_amenaza_purace'):
        p.removeMapLayer(l.id())
        print('quitado PDF:', name)
    elif name in ('dane_departamentos', 'dane_municipios', 'dane_cabeceras', 'dane_veredas'):
        src = l.source() if hasattr(l, 'source') else ''
        if '/geo/raw/' in src:
            p.removeMapLayer(l.id())
            print('quitado raw:', name)

# Capas que ya existen en el proyecto
existentes = {l.name(): l for l in p.mapLayers().values()}
print('capas restantes:', list(existentes.keys()))


# ---- 2. Helpers de estilo ----
def color(hexstr, alpha=255):
    c = QColor(hexstr)
    c.setAlpha(alpha)
    return c


def load_layer(nombre_archivo, nombre_capa, wkb_tipo):
    ruta = PROC + '/' + nombre_archivo
    layer = QgsVectorLayer(ruta, nombre_capa, 'ogr')
    if not layer.isValid():
        print('  ERROR capa no válida:', ruta)
        return None
    p.addMapLayer(layer)
    print('  cargada:', nombre_capa)
    return layer


def fill_simplex(color_fill, width=0.4, color_border=None, style_fill='solid'):
    if color_border is None:
        color_border = color_fill
    sym = QgsFillSymbol.createSimple({
        'color': color_fill.name(), 'color_border': color_border.name(),
        'width_border': str(width), 'style': style_fill})
    return sym


def line_style(color_line, width, dash=None, halo_color=None):
    sym = QgsLineSymbol.createSimple({
        'color': color_line.name(), 'width': str(width),
        'line_style': ('dash' if dash else 'solid')})
    if halo_color:
        sym.setColor(color_line)
    return sym


def marker_style(color_marker, size=3.0, shape='circle', outline=None, outline_w=0.6):
    props = {'name': shape, 'color': color_marker.name(), 'size': str(size)}
    if outline:
        props.update({'color_border': outline.name(), 'width_border': str(outline_w)})
    sym = QgsMarkerSymbol.createSimple(props)
    return sym


def set_labels(layer, campo, size=9, color_txt=QColor('#222222'), min_scale=0, max_scale=0,
               halo=True):
    settings = QgsPalLayerSettings()
    settings.fieldName = campo
    settings.placement = QgsPalLayerSettings.AroundPoint
    fmt = QgsTextFormat()
    fmt.setFont(QgsApplication.font())
    fmt.setSize(size)
    fmt.setColor(color_txt)
    if halo:
        buf = QgsTextBufferSettings()
        buf.setEnabled(True)
        buf.setSize(0.8)
        buf.setColor(QColor(255, 255, 255, 220))
        fmt.setBuffer(buf)
    settings.setFormat(fmt)
    if min_scale:
        settings.minimumScale = min_scale
    if max_scale:
        settings.maximumScale = max_scale
    labels = QgsVectorLayerSimpleLabeling(settings)
    layer.setLabeling(labels)
    layer.setLabelsEnabled(True)


def set_categorized(layer, campo, categorias, default_color=None, alpha_fill=200):
    """categorias: [(valor, hexcolor, label)]"""
    cats = []
    for valor, hexc, label in categorias:
        sym = QgsFillSymbol.createSimple({
            'color': color(hexc, alpha_fill).name(),
            'color_border': color(hexc, 255).name(),
            'width_border': '0.5'})
        cats.append(QgsRendererCategory(valor, sym, label))
    if default_color:
        dsym = QgsFillSymbol.createSimple({
            'color': color(default_color, alpha_fill).name(),
            'color_border': color(default_color, 255).name(), 'width_border': '0.5'})
    else:
        dsym = QgsFillSymbol.createSimple({'color': '#cccccc', 'color_border': '#666666', 'width_border': '0.4'})
    renderer = QgsCategorizedSymbolRenderer(campo, cats)
    if default_color:
        renderer.setSourceSymbol(dsym)
    layer.setRenderer(renderer)


# ---- 3. Cargar capas procesadas (completas, sin clip) ----
print('\n== Cargando capas ==')
# Contexto
departamentos = load_layer('dane_departamentos.geojson', 'DANE Departamentos', 6)
municipios = load_layer('dane_municipios.geojson', 'DANE Municipios', 6)
veredas = load_layer('dane_veredas.geojson', 'DANE Veredas', 6)
cabeceras = load_layer('dane_cabeceras.geojson', 'DANE Cabeceras', 0)
# SGC
amenaza = load_layer('sgc_amenaza.geojson', 'SGC Amenaza volcánica', 6)
piroclastos = load_layer('sgc_piroclastos.geojson', 'SGC Piroclastos', 1)
volcan = load_layer('sgc_volcan_punto.geojson', 'SGC Volcán Puracé (cráter)', 0)

print('\n== Aplicando estilos ==')

# ---- Veredas: contexto fino ----
if veredas:
    veredas.setRenderer(QgsSingleSymbolRenderer(
        fill_simplex(QColor(0, 0, 0, 0), width=0.25,
                     color_border=QColor('#bdbdbd'), style_fill='no')))

# ---- Municipios: fill crema 10%, borde gris medio ----
if municipios:
    sym_m = QgsFillSymbol.createSimple({
        'color': '#f7f3e9', 'color_border': '#7f7f7f', 'width_border': '0.6'})
    sym_m.setOpacity(0.65)
    municipios.setRenderer(QgsSingleSymbolRenderer(sym_m))
    # Halo + borde más grueso para nombres
    set_labels(municipios, 'mpio_cnmbr', size=9, color_txt=QColor('#404040'),
               max_scale=1500000)

# ---- Departamentos: solo borde ----
if departamentos:
    departamentos.setRenderer(QgsSingleSymbolRenderer(
        fill_simplex(QColor(0, 0, 0, 0), width=1.2,
                     color_border=QColor('#4d4d4d'), style_fill='no')))

# ---- Cabeceras: punto morado + etiqueta ----
if cabeceras:
    cabeceras.setRenderer(QgsSingleSymbolRenderer(
        marker_style(QColor('#6a3d9a'), size=5.0,
                     shape='circle', outline=QColor('#ffffff'), outline_w=1.2)))
    set_labels(cabeceras, 'zu_cnmbre', size=10, color_txt=QColor('#3b1f5e'),
               max_scale=1200000)

# ---- Amenaza: categorizado ----
if amenaza:
    set_categorized(amenaza, 'AMENAZA',
                    [('Amenaza Alta', '#d7191c', 'Alta'),
                     ('Amenaza Media', '#fdae61', 'Media'),
                     ('Amenaza Baja', '#ffffbf', 'Baja')],
                    default_color='#cccccc', alpha_fill=190)
    amenaza.setOpacity(0.8)

# ---- Piroclastos: línea discontinua naranja ----
if piroclastos:
    sym_p = QgsLineSymbol.createSimple({
        'color': '#e84a25', 'width': '1.6', 'line_style': 'dash'})
    sym_p.setOpacity(0.9)
    piroclastos.setRenderer(QgsSingleSymbolRenderer(sym_p))

# ---- Volcán: estrella roja destacada ----
if volcan:
    sym_v = QgsMarkerSymbol.createSimple({
        'name': 'star', 'color': '#e60000', 'size': '9.0',
        'color_border': '#ffffff', 'width_border': '1.5'})
    volcan.setRenderer(QgsSingleSymbolRenderer(sym_v))
    set_labels(volcan, 'VOLCAN', size=11, color_txt=QColor('#a00000'))

# ---- Anillos GPKG (re-estilizar si existe) ----
anillos = existentes.get('referencia_anillos \u2014 anillos_km') or \
          existentes.get('referencia_anillos \u2014 anillos_km')
gpkg_layer = None
for l in p.mapLayers().values():
    if l.name().endswith('anillos_km'):
        gpkg_layer = l
        break
if gpkg_layer:
    # Graduado por campo de distancia si existe, si no usar valores fijos
    campo_dist = None
    for f in gpkg_layer.getFeatures():
        for c in ['radio_km', 'dist_km', 'km', 'RADIO_KM', 'radio']:
            if c in f.fields().names():
                campo_dist = c
                break
        if campo_dist:
            break
    if campo_dist:
        ranges = [(0, 5.5, '5 km', '#d7191c'),
                  (5.5, 15.5, '15 km', '#f47d1b'),
                  (15.5, 30.5, '30 km', '#2b9c3f')]
        cats = []
        for lo, hi, label, hexc in ranges:
            sym = QgsFillSymbol.createSimple({
                'color': color(hexc, 40).name(), 'color_border': color(hexc, 255).name(),
                'width_border': '0.9'})
            cats.append(QgsRendererRange(lo, hi, sym, label))
        renderer = QgsGraduatedSymbolRenderer(campo_dist, cats)
        gpkg_layer.setRenderer(renderer)
        print('  anillos: estilo graduado por', campo_dist)
    else:
        sym_a = QgsFillSymbol.createSimple({'color': '#d7191c', 'color_border': '#d7191c', 'width_border': '0.9'})
        gpkg_layer.setRenderer(QgsSingleSymbolRenderer(sym_a))

puntos = None
for l in p.mapLayers().values():
    if l.name().endswith('puntos_referencia'):
        puntos = l
        break
if puntos:
    puntos.setRenderer(QgsSingleSymbolRenderer(
        marker_style(QColor('#2166ac'), size=4.0,
                     shape='circle', outline=QColor('#ffffff'), outline_w=1.0)))

# ---- 4. CRS del proyecto ----
p.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))

# ---- 5. Guardar ----
p.write()
print('\nGUARDADO OK:', PROY)
print('capas finales:', [l.name() for l in p.mapLayers().values()])

QgsApplication.exitQgis()
print('DONE')
