import xml.etree.ElementTree as ET

class Position(object):
    @staticmethod
    def fromElement(el):
        return Position(
                int(el.find('X').text),
                int(el.find('Y').text)
            )

    def __init__(self, x, y):
        self.x = x
        self.y = y

class Character(object):
    def __init__(self, el):
        self.type = el.get('{http://www.w3.org/2001/XMLSchema-instance}type')
        self.pos  = Position.fromElement(el.find('Position'))
        self.name = el.find('name').text

    def dump(self, save):
        output = {
                'name': self.name,
                'pos':  dump_position(self.pos)
            }

        # determine tilesheet and index
        if   self.type == 'Cat':
            ts = 'Animals/cat'
        elif self.type == 'Dog':
            ts = 'Animals/dog'
        elif self.type == 'Horse':
            ts = 'Animals/horse'
        else:
            ts = 'Characters/'+self.name
            
        output['ts']  = useTilesheet(ts, save)
        output['idx'] = 0

        return output

class Item(object):
    def __init__(self, el, connectables):
        self.name = el.find('Name').text
        self.type = el.get('{http://www.w3.org/2001/XMLSchema-instance}type')
        self.category     = int(el.find('category').text)
        self.bigCraftable = el.find('bigCraftable').text == 'true'
        self.pos          = Position.fromElement(el.find('tileLocation'))
        self.sheetIndex   = int(el.find('parentSheetIndex').text)

        if self.type == 'Fence':
            self.whichType = int(el.find('whichType').text)
            key = 'fence%d' % self.whichType
            try:
                position = (self.pos.x, self.pos.y)
                connectables[key].append(position)
            except:
                connectables[key] = [position]


        # print(self.name, self.bigCraftable)
    def dump(self, save, connections):
        output = {
                'name': self.name,
                'pos': dump_position(self.pos)
            }

        if   self.bigCraftable:
            output['ts']  = useTilesheet('TileSheets/Craftables', save)
            output['idx'] = self.sheetIndex

        elif self.type == 'Fence':
            output['ts']  = useTilesheet('LooseSprites/Fence{:d}'.format(self.whichType), save)
            output['idx'] = connections["fence%d" % self.whichType][tuple(dump_position(self.pos))]

        else:
            output['ts']  = useTilesheet('Maps/springobjects', save)
            output['idx'] = self.sheetIndex

        return output

class Building(object):
    def __init__(self, el):
        self.type = el.find('buildingType').text
        self.pos  = Position(
                int(el.find('tileX').text),
                int(el.find('tileY').text)
            )

        self.tilesWide = int(el.find('tilesWide').text)
        self.tilesHigh = int(el.find('tilesHigh').text)

    def dump(self, save):
        output = {
                'pos':  dump_position(self.pos),
                'size': [ self.tilesWide, self.tilesHigh ],
                'type': self.type
            }

        output['ts']  = useTilesheet('Buildings/'+self.type, save)
        output['idx'] = 0

        return output

class ResourceClump:
    def __init__(self, el):
        self.pos = Position(
                int(el.find('tile/X').text),
                int(el.find('tile/Y').text)
            )
        self.tilesWide = int(el.find('width').text)
        self.tilesHigh = int(el.find('height').text)
        self.idx = int(el.find('parentSheetIndex').text)

    def dump(self, save):
        output = {
            'pos': dump_position(self.pos),
            'name': 'resourceclump'
        }
        output['ts'] = useTilesheet('Maps/springobjects', save)
        output['idx'] = self.idx
        output['tileSize'] = [16 * self.tilesWide, 16 * self.tilesHigh]
        return output

