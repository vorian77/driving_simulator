import numpy as np
import math
import rect as rect_lib
import utilities as u

class Obj:
    """parent class for all objects"""

    # colors in RGB
    COLOR_AQUA = (0, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    COLOR_BLUE = (0, 0, 255)
    COLOR_GREEN = (0, 255, 0)
    COLOR_MAROON = (128, 0, 0)
    COLOR_PURPLE = (128, 0, 128)
    COLOR_RED = (255, 0, 0)
    COLOR_TEAL = (0, 128, 128)
    COLOR_WHITE = (255, 255, 255)
    COLOR_YELLOW = (255, 255, 0)
    _ID = 0

    def __init__(self, pygame, screen):
        self.pygame = pygame
        self.screen = screen
        self.id = self.get_id()

    def get_id(self):
        new_id = self.__class__._ID
        self.__class__._ID += 1
        return new_id

    def update(self, *kwargs):
        pass

    def msg(self, text):
        obj_class = self.__class__.__name__
        print(f'{obj_class}: {text}')


class ObjImage(Obj, rect_lib.RectDirection):
    """class for objects that include an image"""

    def __init__(self, pygame, screen, image_file, initial_direction=0):
        Obj.__init__(self, pygame, screen)
        self.initial_direction = initial_direction
        self.heading = None
        self.speed = 0

        self.image_original = None
        self.image = self.load_image(image_file)
        rect_lib.RectDirection.__init__(self, self.image.get_rect(), initial_direction)

    def load_image(self, image_file):
        self.image_original = self.pygame.image.load(image_file)
        self.image_original.convert()
        return self.image_original

    def draw(self):
        self.screen.blit(self.image, self)


class ObjImageMove(ObjImage):
    """class for objects that move"""

    def __init__(self, pygame, screen, image_file, initial_direction=0):
        super().__init__(pygame, screen, image_file, initial_direction)
        self.collision_buffer_parms = None
        self.collision_buffer = None

    def normalize_angle(self, angle):
        # normalize to default 0 degrees/east
        # direction_road clockwise - addition of negative numbers
        # direction_road counter clockwise - addition of positive numbers
        new_angle = angle + (-90, 90, 180, 0)[self.initial_direction]
        return new_angle

    def rotate(self, angle):
        if angle != self.heading:
            self.heading = angle
            self.image = self.image_original
            self.image = self.pygame.transform.rotate(self.image, self.normalize_angle(angle))

    def degree2rad(self, heading):
        return heading * math.pi / 180

    def make_instruction(self, heading, speed):
        return {'heading': heading, 'speed': speed}

    def move_obj(self, instruction):
        def move_obj(heading, speed):
            # set heading
            if heading is None:
                heading = self.heading
            else:
                self.rotate(heading)

            # set speed
            if speed is None:
                speed = self.speed
            else:
                self.speed = speed

            pixels_per_move = u.pixels_per_update(self.speed)
            theta = self.degree2rad(heading)
            center = self.gnav('center')
            x = center[0] + round(pixels_per_move * np.cos(theta))
            y = center[1] + -round(pixels_per_move * np.sin(theta))
            self.snav('center', (x, y))

        def create_collision_buffer(parms):
            buffer_size = 10  # pixels

            def get_buffer_val(self, parms):
                val = self.gnav(parms[0]) if parms[0] != '' else 0
                val += parms[1] * buffer_size
                return val

            ## create_buffer()
            left = get_buffer_val(self, parms[0])
            top = get_buffer_val(self, parms[1])
            width = get_buffer_val(self, parms[2])
            height = get_buffer_val(self, parms[3])
            self.collision_buffer = rect_lib.Rect((left, top, width, height))

        ## move()
        heading = instruction['heading']
        speed = instruction['speed']

        move_obj(heading, speed)
        create_collision_buffer(self.collision_buffer_parms)

    def move_distance(self, p0, p1):
        # returns the number of frames it will take the object
        # at it's current speed to go from point p0 to point p1
        if self.speed == 0:
            return None
        distance = u.cartesian_distance(p0, p1)
        display_speed = u.pixels_per_update(self.speed)
        return distance / display_speed

    def point_in_rect(self, position, rect):
        point = self.gnav(position)
        return rect.collidepoint(point)

    def in_rect(self, rect):
        if self.point_in_rect('midtop', rect):
            return True
        elif self.point_in_rect('midbottom', rect):
            return True
        elif self.point_in_rect('midleft', rect):
            return True
        elif self.point_in_rect('midright', rect):
            return True
        return False

    def set_collision_buffer_parms(self, side):
        if side == 'top':
            self.collision_buffer_parms = (
                (('left', 0), ('top', -1), ('width', 0), ('', 1)),
                (('right', 0), ('top', 0), ('width', 0), ('', 1)),
                (('top', -1), ('right', 0), ('', 1), ('width', 0)),
                (('top', 0), ('left', 0), ('', 1), ('width', 0))
            )[self.direction]
        elif side == 'left':
            self.collision_buffer_parms = (
                (('right', 0), ('top', 0), ('', 1), ('height', 0)),
                (('right', -1), ('bottom', 0), ('', 1), ('height', 0)),
                (('top', 0), ('right', -1), ('height', 0), ('', 1)),
                (('bottom', 0), ('right', 0), ('height', 0), ('', 1))
            )[self.direction]
        elif side == 'right':
            self.collision_buffer_parms = (
                (('left', -1), ('top', 0), ('', 1), ('height', 0)),
                (('left', 0), ('bottom', 0), ('', 1), ('height', 0)),
                (('top', 0), ('left', 0), ('height', 0), ('', 1)),
                (('bottom', 0), ('left', -1), ('height', 0), ('', 1))
            )[self.direction]

    def draw(self):
        super().draw()

    def draw_collision_buffer(self, text):
        self.pygame.draw.rect(self.screen, self.COLOR_YELLOW, self.collision_buffer)
        self.msg(f'{text}...')

    def draw_outline(self, text):
        self.pygame.draw.rect(self.screen, self.COLOR_YELLOW, self, 1)
        self.msg(f'{text}...')

