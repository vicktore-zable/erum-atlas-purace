ol.proj.proj4.register(proj4);
//ol.proj.get("EPSG:4326").setExtent([-77.813094, 1.524802, -74.977372, 3.102910]);
var wms_layers = [];


        var lyr_OpenStreetMap_0 = new ol.layer.Tile({
            'title': 'OpenStreetMap',
            'type':'base',
            'opacity': 1.000000,
            
            
            source: new ol.source.XYZ({
            attributions: ' ',
                url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
            })
        });
var format_Veredas_1 = new ol.format.GeoJSON();
var features_Veredas_1 = format_Veredas_1.readFeatures(json_Veredas_1, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:4326'});
var jsonSource_Veredas_1 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_Veredas_1.addFeatures(features_Veredas_1);
var lyr_Veredas_1 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_Veredas_1,
maxResolution:28.00446615226196,
 minResolution:0.28004466152261964,

                style: style_Veredas_1,
                popuplayertitle: 'Veredas',
                interactive: false,
                title: '<img src="styles/legend/Veredas_1.png" /> Veredas'
            });
var format_Municipios_2 = new ol.format.GeoJSON();
var features_Municipios_2 = format_Municipios_2.readFeatures(json_Municipios_2, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:4326'});
var jsonSource_Municipios_2 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_Municipios_2.addFeatures(features_Municipios_2);
var lyr_Municipios_2 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_Municipios_2,
maxResolution:70.0111653806549,
 minResolution:0.28004466152261964,

                style: style_Municipios_2,
                popuplayertitle: 'Municipios',
                interactive: true,
                title: '<img src="styles/legend/Municipios_2.png" /> Municipios'
            });
var format_Departamentos_3 = new ol.format.GeoJSON();
var features_Departamentos_3 = format_Departamentos_3.readFeatures(json_Departamentos_3, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:4326'});
var jsonSource_Departamentos_3 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_Departamentos_3.addFeatures(features_Departamentos_3);
var lyr_Departamentos_3 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_Departamentos_3, 
                style: style_Departamentos_3,
                popuplayertitle: 'Departamentos',
                interactive: true,
                title: '<img src="styles/legend/Departamentos_3.png" /> Departamentos'
            });
var format_Zonaurbana_4 = new ol.format.GeoJSON();
var features_Zonaurbana_4 = format_Zonaurbana_4.readFeatures(json_Zonaurbana_4, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:4326'});
var jsonSource_Zonaurbana_4 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_Zonaurbana_4.addFeatures(features_Zonaurbana_4);
var lyr_Zonaurbana_4 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_Zonaurbana_4,
maxResolution:28.00446615226196,
 minResolution:0.28004466152261964,

                style: style_Zonaurbana_4,
                popuplayertitle: 'Zona urbana',
                interactive: true,
                title: '<img src="styles/legend/Zonaurbana_4.png" /> Zona urbana'
            });
var format_VasDANEMGN_5 = new ol.format.GeoJSON();
var features_VasDANEMGN_5 = format_VasDANEMGN_5.readFeatures(json_VasDANEMGN_5, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:4326'});
var jsonSource_VasDANEMGN_5 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_VasDANEMGN_5.addFeatures(features_VasDANEMGN_5);
var lyr_VasDANEMGN_5 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_VasDANEMGN_5, 
                style: style_VasDANEMGN_5,
                popuplayertitle: 'Vías DANE MGN',
                interactive: true,
    title: 'Vías DANE MGN<br />\
    <img src="styles/legend/VasDANEMGN_5_0.png" /> Autopista<br />\
    <img src="styles/legend/VasDANEMGN_5_1.png" /> Troncal<br />\
    <img src="styles/legend/VasDANEMGN_5_2.png" /> Primaria<br />\
    <img src="styles/legend/VasDANEMGN_5_3.png" /> Secundaria<br />\
    <img src="styles/legend/VasDANEMGN_5_4.png" /> Terciaria<br />' });
