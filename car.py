import obj as obj_lib
import math
import numpy as np
import road_artifact
import utilities as u

class ObjCar(obj_lib.ObjImageMove):
    """car class"""

    def __init__(self, pygame, screen, image_file, intial_direction):
        super().__init__(pygame, screen, image_file, intial_direction)
        self.speed_prev = None
        self.sensors = self.init_sensors()

    def init_sensors(self):
        sensors = []
        sensors.append(SensorSimulator(self.pygame, self.screen))
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

    def set_direction(self, direction):
        super().set_direction(direction)
        self.set_collision_buffer_parms('top')

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
        location['lane'] = road.get_lane_obj(self)
        return location


class Sensor(obj_lib.Obj):
    """
    parent object class for car sensors

    returns instruction
        driving instruction - (heading, speed)
        no driving instruction (no new process or process has completed) - None
        arrived at destination - 'arrived'
    """

    def __init__(self, pygame, screen):
        super().__init__(pygame, screen)
        self.classifiers = []
        self.init_classifiers()

    def add_classifier(self, object):
        self.classifiers.append(object(self.pygame, self.screen))

    def init_classifiers(self):
        pass

    def collect(self, status):
        raw_data = self.retrieve(status)
        for c in self.classifiers:
            new_process = c.evaluate(status, raw_data)
            if new_process:
                return new_process
        return None

    def retrieve(self, status):
        pass

    def reset(self):
        for c in self.classifiers:
            c.reset()


class SensorSimulator(Sensor):
    def __init__(self, pygame, screen):
        super().__init__(pygame, screen)

    def init_classifiers(self):
        self.add_classifier(ClassiferSimulatorStationaryDestination)
        self.add_classifier(ClassiferSimulatorStationarySignSpeed15)
        self.add_classifier(ClassiferSimulatorStationarySignSpeed25)
        self.add_classifier(ClassiferSimulatorStationarySignSpeed45)
        self.add_classifier(ClassiferSimulatorStationarySignSpeed55)
        self.add_classifier(ClassiferSimulatorStationarySignSpeed65)
        self.add_classifier(ClassiferSimulatorStationarySignStop)
        self.add_classifier(ClassiferSimulatorStationarySignTrafficLight)
        self.add_classifier(ClassiferSimulatorMoveVehicle)
        self.add_classifier(ClassiferSimulatorMovePedestrian)

    def retrieve(self, status):
        # return artifacts that the car has not passed
        car = status['car']
        road = status['location']['road']
        artifacts = status['location']['road'].artifacts
        car_bottom = car.gnav('midbottom')

        visible_artifacts = []
        for artifact in artifacts:
            artifact_top = artifact.gnav('midtop')
            if road.dir_val_exceeds(artifact_top, car_bottom):
                visible_artifacts.append(artifact)
        return visible_artifacts


class Classifier(obj_lib.Obj):
    """parent object class for sensor classifiers"""

    def __init__(self, pygame, screen, activate_distance):
        super().__init__(pygame, screen)
        self.status = {}
        self.activate_distance = activate_distance
        self.activate_distance_buffer = 0

    def evaluate(self, status, raw_data):
        feature = self.extract(status, raw_data)
        if not feature:
            return None
        if not self.activate(status, feature):
            return None
        return self.get_process(status, feature)

    def extract(self, status, raw_data):
        # if raw_data handled by classifier, then return structured data from raw data
        pass

    def status_is_inactive(self, id):
        # if status for feature with id has not been set, set it to inactive
        # otherwise, return true if feature with id's status is inactive
        if id not in self.status:
            self.status[id] = 'inactive'
            return True
        else:
            return self.status[id] == 'inactive'

    def status_set_active(self, feature):
        # set the status for feature active
        id = feature['id']
        self.status[id] = 'active'

    def status_set_inactive(self, feature):
        # set the status for feature active
        id = feature['id']
        self.status[id] = 'inactive'

    def status_set_complete(self, feature):
        # set the status for feature to complete
        id = feature['id']
        self.status[id] = 'complete'

    def activate(self, status, feature):
        # return true if process for feature should be activated, false otherwise
        pass

    def get_process(self, status, feature):
        self.status_set_active(feature)
        data = self.get_process_data(status, feature)
        return (data, self.process_function)

    def get_process_data(self, status, feature):
        return {'status': status, 'feature': feature}

    def process_function(self, data):
        pass

    def reset(self):
        self.status = {}


