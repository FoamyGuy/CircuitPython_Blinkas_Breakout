import board
import displayio
import adafruit_imageload
from displayio import Palette
from adafruit_display_text import label
import terminalio
from adafruit_pybadger import PyBadger
import time

# Direction constants for comparison
UP = 0
DOWN = 1
RIGHT = 2
LEFT = 3

MOVING_DIRECTION = -1

HIDE_SPLASH_TIME = -1

# how long to wait between rendering frames
FPS_DELAY = 1/30

# how many tiles can fit on thes screen. Tiles are 16x16
SCREEN_HEIGHT_TILES = 8
SCREEN_WIDTH_TILES = 10

MAP_LIST = [
    "map.csv",
    "map1.csv",
    "map2.csv",
    "map3.csv",
    "map4.csv",
    "map5.csv"
]

CUR_MAP_INDEX = 0

# hold the map state as it came out of the csv. Only holds non-entities.
ORIGINAL_MAP = {}

# hold the current map state if/when it changes. Only holds non-entities.
CURRENT_MAP = {}

MAP_HEIGHT = 0
MAP_WIDTH = 0

# dictionary with tuple keys that map to tile type values
# e.x. {(0,0): "left_wall", (1,1): "floor"}
CAMERA_VIEW = {}

# how far offset the camera is from the CURRENT_MAP
# used to determine where things are at in the camera view vs. the MAP
CAMERA_OFFSET_X = 0
CAMERA_OFFSET_Y = 0

# list of sprite objects, one for each entity
ENTITY_SPRITES = []

# Dictionary with touple keys that map to lists of entity objects.
# Each one has the index of the sprite in the ENTITY_SPRITES list
# and the tile type string
ENTITY_SPRITES_DICT = {}

# list of entities that need to be on the screen currently based on the camera view
NEED_TO_DRAW_ENTITIES = []

# hold the location of the player in tile coordinates
PLAYER_LOC = (0,0)

INVENTORY = []

MAP_CHIP_COUNT = 0


# return from CURRENT_MAP the tile name of the tile of the given coords
def get_tile(coords):
    return CURRENT_MAP[coords[0], coords[1]]

# return from TILES dict the tile object with stats and behavior for the tile at the given coords.
def get_tile_obj(coords):
    return TILES[CURRENT_MAP[coords[0], coords[1]]]

# check the can_walk property of the tile at the given coordinates
def is_tile_moveable(tile_coords):
    return TILES[CURRENT_MAP[tile_coords[0], tile_coords[1]]]['can_walk']

def take_item(to_coords, from_coords, entity_obj):
    print(entity_obj)
    INVENTORY.append(entity_obj["map_tile_name"])
    ENTITY_SPRITES_DICT[to_coords].remove(entity_obj)
    if len(ENTITY_SPRITES_DICT[to_coords]) == 0:
        del ENTITY_SPRITES_DICT[to_coords]

    if (-1,-1) in ENTITY_SPRITES_DICT:
        ENTITY_SPRITES_DICT[-1,-1].append(entity_obj)
    else:
        ENTITY_SPRITES_DICT[-1,-1] = [entity_obj]

    return True;


def heart_walk(to_coords, from_coords, entity_obj):
    global PLAYER_LOC, CUR_MAP_INDEX
    print("inside heart_walk")
    print("%s -> %s" % (from_coords, to_coords))
    if "robot" in INVENTORY:
        # you win
        text_area.text = "You Win\n =D"
        text_area.y = int(128/2 - 30)
        group.append(splash)
        time.sleep(2)
        group.remove(splash)
        CUR_MAP_INDEX += 1
        if CUR_MAP_INDEX >= len(MAP_LIST):
            CUR_MAP_INDEX = 0
        load_map(MAP_LIST[CUR_MAP_INDEX])
    else:
        return False

def robot_walk(to_coords, from_coords, entity_obj):
    global PLAYER_LOC
    print("inside robot_walk")
    print("%s -> %s" % (from_coords, to_coords))
    if INVENTORY.count("chip") == MAP_CHIP_COUNT:
        # player can move without losing
        INVENTORY.append(entity_obj["map_tile_name"])
        ENTITY_SPRITES_DICT[to_coords].remove(entity_obj)
        if len(ENTITY_SPRITES_DICT[to_coords]) == 0:
            del ENTITY_SPRITES_DICT[to_coords]

        if (-1,-1) in ENTITY_SPRITES_DICT:
            ENTITY_SPRITES_DICT[-1,-1].append(entity_obj)
        else:
            ENTITY_SPRITES_DICT[-1,-1] = [entity_obj]
        return True
    else:
        return False

