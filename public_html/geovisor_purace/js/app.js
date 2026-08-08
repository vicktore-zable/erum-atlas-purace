/* =========================================================
   Geovisor ERUM Atlas — app.js
   Leaflet + dark glass UI (per geoviewer_ux_prompt.md)
   ========================================================= */
(function () {
  'use strict';

  /* ---------- Config de mapas base ---------- */
  var BASEMAPS = {
    osm: {
      label: 'OpenStreetMap',
      icon: 'fa fa-map',
      layer: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
      })
    },
    satellite: {
      label: 'Sat\u00e9lite',
      icon: 'fa fa-satellite',
      layer: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        attribution: 'Tiles &copy; Esri'
      })
    },
    dark: {
      label: 'OSM Oscuro',
      icon: 'fa fa-moon',
      layer: L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap &copy; CARTO'
      })
    }
  };

  /* ---------- Estilos por capa (fieles a master_purace.qgz) ---------- */
  var ESTILOS = {
    'SGC Amenaza': function (f) {
      var a = (f.properties.AMENAZA || '').toLowerCase();
      var c = '#cccccc', o = 0.85;
      if (a.indexOf('alta') >= 0) { c = '#d7191c'; o = 0.9; }
      else if (a.indexOf('media') >= 0) { c = '#fdae61'; o = 0.9; }
      else if (a.indexOf('baja') >= 0) { c = '#ffffbf'; o = 0.9; }
      return { color: c, weight: 0.5, fillColor: c, fillOpacity: o };
    },
    'SGC Piroclastos': { type: 'line', color: '#e84a25', weight: 1.4, dashArray: '4 3', opacity: 0.9 },
    'SGC Volc\u00e1n Purac\u00e9': { type: 'point', color: '#e60000', icon: '<i class="fa fa-star" style="color:#e60000;font-size:20px;filter:drop-shadow(0 0 3px #f00)"></i>', iconSize: [22, 22], iconAnchor: [11, 11] },
    'V\u00edas DANE MGN': {
      type: 'line',
      style: function (f) {
        var t = f.properties.type || 'other';
        var m = {
          motorway: { color: '#e63946', weight: 2.8, opacity: 0.9 },
          trunk: { color: '#e63946', weight: 2.4, opacity: 0.9 },
          primary: { color: '#f4a261', weight: 2.0, opacity: 0.9 },
          secondary: { color: '#e9c46a', weight: 1.6, opacity: 0.85 },
          tertiary: { color: '#d5c27c', weight: 1.2, opacity: 0.8 },
          residential: { color: '#c9c4ad', weight: 1.0, opacity: 0.7 },
          service: { color: '#9aa0a6', weight: 0.8, opacity: 0.6 },
          track: { color: '#8f8f8f', weight: 0.8, opacity: 0.6 }
        };
        return m[t] || { color: '#97979b', weight: 0.8, opacity: 0.5 };
      }
    },
    'Nomenclatura vial': { type: 'line', color: '#e15989', weight: 0.8, opacity: 0.6 },
    'Caminos': { type: 'line', color: '#d97706', weight: 0.6, opacity: 0.45 },
    'Cultura puntos rurales': { type: 'point', color: '#e5b636', icon: '<i class="fa fa-map-marker-alt" style="color:#e5b636;font-size:13px"></i>', iconSize: [14, 14], iconAnchor: [7, 12] },
    'Curvas de nivel': { type: 'line', color: '#9b9fa6', weight: 0.4, opacity: 0.4 },
    'Hidrograf\u00eda rural': { type: 'line', color: '#2196f3', weight: 0.9, opacity: 0.7 },
    'Zona urbana': { type: 'polygon', color: '#ffa6b8', weight: 0.6, fillColor: '#ffa6b8', fillOpacity: 0.12 },
    'Departamentos': { type: 'line', color: '#4f4f4f', weight: 1.1, opacity: 0.8 },
    'Municipios': { type: 'polygon', color: '#7f7f7f', weight: 0.7, fillColor: '#f7f3e9', fillOpacity: 0.1 },
    'Veredas': { type: 'polygon', color: '#94a3b8', weight: 0.6, fillColor: '#94a3b8', fillOpacity: 0.05 }
  };

  // Badge color por capa (para la tarjeta)
  function colorDeCapa(meta) {
    var st = ESTILOS[meta.nombre];
    if (meta.nombre === 'SGC Amenaza') return '#d7191c';
    if (meta.nombre === 'V\u00edas DANE MGN') return '#e63946';
    if (!st) return '#e2e8f0';
    if (st.color) return st.color;
    if (st.style) return '#d28c2f';
    return '#38bdf8';
  }
  var badgeColor = colorDeCapa;

  /* ---------- Estado global ---------- */
  var activeBasemapKey = 'osm';
  var layerStates = {};   // slug -> { meta, visible, loading, layer }
  var geoCache = {};      // slug -> GeoJSON
  var inFlight = {};      // slug -> Promise
  var gruposMeta = null;

  /* ---------- Utils ---------- */
  function esc(s) {
    var d = document.createElement('div');
    d.textContent = (s === null || s === undefined) ? '' : String(s);
    return d.innerHTML;
  }

  function $(sel, root) { return (root || document).querySelector(sel); }

  function popupHTML(p) {
    var rows = '';
    var seen = 0;
    for (var k in p) {
      var v = p[k];
      if (v === null || v === undefined) continue;
      var s = String(v);
      if (s === '' || s === '0' || s === 'NULL' || s === 'None' || s === '0.0' || s === '0,0') continue;
      rows += '<tr><td>' + esc(k) + '</td><td>' + esc(s) + '</td></tr>';
      seen++;
    }
    if (!seen) return '<p style="opacity:.6">Sin atributos</p>';
    return '<div class="attr"><table>' + rows + '</table></div>';
  }

  function tooltipText(p) {
    var keys = ['UNAMBRE', 'UNOM_NANO', 'unom_nano', 'name', 'NOMBRE_VER', 'NOMBRE', 'NOMBRE_MPIO', 'mpio_cnmbr', 'RHDL_NANO', 'RHPL_NANO', 'RCTL_NANO', 'VRE', 'AMENAZA'];
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      if (p[k] && String(p[k]).length > 0 && String(p[k]) !== 'NULL') return String(p[k]);
    }
    return null;
  }

  /* ---------- Mapa ---------- */
  var map = L.map('map', {
    center: [2.32, -76.39],
    zoom: 11,
    minZoom: 7,
    maxZoom: 19,
    zoomControl: true,
    attributionControl: true,
    preferCanvas: true
  });

