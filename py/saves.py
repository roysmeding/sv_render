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

class Item(object):
    def __init__(self, el):
        self.name = el.find('Name').text
        self.type = el.get('{http://www.w3.org/2001/XMLSchema-instance}type')
        self.category     = int(el.find('category').text)
        self.bigCraftable = el.find('bigCraftable').text == 'true'
        self.pos          = Position.fromElement(el.find('tileLocation'))
        self.sheetIndex   = int(el.find('parentSheetIndex').text)

        if self.type == 'Fence':
            self.whichType = int(el.find('whichType').text)

        print(self.name, self.bigCraftable)

class Building(object):
    def __init__(self, el):
        self.type = el.find('buildingType').text
        self.pos  = Position(
                int(el.find('tileX').text),
                int(el.find('tileY').text)
            )

        self.tilesWide = int(el.find('tilesWide').text)
        self.tilesHigh = int(el.find('tilesHigh').text)

class Feature(object):
    def __init__(self, el):
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

        else:
            print("Unhandled terrain feature type {}".format(self.type))

class Location(object):
    def __init__(self, el):
        self.name       = el.find('name').text
        self.characters = [Character(c) for c in el.findall('characters/NPC')]
        self.items      = [Item(i)      for i in el.findall('objects/item/value/Object')]
        self.buildings  = [Building(b)  for b in el.findall('buildings/Building')]
        self.features   = [Feature(f)   for f in el.findall('terrainFeatures/item')]

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

class Player(object):
    def __init__(self, el):
        self.name              = el.find('name').text
        self.farmName          = el.find('farmName').text + ' Farm'
        self.houseUpgradeLevel = int(el.find('houseUpgradeLevel').text)
        self.hasGreenhouse     = el.find('hasGreenhouse').text == 'true'

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


def dump_date(date):
    return str(date)

def dump_position(pos):
    return [ pos.x, pos.y ]

def useTilesheet(filename, save):
    for idx, ts in enumerate(save.tilesheets):
        if ts == filename:
            return idx
    else:
        save.tilesheets.append(filename)
        return len(save.tilesheets)-1

def dump_player(player, save):
    return {
            'name':     player.name,
            'farmName': player.farmName
        }

def dump_character(character, save):
    output = {
            'name': character.name,
            'pos':  dump_position(character.pos)
        }

    # determine tilesheet and index
    if   character.type == 'Cat':
        ts = 'Animals/cat'
    elif character.type == 'Dog':
        ts = 'Animals/dog'
    elif character.type == 'Horse':
        ts = 'Animals/horse'
    else:
        ts = 'Characters/'+character.name
        
    output['ts']  = useTilesheet(ts, save)
    output['idx'] = 0

    return output

def dump_item(item, save):
    output = {
            'name': item.name,
            'pos': dump_position(item.pos)
        }

    if   item.bigCraftable:
        output['ts']  = useTilesheet('TileSheets/Craftables', save)
        output['idx'] = item.sheetIndex

    elif item.type == 'Fence':
        output['ts']  = useTilesheet('LooseSprites/Fence{:d}'.format(item.whichType), save)
        output['idx'] = 0   # TODO

    else:
        output['ts']  = useTilesheet('Maps/springobjects', save)
        output['idx'] = item.sheetIndex

    return output

def dump_building(building, save):
    output = {
            'pos':  dump_position(building.pos),
            'size': [ building.tilesWide, building.tilesHigh ],
            'type': building.type
        }

    output['ts']  = useTilesheet('Buildings/'+building.type, save)
    output['idx'] = 0

    return output

def dump_feature(feature, save):
    output = {
            'pos': dump_position(feature.pos),
        }

    # TODO
    if   feature.type == 'Tree':
        output['ts']  = useTilesheet("TerrainFeatures/tree{:d}_{:s}".format(feature.treeType, save.date.season), save)
        if   feature.stump:
            output['idx'] = 3
        elif feature.growthStage == 0:
            output['idx'] = 6
        elif feature.growthStage == 1:
            output['idx'] = 4
        elif feature.growthStage == 2:
            output['idx'] = 5
        elif feature.growthStage == 3:
            output['idx'] = 1
        else:
            output['idx'] = 0

    elif feature.type == 'Grass':
        output['ts']  = useTilesheet("TerrainFeatures/grass", save)
        output['idx'] = feature.grassType*3

    elif feature.type == 'Flooring':
        output['ts']  = useTilesheet("TerrainFeatures/Flooring", save)
        output['idx'] = (feature.whichFloor%4)*4 + (feature.whichFloor//4)*64

    else:
        return None

    return output


def dump_location(location, save):
    output = {
            'name': location.name
        }

    if len(location.characters) > 0:
        output['characters'] = [dump_character(c, save) for c in location.characters]

    if len(location.items) > 0:
        output['items']      = [dump_item     (i, save) for i in location.items     ]

    output['buildings']  = [dump_building (b, save) for b in location.buildings ]

    if location.name == 'Farm':
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
       
        pos  = [24,10]
        size = [ 7, 6]

        # not sure if correct
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


    if len(location.features) > 0:
        output['features']   = [dump_feature  (f, save) for f in location.features  ]

    return output

def dump_save(save):
    save.tilesheets = []

    return {
            'date':      dump_date(save.date),
            'player':    dump_player(save.player, save),
            'locations': [dump_location(l, save) for l in save.locations],
            'tilesheets': save.tilesheets
        }
