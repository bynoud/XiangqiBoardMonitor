

function draw_board() {

    let canvas = document.getElementById(ID_CANVAS);
    if (canvas == null) return null; // not ready for message yet
    let ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvasW, canvasH);

    ctx.strokeStyle = '#49beb7';
    ctx.lineWidth = 1;

    // horizontal
    for (let row=0; row<BOARD_HEIGH; row++) {
        let sy = padding + row*gridSize;
        let sx = padding;
        ctx.beginPath();
        ctx.moveTo(sx,sy);
        ctx.lineTo(sx+boardW,sy);
        ctx.stroke();
    }
    // vertical
    boardHalf1 = gridSize * 4;
    boardHalf2 = gridSize * 5;
    for (let col=0; col<BOARD_WIDHT; col++) {
        let sy = padding;
        let sx = padding + col*gridSize;
        if (col==0 || col==BOARD_WIDHT-1) {
            ctx.beginPath();
            ctx.moveTo(sx,sy);
            ctx.lineTo(sx,sy+boardH);
            ctx.stroke();
        } else {
            ctx.beginPath();
            ctx.moveTo(sx,sy);
            ctx.lineTo(sx,sy+boardHalf1);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(sx,sy+boardHalf2);
            ctx.lineTo(sx,sy+boardH);
            ctx.stroke();
        }
    }

    // palace
    [[3,0],[3,7]].forEach(c => {
        sx = padding + c[0]*gridSize
        sy = padding + c[1]*gridSize
        grid2 = gridSize*2;
        ctx.beginPath();
        ctx.moveTo(sx,sy);
        ctx.lineTo(sx+grid2, sy+grid2);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(sx,sy+grid2);
        ctx.lineTo(sx+grid2, sy);
        ctx.stroke();
    })

    // cross
    crossHalf = Math.floor(gridHalf*0.3);
    crossSize = crossHalf*2;
    [[1,2], [7,2],
        [0,3], [2,3], [4,3], [6,3], [8,3],
        [1,7], [7,7],
        [0,6], [2,6], [4,6], [6,6], [8,6]].forEach(c => {
        sx = padding + c[0]*gridSize - crossHalf
        sy = padding + c[1]*gridSize - crossHalf
        ctx.beginPath();
        ctx.moveTo(sx,sy);
        ctx.lineTo(sx+crossSize, sy+crossSize);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(sx,sy+crossSize);
        ctx.lineTo(sx+crossSize, sy);
        ctx.stroke();
    })

    return ctx;
}

//
function show_popup({message}) {
    let ctx = draw_board();
    if (ctx==null) return;
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'center';
    ctx.fillStyle = '#ff5959';
    ctx.font = `bold ${gridSize}px serif`;
    ctx.fillText(message, canvasW/2, canvasH/2);
}

//////
function update_position({positions, lastmove, movelist}) {
    let ctx = draw_board();
    if (ctx==null) {
        console.error('Canvas not found');
        return
    }
    draw_position(ctx, positions);
    draw_lastmove(ctx, lastmove);
    draw_movelist(ctx, movelist);
}


function draw_position(ctx, positions) {
    let rad = Math.floor(gridSize*0.4);
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'center';
    ctx.font = `bold ${gridSize/2}px serif`;
    for (let x=0; x<BOARD_WIDHT; x++) {
        for (let y=0; y<BOARD_HEIGH; y++) {
            let p = positions[y][x];
            if (p=='.') continue;
            draw_piece(ctx, rad, p, x, y);
        }
    }
}

function draw_piece(ctx, rad, sym, x, y) {
    let black = sym == sym.toLowerCase()
    let cx = padding+x*gridSize;
    let cy = padding+y*gridSize;

    ctx.beginPath();
    ctx.arc(cx, cy, rad, 0, 2*Math.PI, false);
    ctx.fillStyle = black ? '#085f63' : '#ff5959' ;
    ctx.fill();
    ctx.lineWidth = 3;
    ctx.strokeStyle = '#0e2431';
    ctx.stroke();

    // label
    ctx.fillStyle = '#eaeaea';
    ctx.fillText(sym, cx, cy);

}

function draw_lastmove(ctx, lastmove) {
    if (lastmove.length < 2) return;
    let cx = padding + lastmove[0]*gridSize;
    let cy = padding + lastmove[1]*gridSize;
    let ofs = Math.floor(gridSize*0.5);
    let w = Math.ceil(gridSize*0.2);
    ctx.strokeStyle = '#facf5a';
    ctx.lineWidth = 4;
    [[-1,-1],[-1,1],[1,-1],[1,1]].forEach(pos => {
        let sx = cx + ofs*pos[0];
        let sy = cy + ofs*pos[1];
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(sx - pos[0]*w, sy);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(sx, sy - pos[1]*w);
        ctx.stroke();
    })
}

var MOVE_COLOR = [
    '#0b4386ff', '#5c000bff',
    '#126ddba0', '#b91b23a0',
    '#1995e580', '#d15a4480',
    '#22c8f180', '#eba67580',
    '#2bfffe80', '#fae6d880'];
function draw_movelist(ctx, movelist) {
    // let ctx = draw_board();
    // update_position({positions, lastmove});
    // movelist.forEach((move, index) => {
    for (let index = 0; index < movelist.length; index++) {
        move = movelist[index];
        // console.error(index, move);
        draw_arrow(ctx, 
            padding+move[0][0]*gridSize, padding+move[0][1]*gridSize,
            padding+move[1][0]*gridSize, padding+move[1][1]*gridSize,
            4, MOVE_COLOR[index]);
    }
    // obj = []
    // for index, (start, end) in enumerate(movelist):
    //     if index > len(MOVE_COLOR):
    //         return
    //     obj.append(self.draw_move(start, end, MOVE_COLOR[index]))
    // # loop in revered, the first index has highest raise
    // while len(obj)>0:
    //     o = obj.pop()
    //     self.playCanvas.tag_raise(o)
}

function draw_arrow(context, fromx, fromy, tox, toy, width, color){
	var x_center = tox;
	var y_center = toy;
	
	var angle;
	var x;
	var y;

    context.lineWidth = width;
    context.strokeStyle = color;
    context.fillStyle = color; // for the triangle fill
    context.lineJoin = 'butt';

	context.beginPath();
	
	angle = Math.atan2(toy-fromy,tox-fromx)
    
    // mnake the arrow at the center of the end
    let r = width+2;    // arrow width
    x_center -= r * Math.cos(angle);
    y_center -= r * Math.sin(angle);

    context.beginPath();
    context.moveTo(fromx, fromy);
    context.lineTo(x_center, y_center);
    context.stroke();

	x = r*Math.cos(angle) + x_center;
	y = r*Math.sin(angle) + y_center;

	context.moveTo(x, y);
	
	angle += 0.66*Math.PI
	x = r*Math.cos(angle) + x_center;
	y = r*Math.sin(angle) + y_center;
	
	context.lineTo(x, y);

	
	angle += 0.66*Math.PI
	x = r*Math.cos(angle) + x_center;
	y = r*Math.sin(angle) + y_center;
	
	context.lineTo(x, y);
	
	context.closePath();
	
	context.fill();
}