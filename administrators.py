import math
import obj
import road as road_lib
import road_artifact as ra_lib
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

    def get_closest_point(self, origin, drive_guide, f_dir_val):
        min_distance = math.inf
        min_point_idx = None
        offset = 1
        for idx, point in enumerate(drive_guide):
            if origin != point:
                if f_dir_val(point, origin):
                    d_car_to_point = u.cartesian_distance(origin, point)
                    if d_car_to_point < min_distance:
                        min_distance = d_car_to_point
                        min_point_idx = idx
        if min_point_idx is None:
            return None
        if min_point_idx + offset < len(drive_guide):
            min_point = drive_guide[min_point_idx + offset]
        else:
            min_point = drive_guide[min_point_idx]
        return min_point

    def get_car_heading(self, car, drive_guide, f_dir_val):
        car_center = car.gnav('center')
        close_pt = self.get_closest_point(car_center, drive_guide, f_dir_val)
        heading = None if close_pt is None else u.heading(car_center, close_pt)
        return heading

    def setup_drive_straight(self, data):
        road = data['road']
        car = data['car']
        car.set_direction(road.direction)
        data['dir_val_function'] = road.dir_val_exceeds
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

        if car.point_in_rect('midtop', road):
            drive_guide = road.get_lane_obj(car).drive_guide
            road.draw_drive_guide(car, drive_guide, f_dir_val)

            target_heading = self.get_car_heading(car, drive_guide, f_dir_val)

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

        car_center = car.gnav('center')
        end_of_turn = drive_guide[-1]

        if f_dir_val(end_of_turn, car_center):
            # continue turning until car has completed turn
            road.draw_drive_guide(car, drive_guide, f_dir_val)
            target_heading = self.get_car_heading(car, drive_guide, f_dir_val)

            if target_heading is None:
                target_heading = car.heading

            car.draw_heading(target_heading)

            return car.make_instruction(target_heading, road.speed)
        else:
            car.restore_speed()
            return None