class ClassifierSimulator(Classifier):
    def __init__(self, pygame, screen, artifact_class, activate_distance, activate_pos):
        super().__init__(pygame, screen, activate_distance)
        self.activate_distance_buffer = 5  # length of car
        self.artifact_class = artifact_class
        self.activate_pos = activate_pos
        self.status = {}

    def get_artifact_id(self, artifact):
        road_id = artifact.road.id
        artifact_id = artifact.id
        return (road_id, artifact_id)

    def extract(self, status, raw_data):
        for artifact in raw_data:
            if isinstance(artifact, self.artifact_class):
                if self.status_is_inactive(self.get_artifact_id(artifact)):
                    return self.extract_data(status, artifact)
        return None

    def extract_data(self, status, artifact):
        feature = {'artifact': artifact, 'id': self.get_artifact_id(artifact)}

        car = status['car']
        road = status['location']['road']

        # distance - difference between artifact position and bottom of the car
        if self.activate_pos:
            pos_artifact = artifact.gnav(self.activate_pos)
        else:
            # segment position
            location_road = artifact.pos_parms['length_attribute_road']
            pos_artifact = road.gnav(location_road)
        pos_car = car.gnav('top')

        feature['distance'] = (pos_artifact - pos_car) * road.graph_dir_length
        feature['heading'] = u.heading(car.center, artifact.center)

        # same_lane
        # * none - artifact is not in a lane
        # * True - artifact is in the same lane as the car
        # * False - artifact is in a lane, but not the car's lane
        artifact_lane_id = artifact.pos_width
        if type(artifact_lane_id) is int:
            car_lane = road.get_lane_obj(car)
            feature['same_lane'] = artifact_lane_id == car_lane.lane_id
        else:
            feature['same_lane'] = None

        return feature

    def activate(self, status, feature):
        same_lane = feature['same_lane']
        if same_lane is False:
            return False
        return feature['distance'] <= (self.activate_distance + self.activate_distance_buffer)

    def process_complete(self, feature):
        pass

    def in_collision_buffer(self, car, artifact):
        return car.collision_buffer and not car.collision_buffer.is_clear([artifact])


class ClassiferSimulatorStationary(ClassifierSimulator):
    def __init__(self, pygame, screen, artifact_class, activate_distance, activate_pos):
        super().__init__(pygame, screen, artifact_class, activate_distance, activate_pos)

    def process_complete(self, feature):
        self.status_set_complete(feature)

class ClassiferSimulatorStationaryDestination(ClassiferSimulatorStationary):
    def __init__(self, pygame, screen):
        super().__init__(pygame, screen, road_artifact.ObjRoadArtifactStationaryDestination, 0, None)

    def get_process_data(self, status, feature):
        data = super().get_process_data(status, feature)
        wait_time = 3  # seconds
        data['complete'] = self.pygame.time.get_ticks() + (wait_time * 1000)
        return data

    def process_function(self, data):
        car = data['status']['car']
        ticks = self.pygame.time.get_ticks()
        if ticks < data['complete']:
            car.draw_outline('Waiting at destination')
            return car.make_instruction(None, 0)
        else:
            return 'arrived'


class ClassiferSimulatorStationarySignSpeed(ClassiferSimulatorStationary):
    def __init__(self, pygame, screen, artifact_class, activate_distance, activate_pos, speed):
        self.speed = speed
        super().__init__(pygame, screen, artifact_class, activate_distance, activate_pos)

    def process_function(self, data):
        car = data['status']['car']

        if car.speed != self.speed:
            car.draw_outline(f'Setting speed to: {self.speed}')
            car.speed_prev = self.speed  # allow temporary speed changes to be reset
            return car.make_instruction(None, self.speed)
        else:
            feature = data['feature']
            self.process_complete(feature)