var format_SGCVolcnPurac_6 = new ol.format.GeoJSON();
var features_SGCVolcnPurac_6 = format_SGCVolcnPurac_6.readFeatures(json_SGCVolcnPurac_6, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:4326'});
var jsonSource_SGCVolcnPurac_6 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_SGCVolcnPurac_6.addFeatures(features_SGCVolcnPurac_6);
var lyr_SGCVolcnPurac_6 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_SGCVolcnPurac_6, 
                style: style_SGCVolcnPurac_6,
                popuplayertitle: 'SGC Volcán Puracé',
                interactive: true,
                title: '<img src="styles/legend/SGCVolcnPurac_6.png" /> SGC Volcán Puracé'
            });
var format_SGCPiroclastos_7 = new ol.format.GeoJSON();
var features_SGCPiroclastos_7 = format_SGCPiroclastos_7.readFeatures(json_SGCPiroclastos_7, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:4326'});
var jsonSource_SGCPiroclastos_7 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_SGCPiroclastos_7.addFeatures(features_SGCPiroclastos_7);
var lyr_SGCPiroclastos_7 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_SGCPiroclastos_7, 
                style: style_SGCPiroclastos_7,
                popuplayertitle: 'SGC Piroclastos',
                interactive: true,
                title: '<img src="styles/legend/SGCPiroclastos_7.png" /> SGC Piroclastos'
            });
var format_SGCAmenaza_8 = new ol.format.GeoJSON();
var features_SGCAmenaza_8 = format_SGCAmenaza_8.readFeatures(json_SGCAmenaza_8, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:4326'});
var jsonSource_SGCAmenaza_8 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_SGCAmenaza_8.addFeatures(features_SGCAmenaza_8);
var lyr_SGCAmenaza_8 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_SGCAmenaza_8, 
                style: style_SGCAmenaza_8,
                popuplayertitle: 'SGC Amenaza',
                interactive: true,
    title: 'SGC Amenaza<br />\
    <img src="styles/legend/SGCAmenaza_8_0.png" /> Alta<br />\
    <img src="styles/legend/SGCAmenaza_8_1.png" /> Media<br />\
    <img src="styles/legend/SGCAmenaza_8_2.png" /> Baja<br />' });
var group_Vulcanologa = new ol.layer.Group({
                                layers: [lyr_SGCVolcnPurac_6,lyr_SGCPiroclastos_7,lyr_SGCAmenaza_8,],
                                fold: 'close',
                                title: 'Vulcanología'});
var group_Vas = new ol.layer.Group({
                                layers: [lyr_VasDANEMGN_5,],
                                fold: 'close',
                                title: 'Vías'});
var group_Administrativo = new ol.layer.Group({
                                layers: [lyr_Veredas_1,lyr_Municipios_2,lyr_Departamentos_3,lyr_Zonaurbana_4,],
                                fold: 'close',
                                title: 'Administrativo'});
var group_BaseMaps = new ol.layer.Group({
                                layers: [lyr_OpenStreetMap_0,],
                                fold: 'close',
                                title: 'Base Maps'});