def door_walk(to_coords, from_coords, entity_obj):
    door_key_dict = {
        "door": "key",
        "red_door": "red_key",
        "yellow_door": "yellow_key",
        "cyan_door": "cyan_key",
    }
    if entity_obj["map_tile_name"] in door_key_dict:
        if door_key_dict[entity_obj["map_tile_name"]] in INVENTORY:
            INVENTORY.remove(door_key_dict[entity_obj["map_tile_name"]])
            # remove door entity
            ENTITY_SPRITES_DICT[to_coords].remove(entity_obj)
            if len(ENTITY_SPRITES_DICT[to_coords]) == 0:
                del ENTITY_SPRITES_DICT[to_coords]
            if (-1,-1) in ENTITY_SPRITES_DICT:
                ENTITY_SPRITES_DICT[-1,-1].append(entity_obj)
            else:
                ENTITY_SPRITES_DICT[-1,-1] = [entity_obj]

            return True
        else:
            return False

    return False

# behavior function that makes the player lose if they don't have the water shoes
def water_walk(to_coords, from_coords, tile_name):
    global PLAYER_LOC
    print("inside water_walk")
    print("%s -> %s" % (from_coords, to_coords))
    if "water_shoes" in INVENTORY:
        # player can move without losing
        return True
    else:
        PLAYER_LOC = to_coords
        # if player is past x tile coordinate 4
        camera_loc = (max(0, PLAYER_LOC[0]-4), max(0, PLAYER_LOC[1]-3))
        # if player is past x tile coordinate 4
        set_camera_view(camera_loc[0], camera_loc[1], 10, 8)

        # draw the camera
        draw_camera_view()
        draw_player()

        time.sleep(0.5)
        text_area.text = "Game Over\nWater"
        text_area.y = int(128/2 - 30)
        group.append(splash)
        time.sleep(2)
        group.remove(splash)
        load_map(MAP_LIST[CUR_MAP_INDEX])

# behavior function that makes the player lose if they don't have the fire shoes
def fire_walk(to_coords, from_coords, tile_name):
    global PLAYER_LOC
    print("inside fire_walk")
    print("%s -> %s" % (from_coords, to_coords))
    if "fire_shoes" in INVENTORY:
        # player can move without losing
        return True
    else:
        PLAYER_LOC = to_coords
        # if player is past x tile coordinate 4
        camera_loc = (max(0, PLAYER_LOC[0]-4), max(0, PLAYER_LOC[1]-3))
        # if player is past x tile coordinate 4
        set_camera_view(camera_loc[0], camera_loc[1], 10, 8)

        # draw the camera
        draw_camera_view()
        draw_player()

        time.sleep(0.5)
        text_area.text = "Game Over\nFire"
        text_area.y = int(128/2 - 30)
        group.append(splash)
        time.sleep(2)
        group.remove(splash)
        load_map(MAP_LIST[CUR_MAP_INDEX])


# behavior function that makes the player slide across this tile
def conveyor_slide(to_coords, from_coords, tile_name):

    if "conveyor_shoes" in INVENTORY:
        # player can move without sliding
        print("player can move without sliding")
        return True

    global PLAYER_LOC
    slide_x_offset = 0
    slide_y_offset = 0
    print("inside conveyor slide")
    print("%s -> %s" % (from_coords, to_coords))


    if tile_name == "conveyor_up":
            slide_x_offset = 0
            slide_y_offset = -1

    if tile_name == "conveyor_down":
            slide_x_offset = 0
            slide_y_offset = 1
    if tile_name == "conveyor_left":
        slide_x_offset = -1
        slide_y_offset = 0
    if tile_name == "conveyor_right":
        slide_x_offset = 1
        slide_y_offset = 0
    # coords where we will be sliding the player to
    slide_to_tile_coords = (to_coords[0]+ slide_x_offset, to_coords[1]+ slide_y_offset)
    print("sliding to: %s, %s" % slide_to_tile_coords)
    # check if the player is allowed to move to there
    if is_tile_moveable(slide_to_tile_coords):
        tile_obj = TILES[CURRENT_MAP[slide_to_tile_coords]]
        print("calling move player %s, %s" % (slide_x_offset, slide_y_offset))

        PLAYER_LOC = to_coords
        print("PLAYER_LOC before: %s, %s" % (PLAYER_LOC))


        #camera_loc = (max(0, PLAYER_LOC[0]-4), max(0, PLAYER_LOC[1]-3))
        set_camera_view(
            max(min(PLAYER_LOC[0]-4,MAP_WIDTH-SCREEN_WIDTH_TILES),0),
            max(min(PLAYER_LOC[1]-3,MAP_HEIGHT-SCREEN_HEIGHT_TILES),0),
            10,
            8
        )

        # draw the camera
        draw_camera_view()

        draw_player()
        time.sleep(FPS_DELAY)

        move_player(slide_x_offset, slide_y_offset)
        """
        print("checking before_move on %s" % CURRENT_MAP[slide_to_tile_coords])
        if "before_move" in tile_obj.keys():
            PLAYER_LOC = to_coords
            print("PLAYER_LOC before: %s, %s" % (PLAYER_LOC))
            # if player is past x tile coordinate 4
            if PLAYER_LOC[0] > 4:
                # set camera to player location offset by 4
                set_camera_view(int(PLAYER_LOC[0]-4),0,10,8)
            else:
                # set camera to 0,0
                set_camera_view(0,0,10,8)
            # draw the camera
            draw_camera_view()

            draw_player()
            time.sleep(FPS_DELAY)
            PLAYER_LOC = slide_to_tile_coords
            print("slid player returning false")
            print("PLAYER_LOC after: %s, %s" % (PLAYER_LOC))
            if tile_obj['before_move'](slide_to_tile_coords,to_coords,CURRENT_MAP[slide_to_tile_coords]):
                return False
        else:

            print("PLAYER_LOC before: %s, %s" % (PLAYER_LOC))
            # slide the player and return false to prevent original movement
            PLAYER_LOC = to_coords
            draw_player()
            time.sleep(FPS_DELAY)
            PLAYER_LOC = slide_to_tile_coords
            print("slid player returning false")
            print("PLAYER_LOC after: %s, %s" % (PLAYER_LOC))

            return False

        """
    else:
        # return true to allow original move, but no sliding
        print("did not slide player returning true")
        return True