BASEMAPS.osm.layer.addTo(map);
  L.control.scale({ imperial: false, position: 'bottomleft' }).addTo(map);
  if (L.control.fullscreen) L.control.fullscreen({ position: 'topright' }).addTo(map);
  if (L.control.measure) L.control.measure({ position: 'topleft', color: '#38bdf8' }).addTo(map);

  // Fit área Puracé
  map.fitBounds([[3.10, -75.61], [1.94, -77.18]], { padding: [20, 20] });

  /* ---------- Basemap switcher ---------- */
  function setBasemap(key, btn) {
    if (key === activeBasemapKey) return;
    activeBasemapKey = key;
    Object.keys(BASEMAPS).forEach(function (k) {
      if (k === key) { if (!map.hasLayer(BASEMAPS[k].layer)) BASEMAPS[k].layer.addTo(map); }
      else if (map.hasLayer(BASEMAPS[k].layer)) map.removeLayer(BASEMAPS[k].layer);
    });
    document.querySelectorAll('.basemap-btn').forEach(function (el) {
      el.classList.toggle('active', el.dataset.key === key);
    });
  }

  /* ---------- Loading indicator ---------- */
  var loadingEl = document.getElementById('loading-indicator');
  function showLoading(show, txt) {
    var indicator = loadingEl;
    if (!indicator) indicator = document.getElementById('loading-indicator');
    if (!indicator) return;
    if (show) {
      indicator.classList.add('visible');
      var label = indicator.querySelector('span');
      if (label && txt) label.textContent = txt;
    } else {
      indicator.classList.remove('visible');
    }
  }

  /* ---------- Carga GeoJSON cacheado ---------- */
  function loadGeo(meta) {
    if (geoCache[meta.slug]) return Promise.resolve(geoCache[meta.slug]);
    if (inFlight[meta.slug]) return inFlight[meta.slug];
    inFlight[meta.slug] = fetch('data/' + meta.archivo, { cache: 'force-cache' })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + meta.archivo);
        return r.json();
      })
      .then(function (j) {
        geoCache[meta.slug] = j;
        delete inFlight[meta.slug];
        return j;
      })
      .catch(function (e) { delete inFlight[meta.slug]; throw e; });
    return inFlight[meta.slug];
  }

  /* ---------- Factory L.geoJSON ---------- */
  function makeGeoLayer(meta, gj) {
    var st = ESTILOS[meta.nombre] || {};
    var isPoint = meta.geometria === 'point';

    var opts = {
      onEachFeature: function (f, lay) {        var t = tooltipText(f.properties);
        if (t) lay.bindTooltip(t, { sticky: true });
        lay.bindPopup(popupHTML(f.properties));
      }
    };

    if (isPoint) {
      opts.pointToLayer = function (f, latlng) {
        return L.marker(latlng, { icon: L.divIcon({ html: st.icon || '<i class="fa fa-circle" style="color:' + st.color + '"></i>', iconSize: st.iconSize ? L.point(st.iconSize[0], st.iconSize[1]) : null, iconAnchor: st.iconAnchor ? L.point(st.iconAnchor[0], st.iconAnchor[1]) : null }) });
      };
    }
    if (typeof st === 'function') {
      opts.style = st;
    } else if (st.type === 'line') {
      opts.style = st.style || function () { return { color: st.color, weight: st.weight, opacity: st.opacity, dashArray: st.dashArray }; };
    } else if (st.type === 'polygon' || !st.type) {
      opts.style = function (f) {
        if (st.style) return st.style(f);
        return { color: st.color, weight: st.weight, opacity: 0.9, fillColor: st.fillColor || st.color, fillOpacity: st.fillOpacity };
      };
    }
    var layer = L.geoJSON(gj, opts);
    if (meta.minZoom > 0) layer.options.minZoom = meta.minZoom;
    return layer;
  }

  /* ---------- Toggle capa ---------- */
  function setLayerVisible(meta, on) {
    var rec = layerStates[meta.slug];
    if (!rec) return;
    rec.visible = on;
    if (on) {
      if (rec.layer) {
        if (!map.hasLayer(rec.layer)) map.addLayer(rec.layer);
        return;
      }
      if (rec.loading) return;
      rec.loading = true;
      showLoading(true, 'Cargando ' + meta.nombre + '\u2026');
      loadGeo(meta).then(function (gj) {
        rec.loading = false;
        rec.layer = makeGeoLayer(meta, gj);
        rec.layer.options.minZoom = meta.minZoom || 0;
        if (rec.visible) map.addLayer(rec.layer);
        checkZoom();
        showLoading(false);
        updateCount();
      }).catch(function (e) {
        rec.loading = false;
        showLoading(false);
        console.error(e);
        alert('Error cargando capa ' + meta.nombre + ': ' + e.message);
      });
    } else {
      if (rec.layer && map.hasLayer(rec.layer)) map.removeLayer(rec.layer);
    }
    updateCount();
  }

  /* ---------- Zoom por escala (reglas QGIS) ---------- */
  function checkZoom() {
    var z = map.getZoom();
    Object.keys(layerStates).forEach(function (slug) {
      var rec = layerStates[slug];
      if (!rec.visible || !rec.layer) return;
      var minZ = rec.meta.minZoom || 0;
      var shouldShow = z >= minZ;
      var isShown = map.hasLayer(rec.layer);
      if (shouldShow && !isShown) map.addLayer(rec.layer);
      if (!shouldShow && isShown) map.removeLayer(rec.layer);
    });
  }
  map.on('zoomend', checkZoom);

  function fitToLayer(slug) {
    var rec = layerStates[slug];
    if (!rec) return;
    if (rec.layer) {
      map.fitBounds(rec.layer.getBounds(), { padding: [40, 40], maxZoom: 15 });
    } else {
      loadGeo(rec.meta).then(function (gj) {
        var tmp = L.geoJSON(gj);
        map.fitBounds(tmp.getBounds(), { padding: [40, 40], maxZoom: 15 });
      });
    }
  }

  /* ---------- Contador badges ---------- */
  function updateCount() {
    var total = 0, vis = 0;
    Object.keys(layerStates).forEach(function (s) {
      total++;
      if (layerStates[s].visible) vis++;
    });
    var pc = document.getElementById('panel-count');
    if (pc) pc.textContent = vis + '/' + total + ' Capas';
    var tc = document.getElementById('total-capas');
    if (tc) tc.textContent = total;
  }

  /* ---------- Render del panel ---------- */
  function buildBasemapGrid() {
    var grid = document.getElementById('basemap-grid');
    grid.innerHTML = '';
    Object.keys(BASEMAPS).forEach(function (key) {
      var b = BASEMAPS[key];
      var btn = document.createElement('button');
      btn.className = 'basemap-btn' + (key === 'osm' ? ' active' : '');
      btn.dataset.key = key;
      btn.innerHTML = '<i class="' + b.icon + '"></i><span>' + b.label + '</span>';
      btn.addEventListener('click', function () { setBasemap(key); });
      grid.appendChild(btn);
    });
  }

  function buildCard(meta, parent) {
    var rec = layerStates[meta.slug] = { meta: meta, visible: false, loading: false, layer: null };
    var card = document.createElement('div');
    card.className = 'layer-card';
    var colorHex = badgeColor(meta);

    card.innerHTML =
      '<div class="layer-row">' +
        '<span class="layer-color" style="background:' + colorHex + '"></span>' +
        '<span class="layer-name">' + esc(meta.nombre) + '</span>' +
        '<label class="switch"><input type="checkbox"><span class="slider"></span></label>' +
      '</div>' +
      '<div class="layer-controls">' +
        '<span class="opacity-label">Transp: 100%</span>' +
        '<input type="range" min="0" max="100" value="100" class="opacity-slider" title="Opacidad">' +
        '<button class="fit-btn" title="Enfocar capa"><i class="fa fa-search-plus"></i></button>' +
      '</div>' +
      (meta.minZoom > 0 ? '<div class="layer-scale-note"><i class="fa fa-info-circle"></i> A partir de zoom ' + meta.minZoom + '</div>' : '');

    var cb = card.querySelector('input[type=checkbox]');
    cb.checked = !!meta.checked;
    rec.visible = !!meta.checked;

    cb.addEventListener('change', function () {
      rec.visible = cb.checked;
      if (cb.checked) loadLayerVisible(meta, rec);
      else if (rec.layer && map.hasLayer(rec.layer)) map.removeLayer(rec.layer);
      updateCount();
    });

    var slider = card.querySelector('.opacity-slider');
    var lbl = card.querySelector('.opacity-label');
    slider.addEventListener('input', function () {
      var v = +slider.value;
      lbl.textContent = 'Transp: ' + v + '%';
      if (rec.layer && rec.layer.setStyle) {
        rec.layer.setStyle({ opacity: v / 100, fillOpacity: v / 100 });
        if (rec.layer.eachLayer) rec.layer.eachLayer(function (l) {
          if (l.setStyle) l.setStyle({ opacity: v / 100, fillOpacity: v / 100 });
        });
      }
    });

    card.querySelector('.fit-btn').addEventListener('click', function () {
      fitToLayer(meta.slug);
    });

    parent.appendChild(card);
  }

  function buildGroups(data) {
    var wrap = document.getElementById('groups-container');
    wrap.innerHTML = '';
    var grupos = {};
    data.capas.forEach(function (m) {
      if (m.grupo === 'Base Maps') return;
      if (!grupos[m.grupo]) {
        grupos[m.grupo] = [];
      }
      grupos[m.grupo].push(m);
    });
    Object.keys(grupos).forEach(function (gname) {
      var gd = document.createElement('div');
      gd.className = 'group-block';
      var head = document.createElement('div');
      head.className = 'group-head open';
      head.innerHTML = '<i class="fa fa-chevron-right fa-chevron"></i><span>' + esc(gname) + '</span>';
      var bodyItems = document.createElement('div');
      bodyItems.className = 'group-items';
      head.addEventListener('click', function () {
        gd.classList.toggle('open');
        head.querySelector('i.fa-chevron').style.transform = gd.classList.contains('open') ? 'rotate(90deg)' : '';
      });
      grupos[gname].forEach(function (m) { buildCard(m, bodyItems); });
      gd.appendChild(head);
      gd.appendChild(bodyItems);
      wrap.appendChild(gd);
    });

    // Cargar capas visibles con z invertido (Vulcanología arriba, como QGIS):
    // en el canvas Leaflet dibuja arriba la última añadida, así que cargamos de abajo hacia arriba.
    data.capas.slice().reverse().forEach(function (m) {
      if (m.grupo === 'Base Maps') return;
      if (m.checked && layerStates[m.slug]) loadLayerVisible(m, layerStates[m.slug]);
    });
    updateCount();
  }

  function loadLayerVisible(meta, rec) {
    if (rec.loading) return;
    rec.loading = true;
    showLoading(true, 'Cargando ' + meta.nombre + '\u2026');
    loadGeo(meta).then(function (gj) {
      rec.loading = false;
      rec.layer = makeGeoLayer(meta, gj);
      if (rec.visible) map.addLayer(rec.layer);
      checkZoom();
      showLoading(false);
    }).catch(function (e) {
      rec.loading = false;
      showLoading(false);
      console.error(e);
    });
  }

  /* ---------- Init ---------- */
  function init() {
    buildBasemapGrid();

    // Toggle colapso del panel
    var panel = document.getElementById('layers-panel');
    var toggleBtn = document.getElementById('panel-toggle');
    if (panel && toggleBtn) {
      toggleBtn.addEventListener('click', function () {
        var collapsed = panel.classList.toggle('collapsed');
        toggleBtn.innerHTML = collapsed ? '<i class="fas fa-chevron-down"></i>' : '<i class="fas fa-chevron-up"></i>';
      });
    }

    fetch('capas.json')
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (data) {
        buildGroups(data);
      })
      .catch(function (e) {
        console.error('No se pudo cargar capas.json', e);
        document.getElementById('groups-container').innerHTML = '<p style="padding:12px;color:#f87171">Error cargando capas.json: ' + esc(e.message) + '</p>';
      });

    // Icono de regla en medida
    setTimeout(function () {
      var m = document.querySelector('.leaflet-control-measure a');
      if (m) m.innerHTML = '<i class="fa fa-ruler"></i>';
    }, 800);
  }

  document.addEventListener('DOMContentLoaded', init);
})();