names = set()
grassseasons = {
    "spring": 0,
    "summer": 1,
    "fall": 2,
    "winter": 3
}
class Feature(object):
    def __init__(self, el, connectables):
        self.pos = Position.fromElement(el.find('key/Vector2'))
        feat = el.find('value/TerrainFeature')
        self.type = feat.get('{http://www.w3.org/2001/XMLSchema-instance}type')
        if   self.type == 'Tree':
            self.growthStage = int(feat.find('growthStage').text)
            self.treeType    = int(feat.find('treeType').text)
            self.flipped     = feat.find('flipped').text == 'true'
            self.stump       = feat.find('stump'  ).text == 'true'
            self.tapped      = feat.find('tapped' ).text == 'true'
            self.hasSeed     = feat.find('hasSeed').text == 'true'

        elif self.type == 'Grass':
            self.grassType         = int(feat.find('grassType').text)
            self.numberOfWeeds     = int(feat.find('numberOfWeeds').text)
            self.grassSourceOffset = int(feat.find('grassSourceOffset').text)

        elif self.type == 'Flooring':
            self.whichFloor = int(feat.find('whichFloor').text)
            self.whichView  = int(feat.find('whichView').text)
            key = 'floor%d' % self.whichFloor
            try:
                position = (self.pos.x, self.pos.y)
                connectables[key].append(position)
            except:
                connectables[key] = [position]
        elif self.type == "HoeDirt":
            self.fertilizer = int(feat.find('fertilizer').text)
            self.state = int(feat.find('state').text)
            position = tuple(dump_position(self.pos))
            # hoedirt is added to both if wet, and only the dry one if dry.
            # wet hoedirt is then overlapped with dry hoedirtposition = (self.pos.x, self.pos.y)
            try:
                connectables["hoedirt0"].append(position)
            except:
                connectables["hoedirt0"] = [position]
            if self.state == 1:
                try:
                    connectables["hoedirt1"].append(position)
                except:
                    connectables["hoedirt1"] = [position]
        else:
            print("Unhandled terrain feature type {}".format(self.type))

    def dump(self, save, connections):
        output = {
            'pos': dump_position(self.pos),
            }
        outputs = [output]

        # TODO
        if   self.type == 'Tree':
            ts = useTilesheet("TerrainFeatures/tree{:d}_{:s}".format(self.treeType, save.date.season), save)
            output['ts']  = ts
            if self.stump:
                output['idx'] = 20
                output['tileSize'] = [16, 32]
                output['offset'] = [0, 0]
            elif self.growthStage in [0, 1, 2]:
                if self.growthStage == 0:
                    output['idx'] = 26
                elif self.growthStage == 1:
                    output['idx'] = 24
                elif self.growthStage == 2:
                    output['idx'] = 25
            elif self.growthStage in [3, 4]:
                output['tileSize'] = [16, 32]
                output['offset'] = [0, 0]
                output['idx'] = 18
            else:
                output['tileSize'] = [48, 96]
                output['offset'] = [-16, 0]
                output['idx'] = 0
                # also add a stump.
                outputs.append({
                        'ts': ts,
                        'idx': 27,
                        "pos": dump_position(self.pos)
                    })

        elif self.type == 'Grass':
            output['ts']  = useTilesheet("TerrainFeatures/grass", save)
            output['idx'] = grassseasons[save.date.season]*3
            output['isGrass'] = True

        elif self.type == 'Flooring':
            output['ts']  = useTilesheet("TerrainFeatures/Flooring", save)
            output['idx'] = connections["floor%d" % self.whichFloor][tuple(dump_position(self.pos))]

        elif self.type == 'HoeDirt':
            output['ts'] = useTilesheet("TerrainFeatures/hoeDirt", save)
            idx = connections["hoedirt0"][tuple(dump_position(self.pos))]
            output['idx'] = idx
            # if dirt is wet, add the wet dirt on top of the dry dirt.
            if self.state == 1:
                outputs.append({
                        'pos': dump_position(self.pos),
                        'ts' : useTilesheet("TerrainFeatures/hoeDirt", save),
                        'idx': connections["hoedirt1"][tuple(dump_position(self.pos))]
                    })
        else:
            return []
        return outputs

