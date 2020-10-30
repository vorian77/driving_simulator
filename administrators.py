import obj
import road as road_lib
import drive as drive_lib


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
        self.data = {'car': self.car, 'road': None, 'drive': None}

    def update(self):
        road = self.map.get_road_obj(self.car)
        if road:
            self.data['road'] = road
            if isinstance(road, road_lib.RoadStraight):
                self.data = self.setup_drive_straight(self.data)
            elif isinstance(road, road_lib.RoadIntersectionTurn):
                self.data = self.setup_drive_turn(self.data)
            return (self.data, self.process_drive)
        return None

    def setup_drive_straight(self, data):
        car = data['car']
        road = data['road']
        lane = road.get_lane(car)
        lane_id = lane.lane_id
        car.set_direction(road.direction)
        car.set_collision_buffer_parms('top-lane', lane)
        data['drive'] = drive_lib.DriveStraight(self.pygame, self.screen, road, lane_id)
        return data

    def setup_drive_turn(self, data):
        car = data['car']
        road = data['road']
        lane_id = road.get_lane_id(car)
        car.set_direction(road.direction)
        car.set_collision_buffer_parms('top-front')
        data['drive'] = drive_lib.DriveArcTurn(self.pygame, self.screen, road, lane_id)
        return data

    def process_drive(self, data):
        car = data['car']
        drive = data['drive']
        target_heading = drive.get_heading(car)
        return None if target_heading is None else car.make_instruction(target_heading, None)