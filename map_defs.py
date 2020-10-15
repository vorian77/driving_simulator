maps = []
roads = []
artifacts = []
R = "r"
L = "l"
C = "c"

def load():
    # add_map(1, load_map(map0))
    add_map(2, load_map(map0))
    # add_map(2, load_map(map1))
    #add_map(2, load_map(map2))
    return maps

def map0():
    add_road(3, .75, 96)
    add_artifact("sign_traffic_light", 0, 2, C)
    add_road(0, .75, 96)
    add_artifact("pedestrian", 1, 0, R)
    add_artifact("vehicle", 2, 2, 0)
    add_artifact("sign_stop", 0, 0, R)
    add_road(3, .75, 96)
    add_artifact("destination", 0, 2, C)

def map1():
    add_road(3, .25, 96)
    add_artifact("pedestrian", 1, 0, R)
    add_artifact("sign_stop", 0, 0, R)
    add_road(3, 1, 96)
    add_artifact("pedestrian", 1, 0, L)
    add_artifact("sign_traffic_light", 0, 2, C)
    add_artifact("vehicle", 2, 2, 0)
    add_artifact("destination", 0, 2, C)

def map2():
    add_road(0, 0.25, 96)
    add_artifact("sign_traffic_light", 0, 2, C)
    add_road(2, .4, 96)
    add_artifact("pedestrian", 1, 0, L)
    add_artifact("sign_stop", 0, 0, R)
    add_road(2, .4, 96)
    add_artifact("sign_traffic_light", 0, 2, C)
    add_road(0, .5, 96)
    add_artifact("sign_stop", 0, 0, R)
    add_road(3, .5, 96)
    add_artifact("sign_traffic_light", 0, 2, C)
    add_road(0, .5, 96)
    add_artifact("pedestrian", 1, 0, L)
    add_artifact("sign_traffic_light", 0, 2, C)
    add_road(2, .5, 96)
    add_artifact("sign_stop", 0, 0, R)
    add_road(0, .8, 96)
    add_artifact("pedestrian", 1, 0, R)
    add_artifact("sign_stop", 0, 0, R)
    add_road(3, 2.25, 96)
    add_artifact("pedestrian", 1, 0, L)
    add_artifact("vehicle", 2, 2, 0)
    add_artifact("sign_traffic_light", 0, 2, C)
    add_road(1, .5, 96)
    add_artifact("sign_stop", 0, 0, L)
    add_road(3, .2, 96)
    add_artifact("sign_stop", 0, 0, R)
    add_road(1, 1.9, 96)
    add_artifact("vehicle", 2, 2, 1)
    add_artifact("pedestrian", 1, 0, R)
    add_artifact("sign_stop", 0, 0, R)
    add_road(2, .65, 96)
    add_artifact("vehicle", 2, 2, 0)
    add_artifact("sign_stop", 0, 0, R)
    add_road(0, 1.5, 96)
    add_artifact("pedestrian", 1, 0, L)
    add_artifact("vehicle", 2, 2, 1)
    add_artifact("destination", 0, 2, C)

# utilities
def add_map(lane_count, map_parms):
    maps.append((lane_count, map_parms))

def load_map(f_map):
    global roads
    roads = []
    global artifacts
    artifacts = []
    f_map()
    return roads, artifacts

def add_road(direction, length, speed):
    global roads
    roads.append((direction, length, speed))
    artifacts.append([])

def add_artifact(type, segment, pos_length, pos_width):
    global artifacts
    artifacts[-1].append((type, segment, pos_length, pos_width))
