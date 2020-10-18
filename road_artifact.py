import obj as obj_lib
import utilities as u


class ObjRoadArtifact():
    """rect.py artifact"""
    # icons: www.flaticon.com

    def __init__(self, road, artifact_def):
        self.road = road
        self.type = artifact_def[0]
        self.segment = artifact_def[1]
        self.pos_length = artifact_def[2]
        self.pos_width = artifact_def[3]
        self.pos_parms = self.init_pos_parms()
        self.init_pos(self)

    def init_pos_parms(self):
        """
        position artifact on road
        example artifact_def: "sign_stop", 0, 0, "r", 0)
        artifact_def parms
            * artifact_type: examples: destination, sign, pedestrian
            * segment - area within road where the artifact will be placed
                0 - end of road
                1 - center of road
                2 - beginning of road
            * pos_length
                0 - just before the end of the segment
                1 - center of segment
                2 - just after the top of segment
            * pos_width
                # - lane_id number beginning at 0 for right lane_id
                l - just left of the road
                c - center of the road
                r - just right of the road
        """

        ## init_pos_parms()
        parms = {}

        # length axis
        parms['length_attribute_road'] = ('top', 'cl', 'bottom')[self.segment]
        parms['length_attribute_artifact'] = ('top', 'cl', 'bottom')[self.pos_length]

        # width axis
        if type(self.pos_width) is int:
            parms['width_road_rect'] = self.road.lanes[self.pos_width]
            parms['width_attribute_road'] = 'cw'
            parms['width_attribute_artifact'] = 'cw'
        else:
            parms['width_road_rect'] = self.road
            pos_parms = {'l': ('left', 'right'),
                         'c': ('cw', 'cw'),
                         'r': ('right', 'left')}[self.pos_width]
            parms['width_attribute_road'] = pos_parms[0]
            parms['width_attribute_artifact'] = pos_parms[1]
        return parms

    def init_pos(self, obj):
        self.road.pos_obj(self.pos_parms['length_attribute_road'], obj, self.pos_parms['length_attribute_artifact'])
        self.pos_parms['width_road_rect'].pos_obj(self.pos_parms['width_attribute_road'], obj, self.pos_parms['width_attribute_artifact'])


class ObjRoadArtifactStationary(obj_lib.ObjImage, ObjRoadArtifact):
    def __init__(self, pygame, screen, road, image_file, artifact_def):
        obj_lib.ObjImage.__init__(self, pygame, screen, image_file)
        ObjRoadArtifact.__init__(self, road, artifact_def)

    def update(self, car):
        self.init_pos(self)


class ObjRoadArtifactStationaryDestination(ObjRoadArtifactStationary):
    def __init__(self, pygame, screen, road, artifact_def):
        image_file = 'images/sign_destination_32.png'
        super().__init__(pygame, screen, road, image_file, artifact_def)


class ObjRoadArtifactStationarySignSpeed(ObjRoadArtifactStationary):
    def __init__(self, pygame, screen, road, artifact_def, image_file, speed):
        super().__init__(pygame, screen, road, image_file, artifact_def)
        self.speed = speed


class ObjRoadArtifactStationarySignSpeed15(ObjRoadArtifactStationarySignSpeed):
    def __init__(self, pygame, screen, road, artifact_def):
        image_file = 'images/sign_speed_15.png'
        super().__init__(pygame, screen, road, artifact_def, image_file, 15)


class ObjRoadArtifactStationarySignSpeed25(ObjRoadArtifactStationarySignSpeed):
    def __init__(self, pygame, screen, road, artifact_def):
        image_file = 'images/sign_speed_25.png'
        super().__init__(pygame, screen, road, artifact_def, image_file, 25)


class ObjRoadArtifactStationarySignSpeed45(ObjRoadArtifactStationarySignSpeed):
    def __init__(self, pygame, screen, road, artifact_def):
        image_file = 'images/sign_speed_45.png'
        super().__init__(pygame, screen, road, artifact_def, image_file, 45)


class ObjRoadArtifactStationarySignSpeed55(ObjRoadArtifactStationarySignSpeed):
    def __init__(self, pygame, screen, road, artifact_def):
        image_file = 'images/sign_speed_55.png'
        super().__init__(pygame, screen, road, artifact_def, image_file, 55)


class ObjRoadArtifactStationarySignSpeed65(ObjRoadArtifactStationarySignSpeed):
    def __init__(self, pygame, screen, road, artifact_def):
        image_file = 'images/sign_speed_65.png'
        super().__init__(pygame, screen, road, artifact_def, image_file, 65)


class ObjRoadArtifactStationarySignStop(ObjRoadArtifactStationary):
    def __init__(self, pygame, screen, road, artifact_def):
        image_file = 'images/sign_stop_24.png'
        super().__init__(pygame, screen, road, image_file, artifact_def)


class ObjRoadArtifactStationarySignTrafficLight(ObjRoadArtifactStationary):
    def __init__(self, pygame, screen, road, artifact_def):
        self.image_files = ['images/sign_traffic_light_green_32.png', 'images/sign_traffic_light_red_32.png']
        super().__init__(pygame, screen, road, self.image_files[0], artifact_def)
        self.red = True
        self.timer = u.Timer(pygame, 3)
        self.image = self.load_image(self.image_files[self.red])

    def draw(self):
        super().draw()

        if self.timer.click():
            self.red = not self.red
            self.image = self.load_image(self.image_files[self.red])


