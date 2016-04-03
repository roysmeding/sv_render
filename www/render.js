"use strict";

const VIEWPORT_WIDTH  = 960,
      VIEWPORT_HEIGHT = 480;

const TILE_WIDTH  = 16,
      TILE_HEIGHT = 16;

const ZOOM_FACTOR = 1.05;

var renderer = null;

var viewport = {
		'tx': 0,
		'ty': 0,
		'zoom': 1,
	};

function xhr(url, callback) {
	var oReq = new XMLHttpRequest();
	oReq.addEventListener("load", callback);
	oReq.open("GET", url);
	oReq.send();
}

function tilesheetsLoaded() {
	console.log("All tilesheets loaded!");
	request_redraw();
}

function checkLoaded() {
	if(!renderer.can_be_loaded || renderer.has_loaded)
		return;

	for(let key in renderer.tilesheets) {
		if(!renderer.tilesheets.hasOwnProperty(key))
			continue;
		let ts = renderer.tilesheets[key];
		if(!ts.loaded)
			return;
	}

	tilesheetsLoaded();
	renderer.has_loaded = true;
}

function drawTile(ctx, tile, col, row) {
	let ts = renderer.tilesheets[tile.ts];

	let sx, sy, w, h;
	let offsetX = 0, offsetY = 0;

	if(ts.sprites) {
		let sprite = ts.sprites[tile.idx];
		sx = sprite[0];
		sy = sprite[1];
		w  = sprite[2];
		h  = sprite[3];
	} else {
		let scol =            tile.idx % ts.sheet_size[0],
		    srow = Math.floor(tile.idx / ts.sheet_size[0]);

	    if ("tileSize" in tile) {
	    	w = tile.tileSize[0];
	    	h = tile.tileSize[1];
	    } else {
			w  = ts.tile_size[0];
			h  = ts.tile_size[1];
	    }

	    if ("offset" in tile) {
	    	offsetX = tile.offset[0];
	    	offsetY = tile.offset[1];
	    }

		sx = scol*ts.tile_size[0];
		sy = srow*ts.tile_size[1];
	}

	let dx = col*TILE_WIDTH,
	    dy = row*TILE_HEIGHT - (h -   TILE_HEIGHT);

	ctx.drawImage(ts.img, sx, sy, w, h, dx + offsetX, dy + offsetY, w, h);
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
	layer.dirty = false;
}

function drawLayer(ctx, layer) {
	if(!layer.vis) return;
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
	if(renderer.objs_dirty) {
		renderer.map.objects.sort(function(a,b) { return a.pos[1]-b.pos[1]; });

		renderer.obj_ctx.clearRect(0,0,renderer.obj_canvas.width,renderer.obj_canvas.height);
		for(let o of objs) {
			drawTile(renderer.obj_ctx, o, o.pos[0], o.pos[1]);
		}
		renderer.objs_dirty = false;
	}

	let sx = 0,
	    sy = 0;

	let sw = renderer.obj_canvas.width,
	    sh = renderer.obj_canvas.height;

	let dx = viewport.tx,
	    dy = viewport.ty;

	let dw = renderer.obj_canvas.width  * viewport.zoom,
	    dh = renderer.obj_canvas.height * viewport.zoom;

	ctx.drawImage(renderer.obj_canvas, sx, sy, sw, sh, dx, dy, dw, dh);
}

function drawMap(ctx, map) {
	ctx.clearRect(0,0,renderer.canvas.width,renderer.canvas.height);

	for(let layer of renderer.map.layers)
		if(layer.depth <= 0)
			drawLayer(ctx, layer);

	drawObjects(ctx, renderer.map.objects);

	for(let layer of renderer.map.layers)
		if(layer.depth > 0)
			drawLayer(ctx, layer);
}

var redraw_pending = false;

function redraw() {
	let ctx = renderer.canvas.getContext("2d");
	drawMap(ctx, renderer);
	redraw_pending = false;
}


function request_redraw() {
	if(!redraw_pending) {
		redraw_pending = true;
		window.requestAnimationFrame(redraw);
	}
}

function tilesheetMetaLoaded(ts) {
	return function() {
		if(!(this.status >= 200 && this.status < 300))
			return;
		let r_ts = JSON.parse(this.responseText);

		if(r_ts.sprites) {
			ts.sprites    = r_ts.sprites;
		} else {
			ts.tile_size  = r_ts.tile_size;
			ts.sheet_size = r_ts.sheet_size;
		}

		ts.img = new Image();
		ts.img.addEventListener('load', function() { tilesheetImgLoaded(ts); });
		ts.img.src = "assets/"+r_ts.img_src;
	}
}

