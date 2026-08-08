// Configuración Cesium 3D
const CESIUM_CONFIG = {
    center: Cesium.Cartesian3.fromDegrees(-76.397222, 2.313889, 10000),
    orientation: {
        heading: Cesium.Math.toRadians(0),
        pitch: Cesium.Math.toRadians(-45),
        roll: 0
    }
};

// Token Cesium Ion - purace
Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIzYjRkZTliNi02NTY2LTRjZTAtOGJlOS01MDI5Y2FmYWE2MGEiLCJpZCI6ODYwMjUsInN1YiI6InZpY3RvcmZhYmlvY2FzdHJvIiwiaXNzIjoiaHR0cHM6Ly9hcGkuY2VzaXVtLmNvbSIsImF1ZCI6InB1cmFjZSIsImlhdCI6MTc4NjA2NTUxM30.vpqOzOWWH3LwWpKka1j-aLrz0I1WldUZpBwKkMmcHHM';

// Inicializar visor Cesium
function initCesium() {
    const viewer = new Cesium.Viewer('cesiumContainer', {
        terrain: Cesium.Terrain.fromWorldTerrain(),
        baseLayerPicker: true,
        geocoder: true,
        homeButton: true,
        sceneModePicker: true,
        navigationHelpButton: false,
        animation: false,
        timeline: false,
        fullscreenButton: false,
        vrButton: false,
        infoBox: true,
        selectionIndicator: true,
        shadows: false,
        shouldAnimate: true
    });

    // Posición inicial
    viewer.camera.flyTo({
        destination: CESIUM_CONFIG.center,
        orientation: CESIUM_CONFIG.orientation,
        duration: 2
    });

    return viewer;
}

// Cargar GeoJSON en Cesium
function loadGeoJSONCesium(viewer, url, options = {}) {
    return Cesium.GeoJsonDataSource.load(url, {
        stroke: options.stroke || Cesium.Color.WHITE,
        strokeWidth: options.strokeWidth || 2,
        fill: options.fill || Cesium.Color.WHITE.withAlpha(0.3),
        clampToGround: options.clampToGround !== false,
        markerColor: options.markerColor || Cesium.Color.RED,
        markerSize: options.markerSize || 12,
        markerSymbol: options.markerSymbol || ''
    }).then(dataSource => {
        viewer.dataSources.add(dataSource);
        return dataSource;
    }).catch(err => {
        console.warn(`Error cargando ${url}:`, err);
        return null;
    });
}

// Estilos para diferentes capas en Cesium
const CESIUM_STYLES = {
    // Curvas de nivel
    curvas_50m: {
        stroke: Cesium.Color.GRAY.withAlpha(0.6),
        strokeWidth: 1,
        fill: Cesium.Color.TRANSPARENT,
        clampToGround: true
    },
    curvas_maestras_250m: {
        stroke: Cesium.Color.DARKGRAY.withAlpha(0.8),
        strokeWidth: 2,
        fill: Cesium.Color.TRANSPARENT,
        clampToGround: true
    },
    
    // Vías
    vias_principales: {
        stroke: Cesium.Color.fromCssColorString('#e63946'),
        strokeWidth: 4,
        fill: Cesium.Color.TRANSPARENT,
        clampToGround: true
    },
    vias_secundarias: {
        stroke: Cesium.Color.fromCssColorString('#f4a261'),
        strokeWidth: 2,
        fill: Cesium.Color.TRANSPARENT,
        clampToGround: true
    },
    vias_locales: {
        stroke: Cesium.Color.fromCssColorString('#e9c46a'),
        strokeWidth: 1,
        fill: Cesium.Color.TRANSPARENT,
        clampToGround: true
    },
    
    // Amenaza volcánica
    amenaza_alta: {
        stroke: Cesium.Color.RED.withAlpha(0.8),
        strokeWidth: 2,
        fill: Cesium.Color.RED.withAlpha(0.3),
        clampToGround: true
    },
    amenaza_media: {
        stroke: Cesium.Color.ORANGE.withAlpha(0.8),
        strokeWidth: 2,
        fill: Cesium.Color.ORANGE.withAlpha(0.3),
        clampToGround: true
    },
    amenaza_baja: {
        stroke: Cesium.Color.YELLOW.withAlpha(0.8),
        strokeWidth: 2,
        fill: Cesium.Color.YELLOW.withAlpha(0.3),
        clampToGround: true
    },
    
    // Contornos ceniza
    ceniza_contorno: {
        stroke: Cesium.Color.fromCssColorString('#e94560'),
        strokeWidth: 1,
        fill: Cesium.Color.fromCssColorString('#e94560').withAlpha(0.2),
        clampToGround: true
    },
    
    // Hospitales
    hospital: {
        markerColor: Cesium.Color.RED,
        markerSize: 16,
        markerSymbol: '+'
    },
    
    // Policía
    policia: {
        markerColor: Cesium.Color.BLUE,
        markerSize: 14,
        markerSymbol: 'police'
    },
    
    // Bancos
    banco: {
        markerColor: Cesium.Color.YELLOW,
        markerSize: 12,
        markerSymbol: '$'
    },
    
    // Negocios
    negocio: {
        markerColor: Cesium.Color.GREEN,
        markerSize: 10,
        markerSymbol: 'shop'
    },
    
    // Gasolineras
    gasolinera: {
        markerColor: Cesium.Color.ORANGE,
        markerSize: 12,
        markerSymbol: 'fuel'
    },
    
    // Volcán
    volcan: {
        markerColor: Cesium.Color.RED,
        markerSize: 20,
        markerSymbol: 'volcano'
    }
};

// Configurar popup en Cesium
function setupCesiumPopup(viewer) {
    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
    
    handler.setInputAction(function(click) {
        const pickedObject = viewer.scene.pick(click.position);
        
        if (Cesium.defined(pickedObject) && Cesium.defined(pickedObject.id)) {
            const entity = pickedObject.id;
            
            if (entity.properties) {
                const props = entity.properties.getValue(viewer.clock.currentTime);
                let content = '<div style="max-width:300px;">';
                
                if (props.name) content += `<b>${props.name}</b><br>`;
                if (props.tipo) content += `<i>${props.tipo}</i><br>`;
                if (props.highway) content += `Vía: ${props.highway}<br>`;
                if (props.amenity) content += `Servicio: ${props.amenity}<br>`;
                if (props.shop) content += `Tienda: ${props.shop}<br>`;
                if (props.phone) content += `Tel: ${props.phone}<br>`;
                
                content += '</div>';
                
                viewer.infoBox.viewModel.description = content;
                viewer.infoBox.viewModel.showInfo = true;
            }
        }
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
}