class ClassiferSimulatorStationarySignSpeed15(ClassiferSimulatorStationarySignSpeed):
    def __init__(self, pygame, screen):
        super().__init__(pygame, screen, road_artifact.ObjRoadArtifactStationarySignSpeed15, 0, None, 15)


class ClassiferSimulatorStationarySignSpeed25(ClassiferSimulatorStationarySignSpeed):
    def __init__(self, pygame, screen):
        super().__init__(pygame, screen, road_artifact.ObjRoadArtifactStationarySignSpeed25, 0, None, 25)


class ClassiferSimulatorStationarySignSpeed45(ClassiferSimulatorStationarySignSpeed):
    def __init__(self, pygame, screen):
        super().__init__(pygame, screen, road_artifact.ObjRoadArtifactStationarySignSpeed45, 0, None, 45)


class ClassiferSimulatorStationarySignSpeed55(ClassiferSimulatorStationarySignSpeed):
    def __init__(self, pygame, screen):
        super().__init__(pygame, screen, road_artifact.ObjRoadArtifactStationarySignSpeed55, 0, None, 55)


class ClassiferSimulatorStationarySignSpeed65(ClassiferSimulatorStationarySignSpeed):
    def __init__(self, pygame, screen):
        super().__init__(pygame, screen, road_artifact.ObjRoadArtifactStationarySignSpeed65, 0, None, 65)


class ClassiferSimulatorStationarySignStop(ClassiferSimulatorStationary):
    def __init__(self, pygame, screen):
        super().__init__(pygame, screen, road_artifact.ObjRoadArtifactStationarySignStop, 0, None)

    def get_process_data(self, status, feature):
        data = super().get_process_data(status, feature)
        wait_time = 3  # seconds
        data['complete'] = self.pygame.time.get_ticks() + (wait_time * 1000)
        return data

    def process_function(self, data):
        car = data['status']['car']
        ticks = self.pygame.time.get_ticks()
        if ticks < data['complete']:
            car.draw_outline('Waiting at stop sign')
            return car.make_instruction(None, 0)
        else:
            car.restore_speed()
            self.process_complete(data['feature'])


class ClassiferSimulatorStationarySignTrafficLight(ClassiferSimulatorStationary):
    def __init__(self, pygame, screen):
        super().__init__(pygame, screen, road_artifact.ObjRoadArtifactStationarySignTrafficLight, 0, None)

    def process_function(self, data):
        car = data['status']['car']
        feature = data['feature']
        artifact = feature['artifact']
        if artifact.red:
            car.draw_outline('Waiting at red traffic light')
            return car.make_instruction(None, 0)
        else:
            car.restore_speed()
            self.process_complete(feature)


class ClassifierSimulatorMove(ClassifierSimulator):
    def __init__(self, pygame, screen, artifact_class, activate_distance, activate_pos):
        super().__init__(pygame, screen, artifact_class, activate_distance, activate_pos)

    def process_complete(self, feature):
        self.status_set_inactive(feature)

    def status_set_inactive(self, data):
        feature = data['feature']
        return super().status_set_inactive(feature)