# behavior function that makes the player slide across this tile
def ice_slide(to_coords, from_coords, tile_name):

    if "ice_shoes" in INVENTORY:
        # player can move without sliding
        return True

    global PLAYER_LOC
    slide_x_offset = 0
    slide_y_offset = 0
    print("inside slide")
    print("%s -> %s" % (from_coords, to_coords))
    if to_coords[0] < from_coords[0]:
        # moving left
        MOVING_DIRECTION = LEFT
        slide_x_offset = -1
        slide_y_offset = 0

    elif to_coords[0] > from_coords[0]:
        # moving right
        MOVING_DIRECTION = RIGHT
        slide_x_offset = 1
        slide_y_offset = 0

    elif to_coords[1] < from_coords[1]:
        # moving up
        MOVING_DIRECTION = UP
        slide_x_offset = 0
        slide_y_offset = -1

    elif to_coords[1] > from_coords[1]:
        # moving down
        MOVING_DIRECTION = DOWN
        slide_x_offset = 0
        slide_y_offset = 1

    if tile_name == "ice_floor_top_left":
        if MOVING_DIRECTION == LEFT:
            slide_x_offset = 0
            slide_y_offset = 1
        elif MOVING_DIRECTION == UP:
            slide_x_offset = 1
            slide_y_offset = 0
        else:
            return False
    if tile_name == "ice_floor_bottom_left":
        if MOVING_DIRECTION == LEFT:
            slide_x_offset = 0
            slide_y_offset = -1
        elif MOVING_DIRECTION == DOWN:
            slide_x_offset = 1
            slide_y_offset = 0
        else:
            return False
    if tile_name == "ice_floor_bottom_right":
        if MOVING_DIRECTION == RIGHT:
            slide_x_offset = 0
            slide_y_offset = -1
        elif MOVING_DIRECTION == DOWN:
            slide_x_offset = -1
            slide_y_offset = 0
        else:
            return False
    if tile_name == "ice_floor_top_right":
        if MOVING_DIRECTION == RIGHT:
            slide_x_offset = 0
            slide_y_offset = 1
        elif MOVING_DIRECTION == UP:
            slide_x_offset = -1
            slide_y_offset = 0
        else:
            return False
    # coords where we will be sliding the player to
    slide_to_tile_coords = (to_coords[0]+ slide_x_offset, to_coords[1]+ slide_y_offset)

    print("sliding to %s " % CURRENT_MAP[slide_to_tile_coords])
    # check if the player is allowed to move to there
    if is_tile_moveable(slide_to_tile_coords):
        tile_obj = TILES[CURRENT_MAP[slide_to_tile_coords]]

        PLAYER_LOC = to_coords

        #camera_loc = (max(0, PLAYER_LOC[0]-4), max(0, PLAYER_LOC[1]-3))
        #set_camera_view(camera_loc[0], camera_loc[1], 10, 8)
        set_camera_view(
            max(min(PLAYER_LOC[0]-4,MAP_WIDTH-SCREEN_WIDTH_TILES),0),
            max(min(PLAYER_LOC[1]-3,MAP_HEIGHT-SCREEN_HEIGHT_TILES),0),
            10,
            8
        )
        # draw the camera
        draw_camera_view()

        draw_player()
        time.sleep(FPS_DELAY)
        move_player(slide_x_offset, slide_y_offset)
        """
        print("checking before_move on %s" % CURRENT_MAP[slide_to_tile_coords])
        if "before_move" in tile_obj.keys():
            PLAYER_LOC = to_coords
            # if player is past x tile coordinate 4
            if PLAYER_LOC[0] > 4:
                # set camera to player location offset by 4
                set_camera_view(int(PLAYER_LOC[0]-4),0,10,8)
            else:
                # set camera to 0,0
                set_camera_view(0,0,10,8)
            # draw the camera
            draw_camera_view()

            draw_player()
            PLAYER_LOC = slide_to_tile_coords
            time.sleep(FPS_DELAY)
            print("slid player returning false")
            print("PLAYER_LOC after: %s, %s" % (PLAYER_LOC))
            if tile_obj['before_move'](slide_to_tile_coords,to_coords,CURRENT_MAP[slide_to_tile_coords]):
                return False
        else:

            print("PLAYER_LOC before: %s, %s" % (PLAYER_LOC))
            # slide the player and return false to prevent original movement
            PLAYER_LOC = to_coords
            draw_player()
            time.sleep(FPS_DELAY)
            PLAYER_LOC = slide_to_tile_coords
            print("slid player returning false")
            print("PLAYER_LOC after: %s, %s" % (PLAYER_LOC))

            return False
        """


    else:
        # return true to allow original move, but no sliding
        print("did not slide player returning true")
        return True

