// ERUM Atlas - Puracé - Aplicación Principal

// Variables globales
let leafletMap = null;
let cesiumViewer = null;
let currentView = '2D';
let leafletLayers = {};
let cesiumDataSources = {};

// Configuración de capas
const LAYERS_CONFIG = [
    {
        id: 'curvas_50m',
        name: 'Curvas 50m',
        group: 'Relieve',
        url: '../geo/processed/curvas_50m.geojson',
        visible: true,
        leafletStyle: 'curvas_50m',
        cesiumStyle: 'curvas_50m',
        type: 'line'
    },
    {
        id: 'curvas_maestras_250m',
        name: 'Curvas 250m',
        group: 'Relieve',
        url: '../geo/processed/curvas_maestras_250m.geojson',
        visible: true,
        leafletStyle: 'curvas_maestras_250m',
        cesiumStyle: 'curvas_maestras_250m',
        type: 'line'
    },
    {
        id: 'vias_principales',
        name: 'Vías Principales',
        group: 'Vías',
        url: '../geo/raw/osm_vias.geojson',
        visible: true,
        leafletStyle: 'vias_principales',
        cesiumStyle: 'vias_principales',
        type: 'line'
    },
    {
        id: 'hospitales',
        name: 'Hospitales',
        group: 'Infraestructura',
        url: '../geo/raw/osm_hospitales.geojson',
        visible: true,
        leafletStyle: 'hospital',
        cesiumStyle: 'hospital',
        type: 'point'
    },
    {
        id: 'policia',
        name: 'Policía',
        group: 'Infraestructura',
        url: '../geo/raw/osm_policia.geojson',
        visible: true,
        leafletStyle: 'policia',
        cesiumStyle: 'policia',
        type: 'point'
    },
    {
        id: 'bancos',
        name: 'Bancos',
        group: 'Infraestructura',
        url: '../geo/raw/osm_bancos.geojson',
        visible: true,
        leafletStyle: 'banco',
        cesiumStyle: 'banco',
        type: 'point'
    },
    {
        id: 'negocios',
        name: 'Negocios',
        group: 'Infraestructura',
        url: '../geo/raw/osm_negocios.geojson',
        visible: false,
        leafletStyle: 'negocio',
        cesiumStyle: 'negocio',
        type: 'point'
    },
    {
        id: 'gasolineras',
        name: 'Gasolineras',
        group: 'Infraestructura',
        url: '../geo/raw/osm_gasolineras.geojson',
        visible: true,
        leafletStyle: 'gasolinera',
        cesiumStyle: 'gasolinera',
        type: 'point'
    },
    {
        id: 'amenaza',
        name: 'Amenaza Volcánica',
        group: 'Volcán',
        url: '../geo/processed/sgc_amenaza.geojson',
        visible: true,
        leafletStyle: 'amenaza_alta',
        cesiumStyle: 'amenaza_alta',
        type: 'polygon'
    },
    {
        id: 'volcan',
        name: 'Volcán Puracé',
        group: 'Volcán',
        url: '../geo/processed/sgc_volcan_punto.geojson',
        visible: true,
        leafletStyle: 'volcan',
        cesiumStyle: 'volcan',
        type: 'point'
    },
    {
        id: 'viento',
        name: 'Viento (última hora)',
        group: 'Simulación',
        url: '../geo/wind/wind_2026-08-06_2300.geojson',
        visible: false,
        leafletStyle: 'viento',
        cesiumStyle: 'viento',
        type: 'point'
    },
    {
        id: 'ceniza',
        name: 'Ceniza Contornos',
        group: 'Simulación',
        url: '../geo/ash_contours/conc_5km_20260806_2300.geojson',
        visible: false,
        leafletStyle: 'ceniza_contorno',
        cesiumStyle: 'ceniza_contorno',
        type: 'polygon'
    }
];

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    initApp();
});

function initApp() {
    leafletMap = initLeaflet();
    setupViewControls();
    loadAllLayers();
    createLayerPanel();
}

function setupViewControls() {
    document.getElementById('btn2D').addEventListener('click', () => switchView('2D'));
    document.getElementById('btn3D').addEventListener('click', () => switchView('3D'));
    document.getElementById('btnSplit').addEventListener('click', () => switchView('split'));
}