lyr_OpenStreetMap_0.setVisible(true);lyr_Veredas_1.setVisible(false);lyr_Municipios_2.setVisible(true);lyr_Departamentos_3.setVisible(true);lyr_Zonaurbana_4.setVisible(true);lyr_VasDANEMGN_5.setVisible(true);lyr_SGCVolcnPurac_6.setVisible(true);lyr_SGCPiroclastos_7.setVisible(true);lyr_SGCAmenaza_8.setVisible(true);
var layersList = [group_BaseMaps,group_Administrativo,group_Vas,group_Vulcanologa];
lyr_Veredas_1.set('fieldAliases', {'fid': 'fid', 'Name': 'Name', 'description': 'description', 'timestamp': 'timestamp', 'begin': 'begin', 'end': 'end', 'altitudeMode': 'altitudeMode', 'tessellate': 'tessellate', 'extrude': 'extrude', 'visibility': 'visibility', 'drawOrder': 'drawOrder', 'icon': 'icon', 'OBJECTID': 'OBJECTID', 'DPTOMPIO': 'DPTOMPIO', 'CODIGO_VER': 'CODIGO_VER', 'NOM_DEP': 'NOM_DEP', 'NOMB_MPIO': 'NOMB_MPIO', 'NOMBRE_VER': 'NOMBRE_VER', 'VIGENCIA': 'VIGENCIA', 'FUENTE': 'FUENTE', 'DESCRIPCIO': 'DESCRIPCIO', 'SEUDONIMOS': 'SEUDONIMOS', 'AREA_HA': 'AREA_HA', 'COD_DPTO': 'COD_DPTO', 'OBSERVACIO': 'OBSERVACIO', 'CONSEJE': 'CONSEJE', 'ORIG_FID': 'ORIG_FID', 'SHAPE_Leng': 'SHAPE_Leng', 'SHAPE_Area': 'SHAPE_Area', 'layer': 'layer', 'path': 'path', });
lyr_Municipios_2.set('fieldAliases', {'dpto_ccdgo': 'dpto_ccdgo', 'mpio_ccdgo': 'mpio_ccdgo', 'mpio_cdpmp': 'mpio_cdpmp', 'dpto_cnmbr': 'dpto_cnmbr', 'mpio_cnmbr': 'mpio_cnmbr', 'mpio_crslc': 'mpio_crslc', 'mpio_tipo': 'mpio_tipo', 'mpio_narea': 'mpio_narea', 'mpio_nano': 'mpio_nano', 'shape_Leng': 'shape_Leng', 'shape_Area': 'shape_Area', });
lyr_Departamentos_3.set('fieldAliases', {'dpto_ccdgo': 'dpto_ccdgo', 'dpto_cnmbr': 'dpto_cnmbr', 'dpto_ano_c': 'dpto_ano_c', 'dpto_act_a': 'dpto_act_a', 'dpto_narea': 'dpto_narea', 'dpto_nano': 'dpto_nano', 'shape_Leng': 'shape_Leng', 'shape_Area': 'shape_Area', });
lyr_Zonaurbana_4.set('fieldAliases', {'dpto_ccdgo': 'dpto_ccdgo', 'mpio_ccdgo': 'mpio_ccdgo', 'mpio_cdpmp': 'mpio_cdpmp', 'clas_ccdgo': 'clas_ccdgo', 'setr_ccdgo': 'setr_ccdgo', 'setr_ccnct': 'setr_ccnct', 'secr_ccdgo': 'secr_ccdgo', 'secr_ccnct': 'secr_ccnct', 'zu_ccdgo': 'zu_ccdgo', 'zu_cdivi': 'zu_cdivi', 'zu_cnmbre': 'zu_cnmbre', 'zu_ccnct': 'zu_ccnct', 'zu_narea': 'zu_narea', 'zu_naltd': 'zu_naltd', 'zu_nano': 'zu_nano', 'shape_Leng': 'shape_Leng', 'shape_Area': 'shape_Area', });
lyr_VasDANEMGN_5.set('fieldAliases', {'OBJECTID': 'OBJECTID', 'FID_MGN_AD': 'FID_MGN_AD', 'DPTO_CCDGO': 'DPTO_CCDGO', 'DPTO_NANO_': 'DPTO_NANO_', 'DPTO_CNMBR': 'DPTO_CNMBR', 'DPTO_CACTO': 'DPTO_CACTO', 'DPTO_NAREA': 'DPTO_NAREA', 'DPTO_CSMBL': 'DPTO_CSMBL', 'DPTO_NANO': 'DPTO_NANO', 'PAIS_PAIS_': 'PAIS_PAIS_', 'SHAPE_Leng': 'SHAPE_Leng', 'FID_roads': 'FID_roads', 'osm_id': 'osm_id', 'name': 'name', 'ref': 'ref', 'type': 'type', 'oneway': 'oneway', 'bridge': 'bridge', 'tunnel': 'tunnel', 'maxspeed': 'maxspeed', 'SHAPE_Le_1': 'SHAPE_Le_1', });
lyr_SGCVolcnPurac_6.set('fieldAliases', {'OBJECTID': 'OBJECTID', 'ID': 'ID', 'VOLCAN': 'VOLCAN', 'ESTE': 'ESTE', 'NORTE': 'NORTE', 'LONGITUD': 'LONGITUD', 'LATITUD': 'LATITUD', 'ALTITUD': 'ALTITUD', 'WEB_OVSP': 'WEB_OVSP', 'RULEID': 'RULEID', 'CONOACTACTIVO': 'CONOACTACTIVO', });
lyr_SGCPiroclastos_7.set('fieldAliases', {'OBJECTID': 'OBJECTID', 'ID': 'ID', 'FENOMENOS': 'FENOMENOS', 'LEYENDA_1': 'LEYENDA_1', 'LEYENDA_2': 'LEYENDA_2', 'VOLCAN': 'VOLCAN', 'AMENAZA': 'AMENAZA', 'AREA_KM2': 'AREA_KM2', 'RADIO_KM': 'RADIO_KM', 'RULEID': 'RULEID', 'SHAPE.LEN': 'SHAPE.LEN', });
lyr_SGCAmenaza_8.set('fieldAliases', {'OBJECTID': 'OBJECTID', 'ID': 'ID', 'FENOMENOS': 'FENOMENOS', 'LEYENDA_1': 'LEYENDA_1', 'LEYENDA_2': 'LEYENDA_2', 'LEYENDA_3': 'LEYENDA_3', 'LEYENDA_4': 'LEYENDA_4', 'VOLCAN': 'VOLCAN', 'AMENAZA': 'AMENAZA', 'AREA_KM2': 'AREA_KM2', 'RULEID': 'RULEID', 'SHAPE.AREA': 'SHAPE.AREA', 'SHAPE.LEN': 'SHAPE.LEN', });
lyr_Veredas_1.set('fieldImages', {'fid': 'Range', 'Name': 'TextEdit', 'description': 'TextEdit', 'timestamp': 'TextEdit', 'begin': 'TextEdit', 'end': 'TextEdit', 'altitudeMode': 'TextEdit', 'tessellate': 'TextEdit', 'extrude': 'TextEdit', 'visibility': 'TextEdit', 'drawOrder': 'TextEdit', 'icon': 'TextEdit', 'OBJECTID': 'TextEdit', 'DPTOMPIO': 'TextEdit', 'CODIGO_VER': 'TextEdit', 'NOM_DEP': 'TextEdit', 'NOMB_MPIO': 'TextEdit', 'NOMBRE_VER': 'TextEdit', 'VIGENCIA': 'TextEdit', 'FUENTE': 'TextEdit', 'DESCRIPCIO': 'TextEdit', 'SEUDONIMOS': 'TextEdit', 'AREA_HA': 'TextEdit', 'COD_DPTO': 'TextEdit', 'OBSERVACIO': 'TextEdit', 'CONSEJE': 'TextEdit', 'ORIG_FID': 'TextEdit', 'SHAPE_Leng': 'TextEdit', 'SHAPE_Area': 'TextEdit', 'layer': 'TextEdit', 'path': 'TextEdit', });
lyr_Municipios_2.set('fieldImages', {'dpto_ccdgo': 'TextEdit', 'mpio_ccdgo': 'TextEdit', 'mpio_cdpmp': 'TextEdit', 'dpto_cnmbr': 'TextEdit', 'mpio_cnmbr': 'TextEdit', 'mpio_crslc': 'TextEdit', 'mpio_tipo': 'TextEdit', 'mpio_narea': 'TextEdit', 'mpio_nano': 'Range', 'shape_Leng': 'TextEdit', 'shape_Area': 'TextEdit', });
lyr_Departamentos_3.set('fieldImages', {'dpto_ccdgo': '', 'dpto_cnmbr': '', 'dpto_ano_c': '', 'dpto_act_a': '', 'dpto_narea': '', 'dpto_nano': '', 'shape_Leng': '', 'shape_Area': '', });
lyr_Zonaurbana_4.set('fieldImages', {'dpto_ccdgo': 'TextEdit', 'mpio_ccdgo': 'TextEdit', 'mpio_cdpmp': 'TextEdit', 'clas_ccdgo': 'TextEdit', 'setr_ccdgo': 'TextEdit', 'setr_ccnct': 'TextEdit', 'secr_ccdgo': 'TextEdit', 'secr_ccnct': 'TextEdit', 'zu_ccdgo': 'TextEdit', 'zu_cdivi': 'TextEdit', 'zu_cnmbre': 'TextEdit', 'zu_ccnct': 'TextEdit', 'zu_narea': 'TextEdit', 'zu_naltd': 'TextEdit', 'zu_nano': 'Range', 'shape_Leng': 'TextEdit', 'shape_Area': 'TextEdit', });
lyr_VasDANEMGN_5.set('fieldImages', {'OBJECTID': 'Range', 'FID_MGN_AD': 'Range', 'DPTO_CCDGO': 'TextEdit', 'DPTO_NANO_': 'Range', 'DPTO_CNMBR': 'TextEdit', 'DPTO_CACTO': 'TextEdit', 'DPTO_NAREA': 'TextEdit', 'DPTO_CSMBL': 'TextEdit', 'DPTO_NANO': 'Range', 'PAIS_PAIS_': 'TextEdit', 'SHAPE_Leng': 'TextEdit', 'FID_roads': 'Range', 'osm_id': 'TextEdit', 'name': 'TextEdit', 'ref': 'TextEdit', 'type': 'TextEdit', 'oneway': 'Range', 'bridge': 'Range', 'tunnel': 'Range', 'maxspeed': 'Range', 'SHAPE_Le_1': 'TextEdit', });
lyr_SGCVolcnPurac_6.set('fieldImages', {'OBJECTID': '', 'ID': '', 'VOLCAN': '', 'ESTE': '', 'NORTE': '', 'LONGITUD': '', 'LATITUD': '', 'ALTITUD': '', 'WEB_OVSP': '', 'RULEID': '', 'CONOACTACTIVO': '', });
lyr_SGCPiroclastos_7.set('fieldImages', {'OBJECTID': '', 'ID': '', 'FENOMENOS': '', 'LEYENDA_1': '', 'LEYENDA_2': '', 'VOLCAN': '', 'AMENAZA': '', 'AREA_KM2': '', 'RADIO_KM': '', 'RULEID': '', 'SHAPE.LEN': '', });
lyr_SGCAmenaza_8.set('fieldImages', {'OBJECTID': 'Range', 'ID': 'Range', 'FENOMENOS': 'TextEdit', 'LEYENDA_1': 'TextEdit', 'LEYENDA_2': 'TextEdit', 'LEYENDA_3': 'TextEdit', 'LEYENDA_4': 'TextEdit', 'VOLCAN': 'TextEdit', 'AMENAZA': 'TextEdit', 'AREA_KM2': 'TextEdit', 'RULEID': 'TextEdit', 'SHAPE.AREA': 'TextEdit', 'SHAPE.LEN': 'TextEdit', });
lyr_Veredas_1.set('fieldLabels', {'fid': 'no label', 'Name': 'no label', 'description': 'no label', 'timestamp': 'no label', 'begin': 'no label', 'end': 'no label', 'altitudeMode': 'no label', 'tessellate': 'no label', 'extrude': 'no label', 'visibility': 'no label', 'drawOrder': 'no label', 'icon': 'no label', 'OBJECTID': 'no label', 'DPTOMPIO': 'no label', 'CODIGO_VER': 'no label', 'NOM_DEP': 'no label', 'NOMB_MPIO': 'no label', 'NOMBRE_VER': 'no label', 'VIGENCIA': 'no label', 'FUENTE': 'no label', 'DESCRIPCIO': 'no label', 'SEUDONIMOS': 'no label', 'AREA_HA': 'no label', 'COD_DPTO': 'no label', 'OBSERVACIO': 'no label', 'CONSEJE': 'no label', 'ORIG_FID': 'no label', 'SHAPE_Leng': 'no label', 'SHAPE_Area': 'no label', 'layer': 'no label', 'path': 'no label', });
lyr_Municipios_2.set('fieldLabels', {'dpto_ccdgo': 'no label', 'mpio_ccdgo': 'no label', 'mpio_cdpmp': 'no label', 'dpto_cnmbr': 'no label', 'mpio_cnmbr': 'no label', 'mpio_crslc': 'no label', 'mpio_tipo': 'no label', 'mpio_narea': 'no label', 'mpio_nano': 'no label', 'shape_Leng': 'no label', 'shape_Area': 'no label', });
lyr_Departamentos_3.set('fieldLabels', {'dpto_ccdgo': 'no label', 'dpto_cnmbr': 'no label', 'dpto_ano_c': 'no label', 'dpto_act_a': 'no label', 'dpto_narea': 'no label', 'dpto_nano': 'no label', 'shape_Leng': 'no label', 'shape_Area': 'no label', });
lyr_Zonaurbana_4.set('fieldLabels', {'dpto_ccdgo': 'no label', 'mpio_ccdgo': 'no label', 'mpio_cdpmp': 'no label', 'clas_ccdgo': 'no label', 'setr_ccdgo': 'no label', 'setr_ccnct': 'no label', 'secr_ccdgo': 'no label', 'secr_ccnct': 'no label', 'zu_ccdgo': 'no label', 'zu_cdivi': 'no label', 'zu_cnmbre': 'no label', 'zu_ccnct': 'no label', 'zu_narea': 'no label', 'zu_naltd': 'no label', 'zu_nano': 'no label', 'shape_Leng': 'no label', 'shape_Area': 'no label', });
lyr_VasDANEMGN_5.set('fieldLabels', {'OBJECTID': 'no label', 'FID_MGN_AD': 'no label', 'DPTO_CCDGO': 'no label', 'DPTO_NANO_': 'no label', 'DPTO_CNMBR': 'no label', 'DPTO_CACTO': 'no label', 'DPTO_NAREA': 'no label', 'DPTO_CSMBL': 'no label', 'DPTO_NANO': 'no label', 'PAIS_PAIS_': 'no label', 'SHAPE_Leng': 'no label', 'FID_roads': 'no label', 'osm_id': 'no label', 'name': 'no label', 'ref': 'no label', 'type': 'no label', 'oneway': 'no label', 'bridge': 'no label', 'tunnel': 'no label', 'maxspeed': 'no label', 'SHAPE_Le_1': 'no label', });
lyr_SGCVolcnPurac_6.set('fieldLabels', {'OBJECTID': 'no label', 'ID': 'no label', 'VOLCAN': 'no label', 'ESTE': 'no label', 'NORTE': 'no label', 'LONGITUD': 'no label', 'LATITUD': 'no label', 'ALTITUD': 'no label', 'WEB_OVSP': 'no label', 'RULEID': 'no label', 'CONOACTACTIVO': 'no label', });
lyr_SGCPiroclastos_7.set('fieldLabels', {'OBJECTID': 'no label', 'ID': 'no label', 'FENOMENOS': 'no label', 'LEYENDA_1': 'no label', 'LEYENDA_2': 'no label', 'VOLCAN': 'no label', 'AMENAZA': 'no label', 'AREA_KM2': 'no label', 'RADIO_KM': 'no label', 'RULEID': 'no label', 'SHAPE.LEN': 'no label', });
lyr_SGCAmenaza_8.set('fieldLabels', {'OBJECTID': 'no label', 'ID': 'no label', 'FENOMENOS': 'no label', 'LEYENDA_1': 'no label', 'LEYENDA_2': 'no label', 'LEYENDA_3': 'no label', 'LEYENDA_4': 'no label', 'VOLCAN': 'no label', 'AMENAZA': 'no label', 'AREA_KM2': 'no label', 'RULEID': 'no label', 'SHAPE.AREA': 'no label', 'SHAPE.LEN': 'no label', });
lyr_SGCAmenaza_8.on('precompose', function(evt) {
    evt.context.globalCompositeOperation = 'normal';
});