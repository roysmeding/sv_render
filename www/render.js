"use strict";

const VIEWPORT_WIDTH  = 960,
      VIEWPORT_HEIGHT = 480;

const ZOOM_FACTOR = 1.05;

var renderer = null;
var canvas   = null;
var map      = null;

var viewport = {
		'tx': 0,
		'ty': 0,
		'zoom': 1,
	};

function resolveTSSrc(src) {
	return 'tilesheets/'+src+'.png';
}

function tilesheetsLoaded() {
	console.log("All tilesheets loaded!");
	redraw();
}

function checkLoaded() {
	if(!map.can_be_loaded || map.has_loaded)
		return;
	for(let tilesheet of map.tilesheets) {
		if(!tilesheet.loaded)
			return;
	}

	tilesheetsLoaded();
	map.has_loaded = true;
}

function drawTile(ctx, tile, col, row) {
	let scol =            tile.idx % tile.ts.sheet_size[0],
	    srow = Math.floor(tile.idx / tile.ts.sheet_size[0]);

	let sw   = tile.ts.tile_size[0],
	    sh   = tile.ts.tile_size[1];

	let sx   = scol*sw,
	    sy   = srow*sh;

	let dx   = col*sw,
	    dy   = row*sh;

	ctx.drawImage(tile.ts.img, sx, sy, sw, sh, dx, dy, sw, sh);
}

function redrawLayer(layer) {
	layer.tiles.forEach(function(line, row) {
		line.forEach(function(tile, col) {
			if(tile === null)
				return;
			else
				drawTile(layer.ctx, tile, col, row);
		});
	});
}

function drawLayer(ctx, layer) {
	if(!layer.visible) return;
	if(layer.dirty) redrawLayer(layer);

	let sx = 0,
	    sy = 0;

	let sw = layer.canvas.width,
	    sh = layer.canvas.height;

	let dx = viewport.tx,
	    dy = viewport.ty;

	let dw = layer.canvas.width  * viewport.zoom,
	    dh = layer.canvas.height * viewport.zoom;

	ctx.drawImage(layer.canvas, sx, sy, sw, sh, dx, dy, dw, dh);
}

function drawObjects(ctx, objs) {
	map.obj_ctx.clearRect(0,0,map.obj_canvas.width,map.obj_canvas.height);
	for(let o of objs) {
		drawTile(map.obj_ctx, o, o.pos[0], o.pos[1]);
	}

	let sx = 0,
	    sy = 0;

	let sw = map.obj_canvas.width,
	    sh = map.obj_canvas.height;

	let dx = viewport.tx,
	    dy = viewport.ty;

	let dw = map.obj_canvas.width  * viewport.zoom,
	    dh = map.obj_canvas.height * viewport.zoom;

	ctx.drawImage(map.obj_canvas, sx, sy, sw, sh, dx, dy, dw, dh);
}

function drawMap(ctx, map) {
	ctx.clearRect(0,0,canvas.width,canvas.height);
	for(let layer of map.layers) {
		drawLayer(ctx, layer);
	}
	drawObjects(ctx, map.objects);
}

function redraw() {
	let ctx = canvas.getContext("2d");
	drawMap(ctx, map);
}

function loadTilesheet(ts) {
	ts.loaded = true;

	checkLoaded();
}