function switchView(view) {
    currentView = view;
    const leafletContainer = document.getElementById('leafletContainer');
    const cesiumContainer = document.getElementById('cesiumContainer');
    
    document.querySelectorAll('.controls button').forEach(b => b.classList.remove('active'));
    document.getElementById('btn' + (view === '2D' ? '2D' : view === '3D' ? '3D' : 'Split')).classList.add('active');
    
    leafletContainer.classList.add('hidden');
    cesiumContainer.classList.add('hidden');
    leafletContainer.style.flex = '1';
    cesiumContainer.style.flex = '1';
    
    switch(view) {
        case '2D':
            leafletContainer.classList.remove('hidden');
            leafletMap.invalidateSize();
            break;
        case '3D':
            cesiumContainer.classList.remove('hidden');
            if (!cesiumViewer) {
                cesiumViewer = initCesium();
                setupCesiumPopup(cesiumViewer);
                loadAllLayersCesium();
            }
            break;
        case 'split':
            leafletContainer.classList.remove('hidden');
            cesiumContainer.classList.remove('hidden');
            leafletMap.invalidateSize();
            if (!cesiumViewer) {
                cesiumViewer = initCesium();
                setupCesiumPopup(cesiumViewer);
                loadAllLayersCesium();
            }
            break;
    }
}

function loadAllLayers() {
    LAYERS_CONFIG.forEach(layerConfig => {
        if (layerConfig.visible) {
            loadLayerLeaflet(layerConfig);
        }
    });
}

function loadLayerLeaflet(layerConfig) {
    const style = LEAFLET_STYLES[layerConfig.leafletStyle] || {};
    loadGeoJSONLeaflet(leafletMap, layerConfig.url, style, function(feature, layer) {
        layer.bindPopup(getPopupContent(feature));
    }).then(layer => {
        if (layer) leafletLayers[layerConfig.id] = layer;
    });
}

function loadAllLayersCesium() {
    LAYERS_CONFIG.forEach(layerConfig => {
        if (layerConfig.visible) {
            loadLayerCesium(layerConfig);
        }
    });
}

function loadLayerCesium(layerConfig) {
    const style = CESIUM_STYLES[layerConfig.cesiumStyle] || {};
    loadGeoJSONCesium(cesiumViewer, layerConfig.url, style).then(dataSource => {
        if (dataSource) cesiumDataSources[layerConfig.id] = dataSource;
    });
}

function createLayerPanel() {
    const panel = document.getElementById('layerControls');
    const groups = {};
    
    LAYERS_CONFIG.forEach(layerConfig => {
        if (!groups[layerConfig.group]) groups[layerConfig.group] = [];
        groups[layerConfig.group].push(layerConfig);
    });
    
    let html = '';
    Object.keys(groups).forEach(groupName => {
        html += '<div class="layer-group">';
        html += '<h4 style="margin:10px 0 5px;color:#e94560;font-size:0.9em;">' + groupName + '</h4>';
        groups[groupName].forEach(layerConfig => {
            const checked = layerConfig.visible ? 'checked' : '';
            html += '<div class="layer-item">';
            html += '<input type="checkbox" id="layer_' + layerConfig.id + '" ' + checked;
            html += ' onchange="toggleLayer(\'' + layerConfig.id + '\', this.checked)">';
            html += '<label for="layer_' + layerConfig.id + '">' + layerConfig.name + '</label>';
            html += '</div>';
        });
        html += '</div>';
    });
    
    panel.innerHTML = html;
}

function toggleLayer(layerId, visible) {
    const layerConfig = LAYERS_CONFIG.find(l => l.id === layerId);
    if (!layerConfig) return;
    
    if (visible) {
        if (!leafletLayers[layerId]) {
            loadLayerLeaflet(layerConfig);
        } else {
            leafletMap.addLayer(leafletLayers[layerId]);
        }
    } else {
        if (leafletLayers[layerId]) {
            leafletMap.removeLayer(leafletLayers[layerId]);
        }
    }
    
    if (cesiumViewer) {
        if (visible) {
            if (!cesiumDataSources[layerId]) {
                loadLayerCesium(layerConfig);
            } else {
                cesiumViewer.dataSources.add(cesiumDataSources[layerId]);
            }
        } else {
            if (cesiumDataSources[layerId]) {
                cesiumViewer.dataSources.remove(cesiumDataSources[layerId], false);
            }
        }
    }
}
