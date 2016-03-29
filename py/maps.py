import xnb
import xnb.graphics
import xnb.xtile

def dump_size(s):
    return [s.width, s.height]

def dump_properties(p):
    return p

def dump_tilesheet(ts, m):
    return ts.image_source

def dump_tile(t, m):
    if t is None:
        return None

    if isinstance(t, xnb.xtile.StaticTile):
        output = {
                'ts': m.tilesheets.index(t.tilesheet),
                'idx': t.index
            }

        if len(t.properties) > 0:
            output['properties'] = dump_properties(t.properties)

        return output

    elif isinstance(t, xnb.xtile.AnimatedTile):
        return dump_tile(t.frames[0], m)

    else:
        raise ValueError("Unknown tile type")

def dump_tiles(t, m):
    rows = []
    prev_ts = None

    for row in t:
        cols = []

        for tile in row:
            tile_output = dump_tile(tile, m)

            if len(cols)>0 and tile_output == prev_tile:
                if isinstance(cols[-1], dict) and 'rep' in cols[-1]:
                    cols[-1]['rep'] += 1

                else:
                    cols.append({ 'rep': 1 })

            else:
                if tile_output is None:
                    cols.append(-1)

                else:
                    if tile_output['ts'] != prev_ts:
                        cols.append({'ts': tile_output['ts']})
                        prev_ts = tile_output['ts']

                    cols.append(tile_output['idx'])

                prev_tile = tile_output

        rows.append(cols)

    return rows

def dump_layer(l, m):
    output = {
            'size':        dump_size(l.size),
            'tile_size':   dump_size(l.tile_size),
            'tiles':       dump_tiles(l.tiles, m)
        }

    if not l.visible:
        output['vis'] = False

    if l.layer_id == 'AlwaysFront':
        output['depth'] =  1

    elif l.layer_id == 'Back':
        output['depth'] = -2

    else:
        output['depth'] = -1

    if len(l.properties) > 0:
        output['properties'] = dump_properties(l.properties)

    return output

def dump_map(m):
    output = {
            'tilesheets': [],
            'layers': []
        }

    for ts in m.tilesheets:
        output['tilesheets'].append(dump_tilesheet(ts, m))

    for l in m.layers:
        output['layers'].append(dump_layer(l, m))

    if len(m.properties) > 0:
        output['properties'] = dump_properties(m.properties)

    return output
