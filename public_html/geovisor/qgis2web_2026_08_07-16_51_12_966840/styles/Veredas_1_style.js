var size = 0;
var placement = 'point';

var style_Veredas_1 = function(feature, resolution){
    var context = {
        feature: feature,
        variables: {}
    };
    
    var labelText = ""; 
    var value = feature.get("");
    var labelFont = "13.0px \'Open Sans\', sans-serif";
    var labelFill = "#ff0000";
    var bufferColor = "";
    var bufferWidth = 0;
    var textAlign = 'left';
    var offsetX = 8;
    var offsetY = 3;
    var overflow = false;
    var repeat = 0;
    var placement = 'point';
    if (exp_label_Veredas_1_eval_expression(context) !== null) {
        labelText = String(exp_label_Veredas_1_eval_expression(context));
    }
    var style = [ new ol.style.Style({
        stroke: new ol.style.Stroke({color: 'rgba(247,11,11,1.0)', lineDash: [8.55,1.71,3.42,1.71,3.42,1.71], lineCap: 'butt', lineJoin: 'miter', width: 1.71}),fill: new ol.style.Fill({color: 'rgba(0,0,0,0.0)'}),
        text: createTextStyle(feature, resolution, labelText, labelFont,
                              labelFill, placement, bufferColor,
                              bufferWidth, textAlign, offsetX, offsetY, overflow, repeat)
    })];

    return style;
};
