import sys
import os
import json

import xnb
import maps
import saves

if len(sys.argv) < 3:
    print("Usage: {} <output_file> [maps...]".format(sys.argv[0]))
    sys.exit(1)

_, output_filename = sys.argv[:2]

print("Loading maps...")

output = {}

for location in sys.argv[2:]:
    print('\t{:s}'.format(location))

    # load map
    map_filename = location + '.xnb'
    map_file = xnb.XNBFile(map_filename)

    assert isinstance(map_file.primaryObject, xnb.xtile.Map), "File does not contain XTile map object"

    # dump map
    output[location] = maps.dump_map(map_file.primaryObject)

# write map
print("Writing JSON...")

with open(output_filename, 'w') as f:
    json.dump(output, f, separators=(',',':'))
