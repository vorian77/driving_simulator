import numpy as np
import math
import obj as obj_lib

color_red = (255, 0, 0)
color_blue = (0, 0, 255)
color_green = (0, 255, 0)
color_black = (0, 0, 0)

class test():
    def __init__(self, pygame, screen):
        self.pygame = pygame
        self.screen = screen
        self.data = self.setup()

        self.new_obj = obj_lib.Obj(pygame, screen)
        self.new_obj_image = obj_lib.ObjImage(pygame, screen, 'images/vehicle_car_24.png', 0)

    def setup(self):
        data = {}
        return data

    def update(self):
        self.new_obj_image.x += 1
        self.draw()

    def draw(self):
        self.new_obj_image.draw()