# behavior function that allows the player to push the entity
def allow_push(to_coords, from_coords, entity_obj):
    push_x_offset = 0
    push_y_offset = 0
    print("inside allow push")
    print("%s -> %s" % (from_coords, to_coords))
    if to_coords[0] < from_coords[0]:
        # moving left
        push_x_offset = -1
        push_y_offset = 0

    elif to_coords[0] > from_coords[0]:
        # moving right
        push_x_offset = 1
        push_y_offset = 0

    elif to_coords[1] < from_coords[1]:
        # moving up
        push_x_offset = 0
        push_y_offset = -1

    elif to_coords[1] > from_coords[1]:
        # moving down
        push_x_offset = 0
        push_y_offset = 1

    # coords where we will be pushing the entity to
    push_to_tile_coords = (to_coords[0]+ push_x_offset, to_coords[1]+ push_y_offset)

    # check if the entity is allowed to move to there
    if is_tile_moveable(push_to_tile_coords):
        #print("dict before %s" % ENTITY_SPRITES_DICT)

        # check if there are etity(s) at the tile we are trying to push to.
        if push_to_tile_coords in ENTITY_SPRITES_DICT:
            # append the thing we are pushing to the the list at the new coordinates in the dictionary
            ENTITY_SPRITES_DICT[push_to_tile_coords].append(entity_obj)
        else:
            # create a list with the thing we are pushing and store it in the dictionary
            ENTITY_SPRITES_DICT[push_to_tile_coords] = [entity_obj]

        # remove the thing we are pushing from it's old location
        ENTITY_SPRITES_DICT[to_coords].remove(entity_obj)

        # if there are no entities left in the old location
        if len(ENTITY_SPRITES_DICT[to_coords]) == 0:
            # delete the empty lyst
            del ENTITY_SPRITES_DICT[to_coords]
        #print("dict after %s" % ENTITY_SPRITES_DICT)

        # return true to allow player to move
        return True
    # if we return false player won't be able to move
    return False