function tilesheetImgLoaded(ts) {
	ts.loaded = true;
	checkLoaded();
}

function loadTilesheet(src) {
	if(renderer.tilesheets.hasOwnProperty(src)) {
		console.log("Already loaded tilesheet '"+src+"'");
		return;
	}

	let ts = new Object();
	ts.src = src;
	ts.loaded = false;

	renderer.tilesheets[ts.src] = ts;

	let json_name = 'tilesheets/'+src+'.json';
	xhr(json_name, tilesheetMetaLoaded(ts));
}

function mapsLoaded() {
	let r_maps = JSON.parse(this.responseText);

	let r_map = r_maps[renderer.el.dataset.loc];

	renderer.map = new Object();
	renderer.can_be_loaded = false;
	renderer.has_loaded = false;

	for(let ts of r_map.tilesheets)
		loadTilesheet(ts);

	renderer.map.properties = r_map.properties;
	renderer.map.layers = new Array();

	let max_layerwidth  = 0,
	    max_layerheight = 0;

	for(let r_layer of r_map.layers) {
		let layer = new Object();
		layer.size      = r_layer.size;
		layer.tile_size = r_layer.tile_size;
		layer.vis       = (r_layer.vis === undefined) ? true : r_layer.vis;
		layer.depth     = r_layer.depth;

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
						prev_tile = { 'idx': item, 'ts': r_map.tilesheets[ts] };
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

		renderer.map.layers.push(layer);
	}

	renderer.obj_canvas = document.createElement('canvas');

	renderer.obj_canvas.width  = max_layerwidth;
	renderer.obj_canvas.height = max_layerheight;

	renderer.obj_ctx = renderer.obj_canvas.getContext('2d');
	renderer.objs_dirty = true;

	renderer.can_be_loaded = true;
	checkLoaded();
}

function saveLoaded() {
	let r_save = JSON.parse(this.responseText);
	console.log(r_save);

	for(let ts of r_save.tilesheets) {
		loadTilesheet(ts);
	}

	let r_loc = undefined;
	for(let loc of r_save.locations) {
		if(loc.name == renderer.el.dataset.loc)
			r_loc = loc;
	}

	renderer.map.objects = [];
	for(let item of r_loc.items) {
		let obj = new Object();
		obj.ts  = r_save.tilesheets[item.ts];
		obj.idx = item.idx;
		obj.pos = item.pos;

		renderer.map.objects.push(obj);
	}

	for(let building of r_loc.buildings) {
		let obj = new Object();
		obj.ts  = r_save.tilesheets[building.ts];
		obj.idx = building.idx;
		obj.pos = [
				building.pos[0],
				building.pos[1] + building.size[1] - 1
			];

		renderer.map.objects.push(obj);
	}

	for(let feature of r_loc.features) {
		if(feature === null)
			continue;

		let obj = new Object();
		obj.ts  = r_save.tilesheets[feature.ts];
		obj.idx = feature.idx;
		obj.pos = feature.pos;
		if ("tileSize" in feature) {
			obj.tileSize = feature.tileSize;
		}
		if ("offset" in feature) {
			obj.offset = feature.offset;
		}

		renderer.map.objects.push(obj);
	}

	renderer.objs_dirty = true;
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

	request_redraw();
	e.preventDefault();
}

function wheel(e) {
	let zoom_amount = Math.pow(ZOOM_FACTOR, -e.deltaY/100.);
	viewport.zoom *= zoom_amount;

	let b = renderer.canvas.getBoundingClientRect();

	// position of mouse relative to (0,0) in layer coords
	let relx = e.clientX - b.left - viewport.tx,
	    rely = e.clientY - b.top  - viewport.ty;

	viewport.tx -= (zoom_amount-1) * relx;
	viewport.ty -= (zoom_amount-1) * rely;

	request_redraw();
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
	renderer = new Object();
	renderer.el = document.getElementById("renderer");

	renderer.canvas = document.createElement("canvas");
	renderer.canvas.width  = VIEWPORT_WIDTH;
	renderer.canvas.height = VIEWPORT_HEIGHT;

	renderer.canvas.addEventListener("mousedown", mouseDown, true);
	renderer.canvas.addEventListener("wheel", wheel, true);

	renderer.el.appendChild(renderer.canvas);

	renderer.tilesheets = {};

	xhr(renderer.el.dataset.maps, mapsLoaded);
	xhr(renderer.el.dataset.save, saveLoaded);
}

window.addEventListener("load", load_renderer);