class ObjRoadArtifactMove(obj_lib.ObjImageMove, ObjRoadArtifact):
    def __init__(self, pygame, screen, road, image_file, artifact_def):
        obj_lib.ObjImageMove.__init__(self, pygame, screen, image_file)
        ObjRoadArtifact.__init__(self, road, artifact_def)
        self.speed = 1
        self.lane = None
        self.heading_move = None

    def restart(self):
        pass

    def cycle_complete(self, car):
        pass

    def path_is_clear(self, car):
        objs = [artifact for artifact in self.road.artifacts if isinstance(artifact, obj_lib.ObjImageMove)]
        objs.append(car)
        return not self.collision_buffer or self.collision_buffer.is_clear(objs)

    def start_is_clear(self, car):
        collision_buffer = self.copy()
        self.init_pos(collision_buffer)

        objs = [car]
        for artifact in self.road.artifacts:
            if artifact is not self and isinstance(artifact, obj_lib.ObjImageMove):
                objs.append(artifact)

        return collision_buffer.is_clear(objs)

    def update(self, car):
        if self.cycle_complete(car):
            if self.start_is_clear(car):
                self.restart()
            else:
                self.draw_collision_buffer('Waiting for road to clear - start area.')
        else:
            if self.path_is_clear(car):
                instruction = self.make_instruction(self.heading_move, self.speed)
                self.move_obj(instruction)
            else:
                self.draw_collision_buffer('Waiting for road to clear')


class ObjRoadArtifactMoveVertical(ObjRoadArtifactMove):
    def __init__(self, pygame, screen, road, image_file, artifact_def):
        super().__init__(pygame, screen, road, image_file, artifact_def)
        self.heading_move = self.get_angle_current()
        self.rotate(self.heading_move)

    def set_direction(self, direction):
        super().set_direction(direction)
        self.set_collision_buffer_parms('top')

    def restart(self):
        self.init_pos(self)

    def cycle_complete(self, car):
        # check: car has driven through the road
        artifact_pt = self.gnav('midbottom')
        lane = self.pos_parms['width_road_rect']
        lane_pt = lane.gnav('midtop')
        return lane.dir_val_exceeds(artifact_pt, lane_pt)


class ObjRoadArtifactMoveHorizontal(ObjRoadArtifactMove):
    def __init__(self, pygame, screen, road, image_file, artifact_def):
        super().__init__(pygame, screen, road, image_file, artifact_def)
        self.move_dir_factor = None
        self.f_boundary = None
        self.boundary_width_axis_val = None
        self.boundary_pos_artifact = None
        self.start_pos = self.pos_parms['width_attribute_road']
        self.init_move_parms()

    def init_move_parms(self):
        boundary_buffer = 3

        parms = (
            {'left': ('right', 'left', 3, 1), 'right': ('left', 'right', 2, -1)},
            {'left': ('right', 'right', 2, -1), 'right': ('left', 'left', 3, 1)},
            {'left': ('right', 'bottom', 0, -1), 'right': ('left', 'top', 1, 1)},
            {'left': ('right', 'top', 1, 1), 'right': ('left', 'bottom', 0, -1)}
        )[self.road.direction][self.start_pos]

        boundary_pos_road = parms[0]
        self.boundary_pos_artifact = parms[1]
        move_dir = parms[2]
        self.move_dir_factor = parms[3]

        self.heading_move = self.get_angle(move_dir)
        self.set_collision_buffer_parms(('left', 'right')[self.start_pos != 'left'])
        self.f_boundary = self.get_dir_val_function(move_dir)
        self.boundary_width_axis_val = self.road.gnav(boundary_pos_road) + (boundary_buffer * self.move_dir_factor)

    def restart(self):
        self.start_pos = 'right' if self.start_pos == 'left' else 'left'
        self.init_move_parms()

    def cycle_complete(self, car):
        def get_point(width_val):
            point = [0, 0]
            point[self.road.axis_idx_width] = width_val
            point[self.road.axis_idx_length] = self.gnav('cl')
            return point

        ## cycle_complete()
        artifact_width_axis_val = getattr(self, self.boundary_pos_artifact) # image/rect not rotated road orientation
        return self.f_boundary(get_point(artifact_width_axis_val), get_point(self.boundary_width_axis_val))


class ObjRoadArtifactMovePedestrian(ObjRoadArtifactMoveHorizontal):
    def __init__(self, pygame, screen, road, artifact_def):
        image_file = 'images/person_24.png'
        super().__init__(pygame, screen, road, image_file, artifact_def)

    def path_is_clear(self, car):
        if super().path_is_clear(car):
            return True

        # path is not clear: if car is waiting for ped,
        # allow ped to continue
        if car in self.collision_buffer.contains([car]):
            return car.speed == 0
        else:
            return False

class ObjRoadArtifactMoveVehicle(ObjRoadArtifactMoveVertical):
    def __init__(self, pygame, screen, road, artifact_def):
        image_file = 'images/vehicle_car_black_32.png'
        super().__init__(pygame, screen, road, image_file, artifact_def)


CLASSES = {
    "destination": ObjRoadArtifactStationaryDestination,
    "sign_speed_15": ObjRoadArtifactStationarySignSpeed15,
    "sign_speed_25": ObjRoadArtifactStationarySignSpeed25,
    "sign_speed_45": ObjRoadArtifactStationarySignSpeed45,
    "sign_speed_55": ObjRoadArtifactStationarySignSpeed55,
    "sign_speed_65": ObjRoadArtifactStationarySignSpeed65,
    "sign_stop": ObjRoadArtifactStationarySignStop,
    "sign_traffic_light": ObjRoadArtifactStationarySignTrafficLight,
    "pedestrian": ObjRoadArtifactMovePedestrian,
    "vehicle": ObjRoadArtifactMoveVehicle}
