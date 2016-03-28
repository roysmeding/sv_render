import sys
import os
import xml.etree.ElementTree as ET
import json

import xnb
import xnb.graphics
import xnb.xtile

def dump_size(s):
    return [s.width, s.height]

def dump_properties(p):
    return p

def dump_tilesheet(ts, m):
    output = {
            'src': ts.image_source,
            'sheet_size':   dump_size(ts.sheet_size),
            'tile_size':    dump_size(ts.tile_size),
        }

    if ts.margin.width != 0 or ts.margin.height != 0:
        output['margin'] = dump_size(ts.margin)

    if ts.spacing.width != 0 or ts.spacing.height != 0:
        output['spacing'] = dump_size(ts.spacing)

    if len(ts.properties) > 0:
        output['properties'] = dump_properties(ts.properties)

    return output

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
        if l.visible:
            output['layers'].append(dump_layer(l, m))

    if len(m.properties) > 0:
        output['properties'] = dump_properties(m.properties)

    return output

if len(sys.argv) != 4:
    print("Usage: {} <save_file> <location> <output_file>".format(sys.argv[0]))
    sys.exit(1)

_, save_filename, location, output_filename = sys.argv

# load map
MAPS_DIR = '../xnb/Maps'

map_filename = os.path.join(MAPS_DIR, location) + '.xnb'
map_file = xnb.XNBFile(map_filename)

assert isinstance(map_file.primaryObject, xnb.xtile.Map), "File does not contain XTile map object"

# dump map to output data structure
output_data = dump_map(map_file.primaryObject)

# dump save
tree = ET.parse(sys.argv[1])
root = tree.getroot()

loc = root.find("./locations/GameLocation[name='{:s}']".format(location))

# for character in loc.findall('./characters/NPC'):
#     pos = character.find('Position')
#     x,y = int(pos.find('X').text), int(pos.find('Y').text)
# 
#     print("\tNPC      @ ({:5d}px, {:5d}px): {}".format(x, y, character.find('name').text))

output_data['items'] = []

for item_entry in loc.findall('./objects/item'):
    pos, item = item_entry.find('key')[0], item_entry.find('value')[0]

    col,row = int(pos.find('X').text), int(pos.find('Y').text)

    psi = int(item.find('parentSheetIndex').text)

    output_data['items'].append({ 'pos': [col,row], 'idx': psi })



# for building in loc.findall('./buildings/Building'):
#     x, y = int(building.find('tileX').text), int(building.find('tileY').text)
#     print("\tBuilding @ ({:3d}t, {:3d}t): {}".format(x, y, building.find('buildingType').text))
# 
#     indoors = building.find('indoors')
# 
#     if not indoors:
#         continue
# 
#     for character in indoors.findall('./characters/NPC'):
#         pos = character.find('Position')
#         x,y = int(pos.find('X').text), int(pos.find('Y').text)
# 
#         print("\t\tNPC      @ ({:5d}px, {:5d}px): {}".format(x, y, character.find('name').text))
# 
#     for item_entry in indoors.findall('./objects/item'):
#         pos, item = item_entry.find('key')[0], item_entry.find('value')[0]
# 
#         x,y = int(pos.find('X').text), int(pos.find('Y').text)
#         print("\t\tObject   @ ({:3d}t, {:3d}t): {}".format(x, y, item.find('name').text))
# 
#     for animal_entry in indoors.findall('./animals/item'):
#         ID, animal = animal_entry.find('key')[0], animal_entry.find('value')[0]
# 
#         pos = animal.find('Position')
# 
#         x,y = int(pos.find('X').text), int(pos.find('Y').text)
#         print("\t\tAnimal   @ ({:5d}px, {:5d}px): {}".format(x, y, animal.find('name').text))

with open(output_filename, 'w') as outfile:
    json.dump(output_data, outfile, separators=(',',':'))