class Location(object):
    def __init__(self, el):
        self.name       = el.find('name').text
        self.connectables = {}
        self.characters = [Character(c) for c in el.findall('characters/NPC')]
        self.items      = [Item(i, self.connectables) for i in el.findall('objects/item/value/Object')]
        self.buildings  = [Building(b)  for b in el.findall('buildings/Building')]
        self.resourceclumps = [ResourceClump(rc) for rc in el.findall('resourceClumps/ResourceClump')]
        self.features   = [Feature(f, self.connectables)   for f in el.findall('terrainFeatures/item')]

    def dump(self, save):
        output = {
                'name': self.name
            }
        connections = calculateConnectables(self.connectables)
        output['characters'] = [c.dump(save) for c in self.characters]
        output['items'] = [i.dump(save, connections) for i in self.items]
        output['buildings']  = [b.dump(save) for b in self.buildings ]

        if self.name == 'Farm':
            ts   = useTilesheet("Buildings/houses", save),
            pos  = [58,12]
            size = [10, 5]

            if   save.player.houseUpgradeLevel == 0:
                house = {
                        'ts':   ts,
                        'pos':  pos,
                        'size': size,
                        'idx':  0
                    }

            elif save.player.houseUpgradeLevel == 1:
                house = {
                        'ts':  ts,
                        'pos': pos,
                        'size': size,
                        'idx': 1
                    }

            elif save.player.houseUpgradeLevel == 2:
                house = {
                        'ts':  ts,
                        'pos': pos,
                        'size': size,
                        'idx': 2
                    }
           
            pos  = [25,10]
            size = [ 7, 6]

            # not sure if correct
            # not correct
            if   save.player.hasGreenhouse:
                greenhouse = {
                        'ts':  ts,
                        'pos': pos,
                        'size': size,
                        'idx': 4
                    }
            else:
                greenhouse = {
                        'ts':  ts,
                        'pos': pos,
                        'size': size,
                        'idx': 3
                    }

            output['buildings'].append(house)
            output['buildings'].append(greenhouse)

        output['features']   = []
        for f in self.features:
            output['features'].extend(f.dump(save, connections))
        for rc in self.resourceclumps:
            output['features'].append(rc.dump(save))
        return output

class Date(object):
    def __init__(self, year, season, day):
        self.year   = year
        self.season = season
        self.day    = day

    # nicked from https://codegolf.stackexchange.com/questions/4707/outputting-ordinal-numbers-1st-2nd-3rd#answer-4712
    @staticmethod
    def suffixed(n):
        return "{:d}{:s}".format(n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])

    def __str__(self):
        return '{:s} of {:s}, Year {:d}'.format(
                Date.suffixed(self.day),
                self.season.capitalize(),
                self.year
            )

    def dump(self):
        return str(self)

class Player(object):
    def __init__(self, el):
        self.name              = el.find('name').text
        self.farmName          = el.find('farmName').text + ' Farm'
        self.houseUpgradeLevel = int(el.find('houseUpgradeLevel').text)
        self.hasGreenhouse     = el.find('hasGreenhouse').text == 'true'

    def dump(self, save):
        return {
            'name':     self.name,
            'farmName': self.farmName
        }

class Save(object):
    @staticmethod
    def load(filename):
        tree = ET.parse(filename)
        root = tree.getroot()
        return Save(root)

    def __init__(self, el):
        self.date     = Date(
                int(el.find('year').text),
                    el.find('currentSeason').text,
                int(el.find('dayOfMonth').text)
            )

        self.player = Player(el.find('player'))
        self.locations = [Location(l) for l in el.findall('locations/GameLocation')]

    def dump(self):
        self.tilesheets = []
        print(names)
        return {
                'date':      self.date.dump(),
                'player':    self.player.dump(self),
                'locations': [l.dump(self) for l in self.locations],
                'tilesheets': self.tilesheets
            }


class SparsePositions:
    def __init__(self):
        self.positions = set()

    def get(self, xy):
        if xy in self.positions:
            return True
        return False

    def add(self, xy):
        self.positions.add(xy)

def getAny(posdicts, possiblekeys, xy):
    # if any of the posdicts has xy, return true
    for k in possiblekeys:
        if posdicts[k].get(xy):
            return True
    return False


