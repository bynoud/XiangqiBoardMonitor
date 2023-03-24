

// input params
var {originalWidth, movetime, multipv} = arguments[0];


// JS_VAR_START

var BOARD_HEIGH = 10;
var BOARD_WIDHT = 9;

var ID_ORG = 'xhOriginalContent';
var ID_SIDE = 'xhSideContent';
var ID_MAIN = 'xhMainDiv';
var ID_CANVAS = 'xhSideCanvas';

var ID_CONTROL = 'xhControl';
var ID_CONTROL_MOVETIME = 'xhCtrlMovetime';
var ID_CONTROL_MULTIPV = 'xhCtrlMultipv';
var ID_CONTROL_MYMOVE = 'xhCtrlMymove';
var ID_CONTROL_LOGTEXT = 'xhCtrlLogtext';
var ID_CONTROL_POPUPTEXT = 'xgPopupText';

var gridSize = 40;
var padding = 30;
var gridLineWidth = 2;
var gridLineColor = 'black';

//////
var gridHalf = Math.floor(gridSize / 2);
var boardW = gridSize*(BOARD_WIDHT-1);
var boardH = gridSize*(BOARD_HEIGH-1);
var canvasW = padding*2 + boardW;
var canvasH = padding*2 + boardH;

// JS_VAR_END

/**
 * 
 * @param {HTMLElement} parent 
 * @param {string} eleType 
 * @param {string} id 
 * @returns {HTMLElement}
 */
function addElement(parent, eleType, id=null, style={}, attr={}) {
    var ele = document.createElement(eleType);
    if (id != null) ele.id = id;
    Object.entries(style).forEach(([k,v]) => ele.style[k] = v);
    Object.entries(attr).forEach(([k,v]) => ele.setAttribute(k, v));
    if (parent != null) parent.appendChild(ele);
    return ele
}

// re-organize the web structure
var orgDiv = addElement(null, 'div', ID_ORG,
                        {display: 'inline-block', width: `${originalWidth}px`, verticalAlign: 'top'});
orgDiv.append(...document.body.childNodes);

var mainDiv = addElement(document.body, 'div', ID_MAIN);
mainDiv.appendChild(orgDiv);

var sideDiv = addElement(mainDiv, 'div', ID_SIDE,
                        {display: 'inline-block', background: '#e3f6f5'});
                         //width:`${canvasW+10}px`,
                        // verticalAlign: 'top', background: '#e3f6f5'});

// add canvas
var side1Div = addElement(sideDiv, 'div', null,
                        {display: 'inline-block', width:`${canvasW+10}px`, verticalAlign: 'top'})

var canvasDiv = addElement(side1Div, 'div', null,
                            {height: `${canvasH+10}px`, width: `${canvasW+10}px`});

var canvas = addElement(canvasDiv, 'canvas', ID_CANVAS,
                        {zIndex: 8, position: "absolute", border: "1px solid"},
                        {width: canvasW, height: canvasH});

// popup text
var popupDiv = addElement(canvasDiv, 'div', null,
                        {position: 'absolute', width: `${canvasW+10}px`, height: `${canvasH+10}px`})
var popupText = addElement(popupDiv, 'p', ID_CONTROL_POPUPTEXT,
                        {textAlign: 'center', verticalAlign: 'middle', lineHeight: `${canvasH+10}px`,
                        fontSize: `${gridSize}px`, fontFamily: 'sans-serif', fontWeight: 'bold', color: 'red'})

// addElement(document, 'script', null, {}, {src: 'board_drawing.js'})
// var canvasScript = document.createElement('script')
// canvasScript.textContent = `${draw_board.toString().replace('\n',' ')} draw_board();`
// document.body.appendChild(canvasScript);
// draw_board()

/// control
var controlDiv = addElement(side1Div, 'div', ID_CONTROL, {padding: '10px'})

addElement(controlDiv, 'label', null, {paddingInline: '10px'}).innerHTML = 'Movetime';
addElement(controlDiv, 'input', ID_CONTROL_MOVETIME,
            {width: '50px'},
            {type: 'number', onkeydown:"return false", value:movetime, min:1, max:15});

addElement(controlDiv, 'label', null, {paddingInline: '10px'}).innerHTML = 'Multipv';
addElement(controlDiv, 'input', ID_CONTROL_MULTIPV,
            {width: '50px'}, 
            {type: 'number', onkeydown:"return false", value:multipv, min:1, max:20});

addElement(controlDiv, 'label', null, {paddingInline: '10px'}).innerHTML = 'MyMove';
addElement(controlDiv, 'input', ID_CONTROL_MYMOVE,
            {}, {type: 'checkbox', });

// log
var logDiv = addElement(sideDiv, 'div', null,
                        {display: 'inline-block', width: '300px'});
addElement(logDiv, 'textarea', ID_CONTROL_LOGTEXT,
            {width: '100%', marginTop: '10px'}, {disabled:'true', rows: 20});


// ctx.beginPath();
// ctx.arc(100, 100, 30, 0, 2 * Math.PI, false);
// ctx.fillStyle = 'green';
// ctx.fill();
// ctx.lineWidth = 3;
// ctx.strokeStyle = '#003300';
// ctx.stroke();
            