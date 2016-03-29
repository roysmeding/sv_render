import sys
import os
import json

import xnb
import maps
import saves

if len(sys.argv) != 3:
    print("Usage: {} <save_file> <output_file>".format(sys.argv[0]))
    sys.exit(1)

_, save_filename, output_filename = sys.argv

# load save
print("Loading save...")
save_file = saves.Save.load(save_filename)

# dump save
print("Dumping save...")
save_dump = saves.dump_save(save_file)

# write save
print("Writing JSON...")

with open(output_filename, 'w') as f:
    json.dump(save_dump, f, separators=(',',':'))
