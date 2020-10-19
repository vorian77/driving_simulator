import obj
import road as road_lib

class ObjMap(obj.Obj):
    """rect.py map"""

    def __init__(self, pygame, screen, car, map_parms):
        super().__init__(pygame, screen)
        self.car = car
        self.lane_cnt = map_parms[0]
        self.car_start_lane = map_parms[1]
        self.speed_intersection = 20  # km per hour
        self.roads = self.init_roads(map_parms[2])
        self.init_car()

    def init_roads(self, map_parms):
        roads_def = map_parms[0]
        artifacts_def = map_parms[1]
        roads = []
        road_prev = None
        for rd, ad in zip(roads_def, artifacts_def):
            direction = rd[0]
            length = rd[1]

            # intersection
            if len(roads) > 0:
                road_prev = roads[-1]
                pr_dir = road_prev.direction
                if pr_dir == direction:
                    roads.append(road_lib.RoadStraightIntersection(self.pygame, self.screen, road_prev))
                else:
                    roads.append(road_lib.RoadIntersectionTurn(self.pygame, self.screen, road_prev, self.speed_intersection, direction, self.lane_cnt))
                road_prev = roads[-1]

            # primary rect.py
            roads.append(road_lib.RoadStraightPrimary(self.pygame, self.screen, road_prev, self.lane_cnt, length, direction, ad))
        return roads

    def init_car(self):
        # init car
        road = self.get_road_first()
        self.car.rotate(road.get_angle_current())
        road.lanes[self.car_start_lane].pos_obj('midbottom', self.car, 'midbottom')

    def update(self):
        for road in self.roads:
            road.update(self.car)

    def draw(self):
        for road in self.roads:
            road.draw()

    def get_road_first(self):
        if len(self.roads) == 0:
            return None
        else:
            return self.roads[0]

    def get_road_obj(self, obj):
        for road in reversed(self.roads):
            if obj.in_rect(road):
                return road
        return None
