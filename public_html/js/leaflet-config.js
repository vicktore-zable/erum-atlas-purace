// Configuración Leaflet 2D
const LEAFLET_CONFIG = {
    center: [2.313889, -76.397222], // Puracé
    zoom: 11,
    minZoom: 8,
    maxZoom: 18
};

// Inicializar mapa Leaflet
function initLeaflet() {
    const map = L.map('leafletContainer', {
        center: LEAFLET_CONFIG.center,
        zoom: LEAFLET_CONFIG.zoom,
        minZoom: LEAFLET_CONFIG.minZoom,
        maxZoom: LEAFLET_CONFIG.maxZoom,
        zoomControl: true
    });

    // Capa base OSM
    const osmBase = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // Capa base Esri
    const esriBase = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: '&copy; Esri'
    });

    // Control de capas base
    const baseLayers = {
        'OpenStreetMap': osmBase,
        'Esri Imagery': esriBase
    };

    L.control.layers(baseLayers).addTo(map);

    return map;
}

// Cargar GeoJSON en Leaflet
function loadGeoJSONLeaflet(map, url, style, onEachFeature) {
    return fetch(url)
        .then(r => r.json())
        .then(data => {
            const layer = L.geoJSON(data, {
                style: style,
                onEachFeature: onEachFeature || function(feature, layer) {
                    if (feature.properties && feature.properties.name) {
                        layer.bindPopup(`<b>${feature.properties.name}</b>`);
                    }
                }
            });
            layer.addTo(map);
            return layer;
        })
        .catch(err => console.warn(`Error cargando ${url}:`, err));
}

// Estilos para diferentes tipos de capas
const LEAFLET_STYLES = {
    // Curvas de nivel
    curvas_50m: {
        color: '#999999',
        weight: 0.5,
        opacity: 0.6
    },
    curvas_maestras_250m: {
        color: '#333333',
        weight: 1.5,
        opacity: 0.8
    },
    
    // Vías
    vias_principales: {
        color: '#e63946',
        weight: 3,
        opacity: 0.9
    },
    vias_secundarias: {
        color: '#f4a261',
        weight: 2,
        opacity: 0.8
    },
    vias_locales: {
        color: '#e9c46a',
        weight: 1,
        opacity: 0.7
    },
    
    // Amenaza volcánica
    amenaza_alta: {
        color: '#d7191c',
        fillColor: '#d7191c',
        fillOpacity: 0.4,
        weight: 2
    },
    amenaza_media: {
        color: '#fdae61',
        fillColor: '#fdae61',
        fillOpacity: 0.4,
        weight: 2
    },
    amenaza_baja: {
        color: '#ffffbf',
        fillColor: '#ffffbf',
        fillOpacity: 0.4,
        weight: 2
    },
    
    // Contornos ceniza
    ceniza_contorno: {
        color: '#e94560',
        weight: 1,
        opacity: 0.7,
        fillOpacity: 0.2
    }
};

// Iconos para puntos
function createIcon(type, size = 24) {
    const icons = {
        hospital: { color: '#d62828', icon: '🏥', size: size },
        policia: { color: '#1d3557', icon: '🛡️', size: size },
        banco: { color: '#f4a261', icon: '🏦', size: size },
        negocio: { color: '#2a9d8f', icon: '🏪', size: size },
        gasolinera: { color: '#e76f51', icon: '⛽', size: size },
        volcan: { color: '#e60000', icon: '🌋', size: size + 8 }
    };
    
    const config = icons[type] || icons.negocio;
    
    return L.divIcon({
        html: `<div style="background:${config.color};width:${config.size}px;height:${config.size}px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:${config.size * 0.6}px;border:2px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.3);">${config.icon}</div>`,
        iconSize: [config.size, config.size],
        iconAnchor: [config.size / 2, config.size / 2],
        popupAnchor: [0, -config.size / 2],
        className: 'custom-icon'
    });
}

// Popup content para diferentes tipos
function getPopupContent(feature) {
    const p = feature.properties;
    let html = '<div style="max-width:250px;">';
    
    if (p.name) html += `<b>${p.name}</b><br>`;
    if (p.tipo) html += `<i>${p.tipo}</i><br>`;
    if (p.highway) html += `Vía: ${p.highway}<br>`;
    if (p.amenity) html += `Servicio: ${p.amenity}<br>`;
    if (p.shop) html += `Tienda: ${p.shop}<br>`;
    if (p.phone) html += `Tel: ${p.phone}<br>`;
    if (p.operator) html += `Operador: ${p.operator}<br>`;
    
    if (p.vel_viento_ms !== undefined) {
        html += `<br><b>Viento:</b><br>`;
        html += `Velocidad: ${p.vel_viento_ms} m/s<br>`;
        html += `Dirección: ${p.dir_viento_grados}°<br>`;
    }
    
    if (p.nivel !== undefined) {
        html += `<br><b>Ceniza:</b><br>`;
        html += `Nivel: ${p.nivel}<br>`;
        html += `Máx: ${p.valor_max} ${p.unidad}<br>`;
    }
    
    html += '</div>';
    return html;
}
