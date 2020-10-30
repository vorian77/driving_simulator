import numpy as np
import math
import utilities as u


class test():
    def __init__(self, pygame, screen):
        self.pygame = pygame
        self.screen = screen
        self.COLOR_GREEN = (0, 255, 0)
        self.COLOR_RED = (255, 0, 0)
        self.COLOR_BLACK = (0, 0, 0)
        self.COLOR_YELLOW = (255, 255, 0)
        self.origin = [300, 300]
        self.drive_guide = self.get_arc_points(self.origin, 100, 0, 2)

    def draw(self):
        self.drive_guide_draw()

    def drive_guide_draw(self):
        for p in self.drive_guide:
            self.pygame.draw.circle(self.screen, self.COLOR_RED, (p[0], p[1]), 1)
        self.pygame.draw.circle(self.screen, self.COLOR_YELLOW, (self.origin[0], self.origin[1]), 1)
        self.pygame.draw.circle(self.screen, self.COLOR_GREEN, (self.drive_guide[0][0], self.drive_guide[0][1]), 1)
        self.pygame.draw.circle(self.screen, self.COLOR_BLACK, (self.drive_guide[-1][0], self.drive_guide[-1][1]), 1)

    def get_arc_points(self, origin, radius, arc_dir_start, arc_dir_end):
        def get_art_parms(arc_dir_start, arc_dir_end):
            parms = {(0, 2): (3, 1), (0, 3): (2, 0),
                    (1, 2): (0, 0), (1, 3): (1, 1),
                    (2, 0): (1, 0), (2, 1): (2, 1),
                    (3, 0): (0, 1), (3, 1): (3, 0)}
            return parms[(arc_dir_start, arc_dir_end)]

        def get_plot_point(origin, radius, theta):
            x = origin[0] + round((radius * np.cos(theta)))
            y = origin[1] + round((radius * np.sin(theta)))
            return x, y

        ## get_arc_points()
        arc_parms = get_art_parms(arc_dir_start, arc_dir_end)
        ip_radians_headings_value_offset = arc_parms[0]
        ip_radians_start_idx = arc_parms[1]
        ip_radians_end_idx = u.bitwise_complement(arc_parms[1])

        pi = math.pi
        points = []
        offset = (pi / 2) * ip_radians_headings_value_offset
        radian_range = (0, pi / 2)
        radian_start = radian_range[ip_radians_start_idx] + offset
        radian_end = radian_range[ip_radians_end_idx] + offset
        thetas = np.linspace(radian_start, radian_end, 18)
        for t in thetas:
            points.append((get_plot_point(origin, radius, t)))
        return points
