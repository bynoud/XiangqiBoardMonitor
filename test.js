ctx = document.getElementById("xhSideCanvas").getContext("2d");

// ctx.beginPath();
// canvas_arrow(ctx, 10, 30, 200, 150);
// canvas_arrow(ctx, 100, 200, 400, 50);
// canvas_arrow(ctx, 200, 30, 10, 150);
// canvas_arrow(ctx, 400, 200, 100, 50);
// ctx.stroke();


// function canvas_arrow1(context, fromx, fromy, tox, toy) {
//   var headlen = 10; // length of head in pixels
//   var dx = tox - fromx;
//   var dy = toy - fromy;
//   var angle = Math.atan2(dy, dx);
//   context.moveTo(fromx, fromy);
//   context.lineTo(tox, toy);
//   context.lineTo(tox - headlen * Math.cos(angle - Math.PI / 6), toy - headlen * Math.sin(angle - Math.PI / 6));
//   context.moveTo(tox, toy);
//   context.lineTo(tox - headlen * Math.cos(angle + Math.PI / 6), toy - headlen * Math.sin(angle + Math.PI / 6));
// }

// ctx.lineWidth = 5;
// ctx.strokeStyle = 'steelblue';
// ctx.fillStyle = 'steelblue'; // for the triangle fill
// ctx.lineJoin = 'butt';

// ctx.beginPath();
// ctx.moveTo(50, 50);
// ctx.lineTo(150, 150);
// ctx.stroke();

canvas_arrow(ctx, 50, 50, 150, 150, 5, 'red');
// canvas_arrow(ctx, 150, 150, 50, 50, 7);

function canvas_arrow(context, fromx, fromy, tox, toy, width, color){
	var x_center = tox;
	var y_center = toy;
	
	var angle;
	var x;
	var y;

    ctx.lineWidth = width;
    ctx.strokeStyle = color;
    ctx.fillStyle = color; // for the triangle fill
    ctx.lineJoin = 'butt';

	context.beginPath();
	
	angle = Math.atan2(toy-fromy,tox-fromx)
    
    // mnake the arrow at the center of the end
    let r = width+2;    // arrow width
    x_center -= r * Math.cos(angle);
    y_center -= r * Math.sin(angle);

    ctx.beginPath();
    ctx.moveTo(fromx, fromy);
    ctx.lineTo(x_center, y_center);
    ctx.stroke();

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