# main dictionary that maps tile type strings to objects.
# each one stores the sprite_sheet index and any necessary
# behavioral stats like can_walk or before_move
TILES = {
    # empty strings default to floor and no walk.
    "": {
        "sprite_index": 52,
        "can_walk": False
    },
    "empty": {
        "sprite_index": 52,
        "can_walk": False
    },
    "floor": {
        "sprite_index": 10,
        "can_walk": True
    },
    "top_left_wall": {
        "sprite_index": 3,
        "can_walk": False
    },
    "top_wall": {
        "sprite_index": 4,
        "can_walk": False
    },
    "top_right_wall": {
        "sprite_index": 5,
        "can_walk": False
    },
    "bottom_left_wall": {
        "sprite_index": 15,
        "can_walk": False
    },
    "bottom_wall": {
        "sprite_index": 16,
        "can_walk": False
    },
    "bottom_right_wall": {
        "sprite_index": 17,
        "can_walk": False
    },
    "right_wall": {
        "sprite_index": 11,
        "can_walk": False
    },
    "left_wall": {
        "sprite_index": 9,
        "can_walk": False
    },
    "robot": {
        "sprite_index": 49,
        "can_walk": True,
        "entity": True,
        "before_move": robot_walk
    },
    "heart": {
        "sprite_index": 50,
        "can_walk": True,
        "entity": True,
        "before_move": heart_walk
    },
    "player": {
        "sprite_index": 48,
        "entity": True,
    },
    "fire_floor": {
        "sprite_index": 20,
        "before_move": fire_walk,
        "can_walk": True
    },
    "water_floor": {
        "sprite_index": 37,
        "before_move": water_walk,
        "can_walk": True
    },
    "ice_floor": {
        "sprite_index": 7,
        "before_move": ice_slide,
        "can_walk": True
    },
    "ice_floor_top_left": {
        "sprite_index": 18,
        "before_move": ice_slide,
        "can_walk": True
    },
    "ice_floor_bottom_left": {
        "sprite_index": 24,
        "before_move": ice_slide,
        "can_walk": True
    },
    "ice_floor_bottom_right": {
        "sprite_index": 25,
        "before_move": ice_slide,
        "can_walk": True
    },
    "ice_floor_top_right": {
        "sprite_index": 19,
        "before_move": ice_slide,
        "can_walk": True
    },
    "conveyor_down": {
        "sprite_index": 22,
        "before_move": conveyor_slide,
        "can_walk": True
    },
    "conveyor_up": {
        "sprite_index": 27,
        "before_move": conveyor_slide,
        "can_walk": True
    },
    "conveyor_right": {
        "sprite_index": 28,
        "before_move": conveyor_slide,
        "can_walk": True
    },
    "conveyor_left": {
        "sprite_index": 21,
        "before_move": conveyor_slide,
        "can_walk": True
    },
    "ice_shoes": {
        "sprite_index": 34,
        "before_move": take_item,
        "entity": True,
        "can_walk": True
    },
    "fire_shoes": {
        "sprite_index": 29,
        "before_move": take_item,
        "entity": True,
        "can_walk": True
    },
    "water_shoes": {
        "sprite_index": 33,
        "before_move": take_item,
        "entity": True,
        "can_walk": True
    },
    "conveyor_shoes": {
        "sprite_index": 23,
        "before_move": take_item,
        "entity": True,
        "can_walk": True
    },
    "key": {
        "sprite_index": 53,
        "before_move": take_item,
        "entity": True,
        "can_walk": True
    },
    "door": {
        "sprite_index": 35,
        "before_move": door_walk,
        "entity": True,
        "entity": True,
        "can_walk": True
    },
    "red_key": {
        "sprite_index": 47,
        "before_move": take_item,
        "entity": True,
        "can_walk": True
    },
    "red_door": {
        "sprite_index": 41,
        "before_move": door_walk,
        "entity": True,
        "entity": True,
        "can_walk": True
    },
    "yellow_key": {
        "sprite_index": 46,
        "before_move": take_item,
        "entity": True,
        "can_walk": True
    },
    "yellow_door": {
        "sprite_index": 40,
        "before_move": door_walk,
        "entity": True,
        "entity": True,
        "can_walk": True
    },
    "cyan_key": {
        "sprite_index": 45,
        "before_move": take_item,
        "entity": True,
        "can_walk": True
    },
    "cyan_door": {
        "sprite_index": 39,
        "before_move": door_walk,
        "entity": True,
        "entity": True,
        "can_walk": True
    },
    "chip": {
        "sprite_index": 51,
        "before_move": take_item,
        "entity": True,
        "can_walk": True
    }


}

# Badger object for easy button handling
badger = PyBadger()

# display object variable
display = board.DISPLAY

# Load the sprite sheet (bitmap)
sprite_sheet, palette = adafruit_imageload.load("/sprite_sheet.bmp",
                                                bitmap=displayio.Bitmap,
                                                palette=displayio.Palette)

# make bright pink be transparent so entities can be drawn on top of map tiles
palette.make_transparent(13)

# Create the castle TileGrid
castle = displayio.TileGrid(sprite_sheet, pixel_shader=palette,
                            width = 10,
                            height = 8,
                            tile_width = 16,
                            tile_height = 16)



# Create a Group to hold the castle and add it
castle_group = displayio.Group()
castle_group.append(castle)

sprite_group = displayio.Group(max_size=64)

# Create a Group to hold the sprite and castle
group = displayio.Group()

# Add the sprite and castle to the group
group.append(castle_group)



# Make the display context
splash = displayio.Group(max_size=10)

