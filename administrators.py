import math
import obj
import road as road_lib
import utilities as u

class ObjAdmin(obj.Obj):
    """administrator"""
    def __init__(self, pygame, screen, map):
        super().__init__(pygame, screen)
        self.map = map
        self.car = map.car

    def get_next_instruction(self):
        pass


class VehicleManagementSystem(ObjAdmin):
    """parent object class for test track objects"""

    def __init__(self, pygame, screen, map):
        super().__init__(pygame, screen, map)
        self.rp = RoutePlanner(self.pygame, self.screen, map)
        self.processes = []

    def add_process(self, process):
        if process:
            self.processes.append(process)

    def update(self):
        self.add_process(self.car.update(self.map))

        if len(self.processes) > 0:
            process = self.processes.pop()
            process_data = process[0]
            process_function = process[1]
            instruction = process_function(process_data)
            if instruction == 'arrived':
                return instruction
            elif instruction:
                self.car.move_obj(instruction)
                self.add_process(process)
            else:
                self.msg(f'dropping process: {process[1]}')
            return

        return self.add_process(self.rp.update())


class RoutePlanner(ObjAdmin):
    def __init__(self, pygame, screen, map):
        super().__init__(pygame, screen, map)
        self.drive_plan_color = (255, 0, 0)

    def update(self):
        road = self.map.get_road_obj(self.car)
        if road:
            data = {'car': self.car, 'road': road}

            if isinstance(road, road_lib.RoadStraight):
                data = self.setup_drive_straight(data)
                return (data, self.process_drive_straight)
            elif isinstance(road, road_lib.RoadIntersectionTurn):
                data = self.setup_drive_turn(data)
                return (data, self.process_drive_turn)
        return None

    def get_closest_point(self, refn_point, speed, drive_guide, f_dir_val):
        min_distance = math.inf
        min_point_idx = None
        move_distance = u.pixels_per_update(speed)
        for idx, point in enumerate(drive_guide):
            if f_dir_val(point, refn_point):
                d_car_to_point = u.cartesian_distance(refn_point, point)
                if d_car_to_point > move_distance:
                    if d_car_to_point < min_distance:
                        min_distance = d_car_to_point
                        min_point_idx = idx
        return drive_guide[min_point_idx] if min_point_idx else None

    def get_car_heading_turn(self, car, car_refn_location, drive_guide, f_dir_val):
        car_refn_point = car.gnav(car_refn_location)
        closest_pt = self.get_closest_point(car_refn_point, car.speed, drive_guide, f_dir_val)
        return car.heading if not closest_pt else u.heading(car_refn_point, closest_pt)

    def get_car_heading_straight(self, car, car_refn_location, drive_guide, f_dir_val):
        max_heading_change = 4  # degrees

        car_refn_point = car.gnav(car_refn_location)
        closest_pt = self.get_closest_point(car_refn_point, car.speed, drive_guide, f_dir_val)
        if not closest_pt:
            return car.heading

        # normalize car heading
        car_heading = car.heading if car.heading > 0 else (360 - abs(car.heading))
        car_heading = car_heading % 360

        heading_to_closest_pt = u.heading(car_refn_point, closest_pt)
        if car_heading == heading_to_closest_pt:
            heading = car_heading
        else:
            heading_change = abs(heading_to_closest_pt - car_heading)
            if heading_change > max_heading_change:
                heading_change = max_heading_change

            if heading_to_closest_pt - car_heading > 0:
                heading = car_heading + heading_change
            else:
                heading = car_heading - heading_change
        return heading

    def setup_drive_straight(self, data):
        road = data['road']
        car = data['car']
        car.set_direction(road.direction)
        data['dir_val_function'] = road.dir_val_exceeds
        data['drive_guide'] = road.get_lane_obj(car).drive_guide
        return data

    def setup_drive_turn(self, data):
        road = data['road']
        car = data['car']
        car.set_direction(road.direction)
        data['dir_val_function'] = road.dir_val_exceeds
        data['drive_guide'] = road.drive_guides[road.get_lane_obj(car).lane_id]
        return data

    def process_drive_straight(self, data):
        car = data['car']
        road = data['road']
        f_dir_val = data['dir_val_function']
        drive_guide = data['drive_guide']
        car_refn_location = 'midtop'

        if car.point_in_rect(car_refn_location, road):
            road.draw_drive_guide(car, car_refn_location, drive_guide, f_dir_val)
            target_heading = self.get_car_heading_straight(car, car_refn_location, drive_guide, f_dir_val)
            if target_heading != road.get_angle_current():
                car.draw_heading(target_heading)
            return car.make_instruction(target_heading, None)
        else:
            return None

    def process_drive_turn(self, data):
        road = data['road']
        car = data['car']
        drive_guide = data['drive_guide']
        f_dir_val = data['dir_val_function']

        car_refn_location = 'center'
        end_of_turn = drive_guide[-1]

        if f_dir_val(end_of_turn, car.gnav(car_refn_location)):
            road.draw_drive_guide(car, car_refn_location, drive_guide, f_dir_val)
            target_heading = self.get_car_heading_turn(car, car_refn_location, drive_guide, f_dir_val)
            car.draw_heading(target_heading)
            return car.make_instruction(target_heading, None)
        else:
            return None
