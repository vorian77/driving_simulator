import math

# conversions
def convert_road(km):
    ROAD_PIXELS_PER_KM = 153
    return round(math.ceil(km * ROAD_PIXELS_PER_KM))

def convert_car(meters):
    CAR_PIXELS_PER_METER = 6.8
    return round(math.ceil(meters * CAR_PIXELS_PER_METER))

def bitwise_complement(value):
    return abs(value - 1)

def numeric_complement(value):
    return 0 - value

def center(width_larger, width_smaller):
    return int((width_larger / 2) - (width_smaller / 2))

def cartesian_distance(p0, p1):
    distance = math.sqrt(((p0[0] - p1[0]) ** 2) + ((p0[1] - p1[1]) ** 2))
    return distance

def heading(start, end):
    # normalize to start at position (0, 0)
    normalized_x = end[0] - start[0]
    normalized_y = end[1] - start[1]

    #https: // stackoverflow.com / questions / 10473930 / how - do - i - find - the - angle - between - 2 - points - in -pygame / 10474341
    radians = math.atan2(-normalized_y, normalized_x)
    radians %= 2 * math.pi
    degrees = round(math.degrees(radians))
    return degrees

def pixels_per_update(speed):
    # conversion from kilometers per hour
    # to distance traveled in 1 update cycle
    return math.ceil(speed / 30)

class Timer():
    def __init__(self, pygame, duration):
        self.pygame = pygame
        self.duration = duration
        self.timer = 1000 * self.duration
        self.cycle_total = 0
        self.counter = 0
        self.clock = self.pygame.time.Clock()

    def set_duration(self, duration):
        self.duration = duration
        self.timer = 1000 * self.duration

    def click(self):
        self.cycle_total += self.clock.get_time()
        rtn = self.cycle_total > self.timer
        if rtn:
            self.cycle_total = 0
            self.counter += 1
        self.clock.tick()
        return rtn