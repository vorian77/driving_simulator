import math
import numpy as np
import obj as obj_lib
import sensor as sensor_lib


class ObjCar(obj_lib.ObjImageMove):
    """car class"""

    def __init__(self, pygame, screen, image_file, intial_direction):
        super().__init__(pygame, screen, image_file, intial_direction)
        self.speed_prev = None
        self.sensors = self.init_sensors()

    def init_sensors(self):
        sensors = []
        sensors.append(sensor_lib.SensorSimulator(self.pygame, self.screen))
        return sensors

    def draw_heading(self, heading):
        def degree2rad(heading):
            return heading * math.pi / 180

        ## draw_heading()
        length = 75
        start_point = self.gnav('center')
        theta = degree2rad(heading)
        end_x = start_point[0] + round(length * np.cos(theta))
        end_y = start_point[1] + -round(length * np.sin(theta))
        self.pygame.draw.lines(self.screen, (0, 255, 0), False, [start_point, (end_x, end_y)], 1)

    def update(self, map):
        status = self.get_status(map)
        for sensor in self.sensors:
            new_process = sensor.collect(status)
            if new_process:
                return new_process
        return None

    def restore_speed(self):
        self.speed = self.speed_prev

    def reset(self):
        for sensor in self.sensors:
            sensor.reset()

    def get_status(self, map):
        # ping onboard systems for current status of car
        # status could be acquired from Inertial Measurement Unit (IMU), GPS receiver, spedometer, etc..
        status = {}
        status['car'] = self
        status['map'] = map
        status['location'] = self.get_status_location(status)
        return status

    def get_status_location(self, status):
        location = {}
        road = status['map'].get_road_obj(status['car'])
        location['road'] = road
        location['lane'] = road.get_lane(self)
        return location