class ClassiferSimulatorMoveVehicle(ClassifierSimulatorMove):
    def __init__(self, pygame, screen):
        super().__init__(pygame, screen, road_artifact.ObjRoadArtifactMoveVehicle, 50, 'bottom')

    def get_process_data(self, status, feature):
        data = super().get_process_data(status, feature)

        car = data['status']['car']
        road = data['status']['location']['road']
        artifact = feature['artifact']

        current_lane_id = road.get_lane_obj(car).lane_id

        if road.lane_cnt == 1:
            # only 1 lane - match speed of car
            data['type'] = 'single_lane'
            data['artifact_pos'] = artifact.gnav('bottom')
        else:
            # select adjoining lane
            data['type'] = 'multiple_lane'
            if current_lane_id - 1 >= 0:
                new_lane_id = current_lane_id - 1
            else:
                new_lane_id = current_lane_id + 1
            new_lane = road.lanes[new_lane_id]

            if road.direction == 0:
                left = new_lane.left
                top = max(artifact.gnav('top'), new_lane.gnav('top'))
                width = new_lane.width
                height = car.gnav('top') - top
                data['collision_zone'] = self.pygame.Rect(left, top, width, height)
                data['end_point'] = data['collision_zone'].midtop
            elif road.direction == 1:
                left = new_lane.left
                top = car.gnav('top')
                width = new_lane.width
                height = min(artifact.gnav('top'), new_lane.gnav('top')) - top
                data['collision_zone'] = self.pygame.Rect(left, top, width, height)
                data['end_point'] = data['collision_zone'].midbottom
            elif road.direction == 2:
                left = max(artifact.gnav('top'), new_lane.gnav('top'))
                top = new_lane.top
                width = car.gnav('top') - left
                height = new_lane.height
                data['collision_zone'] = self.pygame.Rect(left, top, width, height)
                data['end_point'] = data['collision_zone'].midleft
            elif road.direction == 3:
                left = car.gnav('top')
                top = new_lane.top
                width = artifact.gnav('bottom') - left
                height = new_lane.height
                data['collision_zone'] = self.pygame.Rect(left, top, width, height)
                data['end_point'] = data['collision_zone'].midright
        return data

    def process_function(self, data):
        def is_clear(road, collision_zone):
            moving_objects = [artifact for artifact in road.artifacts if isinstance(artifact, obj_lib.ObjImageMove)]
            return collision_zone.collidelist(moving_objects) == -1

        def change_lane(data):
            car = data['status']['car']
            road = data['status']['location']['road']

            collision_zone = data['collision_zone']
            car_location = car.gnav('center')
            end_point = data['end_point']

            self.pygame.draw.rect(car.screen, car.COLOR_YELLOW, collision_zone)

            # changed collision zone to drive guide
            drive_guide = u.get_drive_guide(road, car.gnav('center'), end_point, 3)
            road.draw_drive_guide(car, 'center', drive_guide)

            if is_clear(road, collision_zone):
                # draw end point
                self.pygame.draw.circle(road.screen, road.COLOR_RED, end_point, 2)


                if road.dir_val_exceeds(end_point, car_location):
                    # continue lane change
                    heading = u.heading(car_location, end_point)
                    car.draw_heading(heading)
                    self.msg(f'Changing lane to avoid vehicle...')
                    return car.make_instruction(heading, car.speed_prev)
                else:
                    return self.status_set_inactive(data)
            else:
                self.msg(f'Waiting for adjacent lane to clear...')
                return car.make_instruction(None, 0)

        def slow_down(data):
            car = data['status']['car']
            feature = data['feature']
            artifact = feature['artifact']

            distance = abs(artifact.gnav('bottom') - car.gnav('top'))
            if self.activate_distance > distance:
                pos_prev = data['artifact_pos']
                pos_current = artifact.gnav('bottom')
                speed = (pos_current - pos_prev)  # speed is distance per clock cycle
                data['artifact_pos'] = pos_current
                car.draw_collision_buffer('Reducing speed for slow vehicle')
                return car.make_instruction(artifact.heading, speed)
            else:
                return self.status_set_inactive(data)

        ## process_function()
        if data['type'] == 'single_lane':
            return slow_down(data)
        else:
            return change_lane(data)


class ClassiferSimulatorMovePedestrian(ClassifierSimulatorMove):
    def __init__(self, pygame, screen):
        super().__init__(pygame, screen, road_artifact.ObjRoadArtifactMovePedestrian, 18, 'bottom')

    def activate(self, status, feature):
        if not super().activate(status, feature):
            return False
        pedestrian = feature['artifact']
        car = status['car']
        return self.in_collision_buffer(car, pedestrian)

    def process_function(self, data):
        car = data['status']['car']
        pedestrian = data['feature']['artifact']
        if self.in_collision_buffer(car, pedestrian):
            car.draw_collision_buffer('Waiting for pedestrian')
            return car.make_instruction(None, 0)
        else:
            car.restore_speed()
            return super().status_set_inactive(data)