# to lookup the correct floor tile from connections
# up, down, left, right
tilePositions = {
    0b0000: (0, 0),
    0b0001: (1, 3),
    0b0010: (3, 3),
    0b0011: (2, 3),
    0b0100: (0, 1),
    0b0101: (1, 0),
    0b0110: (3, 0),
    0b0111: (2, 0),
    0b1000: (0, 3),
    0b1001: (1, 2),
    0b1010: (3, 2),
    0b1011: (2, 2),
    0b1100: (0, 2),
    0b1101: (1, 1),
    0b1110: (3, 1),
    0b1111: (2, 1)
}

def calculateConnectables(connectables):
    result = {}
    posdicts = {} # save for gate logic.
    for type_ in connectables:
        if type_ == "fence4": 
            continue # fence4 is a gate. special code to handle.
        result[type_] = {} # dictionary of position to index.
        positions = connectables[type_] # array of all positions each connectable obj is at
        posdict = SparsePositions()
        # first build the lookup table
        for pos in positions:
            posdict.add(pos)
        for pos in positions:
            x, y = pos
            # next, check connections.
            hasUp = posdict.get((x, y-1))
            hasLeft = posdict.get((x-1, y))
            hasRight = posdict.get((x+1, y))
            hasDown = posdict.get((x, y+1))

            if type_.startswith("fence"):
                posdicts[type_] = posdict
                if hasLeft and hasRight:
                    # surprising, game does not care about up connections in this case
                    result[type_][pos] = 7
                elif hasUp:
                    if hasLeft:
                        result[type_][pos] = 8
                    elif hasRight:
                        result[type_][pos] = 6
                    else:
                        result[type_][pos] = 3
                else:
                    # no up, and not both left & right
                    if hasLeft:
                        result[type_][pos] = 2
                    elif hasRight:
                        result[type_][pos] = 0
                    else:
                        result[type_][pos] = 5
            elif type_.startswith("floor"):
                # represent state as one number for convenience
                state = 0
                if hasUp:
                    state += 8
                if hasDown:
                    state += 4
                if hasLeft:
                    state += 2
                if hasRight:
                    state += 1
                # tilex/y are because the sheet layout of floors are weird.
                # initialize to the topleft of sheet section for floor.
                floornum = int(type_[5:])
                tilex = (floornum % 4) * 4
                tiley = (floornum // 4) * 4
                dx, dy = tilePositions[state]
                tilex += dx
                tiley += dy
                result[type_][pos] = tilex + tiley * 16
            elif type_.startswith("hoedirt"):
                # represent state as one number for convenience
                state = 0
                if hasUp:
                    state += 8
                if hasDown:
                    state += 4
                if hasLeft:
                    state += 2
                if hasRight:
                    state += 1
                dirtnum = int(type_[7:])
                tilex, tiley = 4 * dirtnum, 0
                dx, dy = tilePositions[state]
                tilex += dx
                tiley += dy
                result[type_][pos] = tilex + tiley * 8
            else:
                print("Did not implement connections for %s yet" % type_)
                result[type_] = {}
                for pos in connections[type_]:
                    result[pos] = 0
    # now do gates. if there are ANY fences on either side, it is connected.
    fencetypes = [x for x in posdicts if (x.startswith("fence") and x != "fence4")]
    type_ = "fence4"
    result[type_] = {}
    if "fence4" in connectables:
        for pos in connectables[type_]:
            x, y = pos
            hasUp = getAny(posdicts, fencetypes, (x, y-1))
            hasDown = getAny(posdicts, fencetypes, (x, y+1))
            hasLeft = getAny(posdicts, fencetypes, (x-1, y))
            hasRight = getAny(posdicts, fencetypes, (x+1, y))
            result[type_][pos] = 17 # defualt unconnected
            if hasDown and hasUp and not hasLeft and not hasRight:
                result[type_][pos] = 16
            elif not hasDown and not hasUp and hasLeft and hasRight:
                result[type_][pos] = 12
            result[type_][pos] = 17 # because weird widths
    return result

def dump_position(pos):
    return [ pos.x, pos.y ]

def useTilesheet(filename, save):
    for idx, ts in enumerate(save.tilesheets):
        if ts == filename:
            return idx
    else:
        save.tilesheets.append(filename)
        return len(save.tilesheets)-1