function loadMap() {
	let r_map = JSON.parse(this.responseText);

	map = new Object();
	map.can_be_loaded = false;
	map.has_loaded = false;

	map.tilesheets = r_map.tilesheets;
	for(let tilesheet of map.tilesheets) {
		console.log("Loading tilesheet '"+tilesheet.src+"'");

		tilesheet.loaded = false;
		tilesheet.img = new Image();
		tilesheet.img.addEventListener('load', function() { loadTilesheet(tilesheet); });
		tilesheet.img.src = resolveTSSrc(tilesheet.src);
	}


	let object_ts = new Object();
	object_ts.tile_size  = [16,16];
	object_ts.sheet_size = [24,33];
	object_ts.src = 'springobjects';
	object_ts.loaded = false;
	object_ts.img = new Image();
	object_ts.img.addEventListener('load', function() { loadTilesheet(object_ts); });
	object_ts.img.src = resolveTSSrc(object_ts.src);

	map.objects = r_map.objects;

	for(let obj of map.objects) {
		obj.ts = object_ts;
	}

	map.properties = r_map.properties;
	map.layers = new Array();

	let max_layerwidth  = 0,
	    max_layerheight = 0;

	for(let r_layer of r_map.layers) {
		let layer = new Object();
		layer.size      = r_layer.size;
		layer.tile_size = r_layer.tile_size;
		layer.visible   = true;

		layer.tiles = new Array(r_layer.size[1]);
		let row = 0;
		let ts  = undefined;
		for(let r_row of r_layer.tiles) {
			layer.tiles[row] = new Array();

			let col       = 0;
			let prev_tile = undefined;

			for(let item of r_row) {
				if(typeof item === 'number') {
					if(item == -1)
						prev_tile = null;
					else
						prev_tile = { 'idx': item, 'ts': map.tilesheets[ts] };
					layer.tiles[row][col++] = prev_tile;
				} else if(item.rep !== undefined) {
					for(let i = 0; i < (item.rep); i++) {
						layer.tiles[row][col++] = prev_tile;
					}
				} else if(item.ts  !== undefined) {
					ts = item.ts;
				}
			}
			row += 1;
		}

		layer.dirty = true;

		layer.canvas = document.createElement('canvas');

		layer.canvas.width  = layer.size[0] * layer.tile_size[0];
		layer.canvas.height = layer.size[1] * layer.tile_size[1];

		if(layer.canvas.width  >= max_layerwidth)  max_layerwidth  = layer.canvas.width;
		if(layer.canvas.height >= max_layerheight) max_layerheight = layer.canvas.height;

		layer.ctx = layer.canvas.getContext('2d');

		map.layers.push(layer);
	}


	map.obj_canvas = document.createElement('canvas');
	map.obj_canvas.width  = max_layerwidth;
	map.obj_canvas.height = max_layerheight;
	map.obj_ctx = map.obj_canvas.getContext('2d')

	map.can_be_loaded = true;
	checkLoaded();
}

function mouseMove(e) {
	var dx = e.movementX    ||
		 e.mozMovementX ||
		 0;

	var dy = e.movementY    ||
		 e.mozMovementY ||
		 0;

	viewport.tx += dx;
	viewport.ty += dy;

	window.requestAnimationFrame(redraw);
	e.preventDefault();
}

function wheel(e) {
	let zoom_amount = Math.pow(ZOOM_FACTOR, -e.deltaY/100.);
	viewport.zoom *= zoom_amount;

	let b = canvas.getBoundingClientRect();

	// position of mouse relative to (0,0) in layer coords
	let relx = e.clientX - b.left - viewport.tx,
	    rely = e.clientY - b.top  - viewport.ty;

	viewport.tx -= (zoom_amount-1) * relx;
	viewport.ty -= (zoom_amount-1) * rely;

	window.requestAnimationFrame(redraw);
	e.preventDefault();
}

function mouseDown(e) {
	window.addEventListener('mousemove', mouseMove, true);
	window.addEventListener("mouseup",   mouseUp,   true);
	e.preventDefault();
}

function mouseUp(e) {
	window.removeEventListener('mousemove', mouseMove, true);
	e.preventDefault();
}

function load_renderer() {
	renderer = document.getElementById("renderer");

	canvas = document.createElement("canvas");
	canvas.width  = VIEWPORT_WIDTH;
	canvas.height = VIEWPORT_HEIGHT;

	canvas.addEventListener("mousedown", mouseDown, true);
	canvas.addEventListener("wheel", wheel, true);

	renderer.appendChild(canvas);

	var oReq = new XMLHttpRequest();
	oReq.addEventListener("load", loadMap);
	oReq.open("GET", renderer.dataset.map);
	oReq.send();
}

window.addEventListener("load", load_renderer);