# Draw a green background
color_bitmap = displayio.Bitmap(160, 128, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x000077

bg_sprite = displayio.TileGrid(color_bitmap,
                               pixel_shader=color_palette,
                               x=0, y=0)

splash.append(bg_sprite)

# Draw a smaller inner rectangle
inner_bitmap = displayio.Bitmap(160-30, 128-30, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0xAA0088 # Purple
inner_sprite = displayio.TileGrid(inner_bitmap,
                                  pixel_shader=inner_palette,
                                  x=15, y=15)
splash.append(inner_sprite)

# Draw a label
text_group = displayio.Group(max_size=64, scale=1, x=24, y=24)

text = "Game Over"
text_area = label.Label(terminalio.FONT, text=" "*64, color=0xFFFF00)
text_area.text = text
text_group.append(text_area) # Subgroup for text scaling
splash.append(text_group)

sprite = None

#group.append(splash)

def load_map(file_name):
    global sprite, ORIGINAL_MAP, CURRENT_MAP, ENTITY_SPRITES
    global ENTITY_SPRITES_DICT, INVENTORY, PLAYER_LOC, sprite_group
    global CAMERA_VIEW, MAP_HEIGHT, MAP_WIDTH
    global group
    global MAP_CHIP_COUNT


    for cur_s in ENTITY_SPRITES:
        sprite_group.remove(cur_s)
    try:
        sprite_group.remove(sprite)
    except:
        pass

    ORIGINAL_MAP = {}
    CURRENT_MAP = {}
    ENTITY_SPRITES = []
    ENTITY_SPRITES_DICT = {}
    CAMERA_VIEW = {}
    INVENTORY = []
    MAP_CHIP_COUNT = 0

    # Open and read raw string from the map csv file
    f = open(file_name, 'r')
    map_csv_str = f.read()
    f.close()

    # split the raw string into lines
    map_csv_lines = map_csv_str.replace("\r", "").split("\n")

    # if the last row is empty then remove it
    if len(map_csv_lines[-1]) == 0:
        del map_csv_lines[-1]

    # set the WIDTH and HEIGHT variables.
    # this assumes the map is rectangular.
    MAP_HEIGHT = len(map_csv_lines)
    MAP_WIDTH = len(map_csv_lines[0].split(","))

    #print(TILES.keys())
    #print(map_csv_lines)

    # loop over each line storing index in y variable
    for y, line in enumerate(map_csv_lines):
        # ignore empty line
        if line != "":
            # loop over each tile type separated by commas, storing index in x variable
            for x, tile_name in enumerate(line.split(",")):
                print("%s '%s'" % (len(tile_name), str(tile_name)))

                # if the tile exists in our main dictionary
                if tile_name in TILES.keys():

                    # if the tile is an entity
                    if 'entity' in TILES[tile_name].keys() and TILES[tile_name]['entity']:
                        if tile_name == "chip":
                            MAP_CHIP_COUNT += 1
                        # set the map tiles to floor
                        ORIGINAL_MAP[x,y] = "floor"
                        CURRENT_MAP[x,y] = "floor"

                        # if it's the player
                        if tile_name == "player":
                            # Create the sprite TileGrid
                            sprite = displayio.TileGrid(sprite_sheet, pixel_shader=palette,
                                width = 1,
                                height = 1,
                                tile_width = 16,
                                tile_height = 16,
                                default_tile = TILES[tile_name]['sprite_index'])

                            # set the position of sprite on screen
                            sprite.x = x*16
                            sprite.y = y*16

                            # set position in x,y tile coords for reference later
                            PLAYER_LOC = (x,y)

                            # add sprite to the group
                            sprite_group.append(sprite)
                        else: # not the player
                            # Create the sprite TileGrid
                            entity_srite = displayio.TileGrid(sprite_sheet, pixel_shader=palette,
                                        width = 1,
                                        height = 1,
                                        tile_width = 16,
                                        tile_height = 16,
                                        default_tile = TILES[tile_name]['sprite_index'])
                            # set the position of sprite on screen
                            # default to offscreen
                            entity_srite.x = -16
                            entity_srite.y = -16

                            # add the sprite object to ENTITY_SPRITES list
                            ENTITY_SPRITES.append(entity_srite)
                            #print("setting entity_sprites_dict[%s,%s]" % (x,y))

                            # create an entity obj
                            entity_obj = {
                                "entity_sprite_index": len(ENTITY_SPRITES) - 1,
                                "map_tile_name": tile_name
                            }

                            # if there are no entities at this location yet
                            if (x,y) not in ENTITY_SPRITES_DICT:
                                # create a list and add it to the dictionary at the x,y location
                                ENTITY_SPRITES_DICT[x, y] = [entity_obj]
                            else:
                                # append the entity to the existing list in the dictionary
                                ENTITY_SPRITES_DICT[x, y].append(entity_obj)

                    else: # tile is not entity
                        # set the tile_name into MAP dictionaries
                        ORIGINAL_MAP[x, y] = tile_name
                        CURRENT_MAP[x, y] = tile_name

                else: # tile type wasn't found in dict
                    print("tile: %s not found in TILES dict" % tile_name)

    # add all entity sprites to the group
    for entity in ENTITY_SPRITES:
        sprite_group.append(entity)

# Add the Group to the Display

load_map(MAP_LIST[CUR_MAP_INDEX])
group.append(sprite_group)

display.show(group)
# variables to store previous value of button state
prev_up = False
prev_down = False
prev_left = False
prev_right = False

prev_b = False
prev_a = False
prev_start = False
prev_select = False

# helper function returns true if player is allowed to move given direction
# based on can_walk property of the tiles next to the player
def can_player_move(direction):
    if direction == UP:
        tile_above_coords = (PLAYER_LOC[0], PLAYER_LOC[1] - 1)
        if tile_above_coords[1] < 0:
            return False
        return TILES[CURRENT_MAP[tile_above_coords[0], tile_above_coords[1]]]['can_walk']

    if direction == DOWN:
        tile_below_coords = (PLAYER_LOC[0], PLAYER_LOC[1] + 1)
        if tile_below_coords[1] >= MAP_HEIGHT:
            return False
        return TILES[CURRENT_MAP[tile_below_coords[0], tile_below_coords[1]]]['can_walk']

    if direction == LEFT:
        tile_left_of_coords = (PLAYER_LOC[0]-1, PLAYER_LOC[1])
        if tile_left_of_coords[0] < 0:
            return False
        return TILES[CURRENT_MAP[tile_left_of_coords[0], tile_left_of_coords[1]]]['can_walk']

    if direction == RIGHT:
        tile_right_of_coords = (PLAYER_LOC[0] + 1, PLAYER_LOC[1])
        if tile_right_of_coords[0] >= MAP_WIDTH:
            return False
        return TILES[CURRENT_MAP[tile_right_of_coords[0], tile_right_of_coords[1]]]['can_walk']

# set the appropriate tiles into the CAMERA_VIEW dictionary
# based on given starting coords and size
def set_camera_view(startX, startY, width, height):
    global CAMERA_OFFSET_X
    global CAMERA_OFFSET_Y
    # set the offset variables for use in other parts of the code
    CAMERA_OFFSET_X = startX
    CAMERA_OFFSET_Y = startY

    # loop over the rows and indexes in the desired size section
    for y_index, y in enumerate(range(startY, startY+height)):
        # loop over columns and indexes in the desired size section
        for x_index, x in enumerate(range(startX, startX+width)):
            #print("setting camera_view[%s,%s]" % (x_index,y_index))
            try:
                # set the tile at the current coordinate of the MAP into the CAMERA_VIEW
                CAMERA_VIEW[x_index,y_index] = CURRENT_MAP[x,y]
            except KeyError:
                # if coordinate is out of bounds set it to empty by default
                CAMERA_VIEW[x_index,y_index] = "empty"


def move_player(x_offset, y_offset):
    global PLAYER_LOC
    # variable to store if player is allowed to move
    can_move = False

    # coordinates the player is moving to
    moving_to_coords = (PLAYER_LOC[0] + x_offset, PLAYER_LOC[1] + y_offset)

    # tile name of the spot player is moving to
    moving_to_tile_name = CURRENT_MAP[moving_to_coords[0], moving_to_coords[1]]
    print("moving to %s checking before_move" % moving_to_tile_name )
    # if there are entity(s) at spot the player is moving to
    if moving_to_coords in ENTITY_SPRITES_DICT:
        print("found entity(s) where we are moving to")

        # loop over all entities at the location player is moving to
        for entity_obj in ENTITY_SPRITES_DICT[moving_to_coords]:
            print("checking entity %s" % entity_obj["map_tile_name"])

            # if the entity has a before_move behavior function
            if "before_move" in TILES[entity_obj["map_tile_name"]].keys():
                print("calling before_move %s, %s, %s" % (moving_to_coords,PLAYER_LOC,entity_obj))

                # call the before_move behavior function act upon it's result
                if TILES[entity_obj["map_tile_name"]]['before_move'](moving_to_coords,PLAYER_LOC,entity_obj):
                    # all the movement if it returned true
                    can_move = True
                else:
                    # pass and don't allow movement if it returned false
                    pass
            else: # entity does not have a before_move function
                # allow movement
                can_move = True

    else: # no entities at the location player is moving to
        # check if the tile has a before_move behavior function
        if "before_move" in TILES[moving_to_tile_name].keys():
            if TILES[moving_to_tile_name]['before_move'](moving_to_coords,PLAYER_LOC, moving_to_tile_name):
                # allow the movement if it returned true
                can_move = True
            else:
                # break and don't allow movement if it returned false
                pass
        else:
            can_move = True
    # if player is allowed to move
    if can_move:
        print("Player is allowed to move, changing coords")
        # set the player loc variable to the new coords
        PLAYER_LOC = moving_to_coords
    else:
        print("Player is not allowed to move")

def draw_player():
    #print("inside draw player")
    player_screen_x = PLAYER_LOC[0] - CAMERA_OFFSET_X
    player_screen_y = PLAYER_LOC[1] - CAMERA_OFFSET_Y
    #print("setting player loc %s, %s" % (player_screen_x, player_screen_y))
    sprite.x = player_screen_x*16
    sprite.y = player_screen_y*16

# draw the current CAMERA_VIEW dictionary and the ENTITY_SPRITES_DICT
def draw_camera_view():
    # list that will hold all entities that have been drawn based on their MAP location
    # any entities not in this list should get moved off the screen
    drew_entities = []
    #print(CAMERA_VIEW)

    # loop over y tile coordinates
    for y in range(0, SCREEN_HEIGHT_TILES):
        # loop over x tile coordinates
        for x in range(0, SCREEN_WIDTH_TILES):
            # tile name at this location
            tile_name = CAMERA_VIEW[x,y]

            # if tile exists in the main dictionary
            if tile_name in TILES.keys():
                # if there are entity(s) at this location
                if (x + CAMERA_OFFSET_X, y + CAMERA_OFFSET_Y) in ENTITY_SPRITES_DICT:
                    # default background for entities is floor
                    castle[x, y] = TILES["floor"]['sprite_index']

                    # if it's not the player
                    if tile_name != "player":
                        # loop over all entities at this location
                        for entity_obj_at_tile in ENTITY_SPRITES_DICT[x + CAMERA_OFFSET_X, y + CAMERA_OFFSET_Y]:
                            # set appropriate x,y screen coordinates based on tile coordinates
                            ENTITY_SPRITES[int(entity_obj_at_tile["entity_sprite_index"])].x = x * 16
                            ENTITY_SPRITES[int(entity_obj_at_tile["entity_sprite_index"])].y = y * 16

                            # add the index of the entity sprite to the drew_entities list so we know not to hide it later.
                            drew_entities.append(entity_obj_at_tile["entity_sprite_index"])

                else: # no entities at this location
                    # set the sprite index of this tile into the CASTLE dictionary
                    castle[x, y] = TILES[tile_name]['sprite_index']

            else: # tile type not found in main dictionary
                # default to floor tile
                castle[x, y] = TILES["floor"]['sprite_index']

            # if the player is at this x,y tile coordinate accounting for camera offset
            if PLAYER_LOC == ((x + CAMERA_OFFSET_X, y + CAMERA_OFFSET_Y)):
                # set player sprite screen coordinates
                sprite.x = x*16
                sprite.y = y*16

    # loop over all entity sprites
    for index in range(0, len(ENTITY_SPRITES)):
        # if the sprite wasn't drawn then it's outside the camera view
        if index not in drew_entities:
            # hide the sprite by moving it off screen
            ENTITY_SPRITES[index].x = int(-16)
            ENTITY_SPRITES[index].y = int(-16)

# variable to store timestamp of last drawn frame
last_update_time = 0

# variables to store movement offset values
x_offset = 0
y_offset = 0

# main loop
while True:
    # auto dim the screen
    #badger.auto_dim_display(delay=10, check_buttons=True)
    badger.brightness = 0.1

    # set the current button values into variables
    cur_up = badger.button.up
    cur_down = badger.button.down
    cur_right = badger.button.right
    cur_left = badger.button.left

    cur_a = badger.button.a
    cur_b = badger.button.b
    cur_start = badger.button.start
    cur_select = badger.button.select

    # check for up button press / release
    if not cur_start and prev_start:
        text_area.text = "Press B\nto Restart"
        text_area.y = int(128/2 - 30)
        group.append(splash)
        HIDE_SPLASH_TIME = now + 3

    if not cur_b and prev_b:
        if HIDE_SPLASH_TIME > now:
            if text_area.text == "Press B\nto Restart":
                HIDE_SPLASH_TIME = -1
                group.remove(splash)
                load_map(MAP_LIST[CUR_MAP_INDEX])

    # check for up button press / release
    if not cur_up and prev_up:
        if can_player_move(UP):
            x_offset = 0
            y_offset = - 1

    # check for down button press / release
    if not cur_down and prev_down:
        if can_player_move(DOWN):
            x_offset = 0
            y_offset = 1

    # check for right button press / release
    if not cur_right and prev_right:
        if can_player_move(RIGHT):
            x_offset = 1
            y_offset = 0

    # check for left button press / release
    if not cur_left and prev_left:
        if can_player_move(LEFT):
            print("can_move left")
            x_offset = -1
            y_offset = 0

    # if any offset is not zero then we need to process player movement
    if x_offset != 0 or y_offset != 0:
        move_player(x_offset, y_offset)

    # reset movement offset variables
    y_offset = 0
    x_offset = 0

    # set previos button values for next iteration
    prev_up = cur_up
    prev_down = cur_down
    prev_right = cur_right
    prev_left = cur_left

    prev_select = cur_select
    prev_start = cur_start
    prev_a = cur_a
    prev_b = cur_b


    # current time
    now = time.monotonic()

    # if it has been long enough based on FPS delay
    if now > last_update_time + FPS_DELAY:

        #camera_loc = (max(0, PLAYER_LOC[0]-4), max(0, PLAYER_LOC[1]-3))
        #set_camera_view(camera_loc[0], camera_loc[1], 10, 8)

        set_camera_view(
            max(min(PLAYER_LOC[0]-4,MAP_WIDTH-SCREEN_WIDTH_TILES),0),
            max(min(PLAYER_LOC[1]-3,MAP_HEIGHT-SCREEN_HEIGHT_TILES),0),
            10,
            8
        )

        # draw the camera
        draw_camera_view()

        # store the last update time
        last_update_time = now

        if HIDE_SPLASH_TIME != -1:
            if HIDE_SPLASH_TIME < now:
                group.remove(splash)
                HIDE_SPLASH_TIME = -1