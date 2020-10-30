import math
import numpy as np
import obj as obj_lib
import utilities as u


class Drive(obj_lib.Obj):
    def __init__(self, pygame, screen):
        obj_lib.Obj.__init__(self, pygame, screen)
        self.road = None
        self.drive_guide = None
        self.car_refn_location = None

    def drive_guide_init(self, *args):
        pass

    def drive_guide_draw(self, car):
        car_refn_point = car.gnav('center')
        f_dir_val = self.road.dir_val_exceeds
        for p in self.drive_guide:
            if f_dir_val(p, car_refn_point):
                self.pygame.draw.circle(self.screen, self.COLOR_RED, (p[0], p[1]), 0)

    def drive_guide_heading(self, car):
        pass

    def get_heading(self, car):
        if self.get_heading_complete(car):
            return None
        else:
            self.drive_guide_draw(car)
            target_heading = self.get_heading_value(car)
            if target_heading != car.heading:
                car.draw_heading(target_heading)
            return target_heading

    def get_heading_complete(self, car):
        pass

    def get_heading_value(self, car):
        pass

    def get_heading_closest_point(self, refn_point, speed):
        min_distance = math.inf
        min_point_idx = None
        move_distance = u.pixels_per_update(speed)
        f_dir_val = self.road.dir_val_exceeds
        for idx, point in enumerate(self.drive_guide):
            if f_dir_val(point, refn_point):
                d_car_to_point = u.cartesian_distance(refn_point, point)
                if d_car_to_point > move_distance:
                    if d_car_to_point < min_distance:
                        min_distance = d_car_to_point
                        min_point_idx = idx
        return self.drive_guide[min_point_idx] if min_point_idx else None


class DriveStraight(Drive):
    def __init__(self, pygame, screen, *args):
        Drive.__init__(self, pygame, screen)
        self.car_refn_location = 'midtop'
        self.drive_guide = self.drive_guide_init(*args)

    def drive_guide_init(self, *args):
        # creates straight drive guide for road,
        # given start and end points, and gap between points
        self.road = args[0]
        lane_id = args[1]
        self.lane = self.road.lanes[lane_id]
        start_point = self.lane.gnav('midbottom')
        end_point = self.lane.gnav('midtop')

        points = []
        length_gap = 3 * self.road.graph_dir_length
        point_cnt = int((end_point[self.road.axis_idx_length] - start_point[self.road.axis_idx_length]) / length_gap)
        if point_cnt == 0:
            return points

        width_diff = end_point[self.road.axis_idx_width] - start_point[self.road.axis_idx_width]
        width_gap = width_diff / point_cnt

        for point in range(point_cnt):
            c = [0, 0]
            c[self.road.axis_idx_length] = int(start_point[self.road.axis_idx_length] + (point * length_gap))
            c[self.road.axis_idx_width] = int(start_point[self.road.axis_idx_width] + (point * width_gap))
            points.append(c)
        return points

    def get_heading_complete(self, car):
        return not car.point_in_rect(self.car_refn_location, self.lane)

    def get_heading_value(self, car):
        # determine max_heading_range
        speed_min = 15
        speed_max = 65
        angle_min = 4
        angle_max = 7
        max_heading_change = int(angle_min + ((car.speed - speed_min) / (speed_max - speed_min) * (angle_max - angle_min)))  # degrees

        car_refn_point = car.gnav(self.car_refn_location)
        closest_pt = self.get_heading_closest_point(car_refn_point, car.speed)
        if not closest_pt:
            return car.heading

        # normalize car heading
        car_heading = car.heading if car.heading > 0 else (360 - abs(car.heading))
        car_heading = car_heading % 360

        heading_to_closest_pt = u.heading(car_refn_point, closest_pt)
        car_width_val = car.gnav('cw')
        lane_width_val = closest_pt[car.axis_idx_width]

        if car_heading == heading_to_closest_pt and car_width_val == lane_width_val:
            heading = car_heading
        else:
            heading_change = heading_to_closest_pt - car_heading
            if heading_change > 180:
                heading_change = heading_change - 360
            elif heading_change < -180:
                heading_change = heading_change + 360
            if heading_change > 0:
                if heading_change > max_heading_change:
                    heading_change = max_heading_change
            else:
                if heading_change < -max_heading_change:
                    heading_change = -max_heading_change
            heading = car_heading + heading_change
        return heading


class DriveArc(Drive):
    def __init__(self, pygame, screen, *args):
        Drive.__init__(self, pygame, screen)
        self.car_refn_location = 'center'
        self.drive_guide = self.drive_guide_init(*args)

    def get_heading_complete(self, car):
        f_dir_val = self.road.dir_val_exceeds
        end_of_turn = self.drive_guide[-1]
        return not f_dir_val(end_of_turn, car.gnav(self.car_refn_location))

    def get_heading_value(self, car):
        car_refn_point = car.gnav(self.car_refn_location)
        closest_pt = self.get_heading_closest_point(car_refn_point, car.speed)
        return car.heading if not closest_pt else u.heading(car_refn_point, closest_pt)

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


class DriveArcTurn(DriveArc):
    def __init__(self, pygame, screen, *args):
        DriveArc.__init__(self, pygame, screen, *args)

    def drive_guide_init(self, *args):
        self.road = args[0]
        lane_id = args[1]
        road_prev = self.road.road_prev

        def get_origin_attribute(arc_dir_start, arc_dir_end):
            attributes = {(0, 2): 'topleft', (0, 3): 'topright',
                          (1, 2): 'topright', (1, 3): 'topleft',
                          (2, 0): 'topright', (2, 1): 'topleft',
                          (3, 0): 'topleft', (3, 1): 'topright'}
            return attributes[(arc_dir_start, arc_dir_end)]

        ## drive_guide_init()

        # get arc directions
        arc_dir_start = road_prev.direction
        arc_dir_end = self.road.direction

        # get origin
        origin_attribute = get_origin_attribute(arc_dir_start, arc_dir_end)
        origin = road_prev.gnav(origin_attribute)

        # get radius
        width_axis_idx = road_prev.axis_idx_width
        lane_center = self.road.lanes[lane_id].gnav('midtop')
        radius = abs(origin[width_axis_idx] - lane_center[width_axis_idx])

        # return arc points
        return self.get_arc_points(origin, radius, arc_dir_start, arc_dir_end)


class DriveArcChangeLane(DriveArc):
    def __init__(self, pygame, screen, *args):
        DriveArc.__init__(self, pygame, screen, *args)

    def drive_guide_init(self, *args):
        def create_origin(start, radius, width_axis_multiple, length_axis_multiple):
            origin = [0, 0]
            origin[self.road.axis_idx_width] = \
                start[self.road.axis_idx_width] + \
                (radius * width_axis_multiple)
            origin[self.road.axis_idx_length] = \
                start[self.road.axis_idx_length] + \
                (radius * self.road.graph_dir_length * length_axis_multiple)
            return origin

        car = args[0]
        self.road = args[1]
        lane_id_current = args[2]
        lane_id_new = args[3]

        start = car.gnav(self.car_refn_location)
        dir_road = self.road.direction
        lane_current = self.road.lanes[lane_id_current]
        moving_left = lane_id_new > lane_id_current

        # get radius
        radius = abs(lane_current.gnav('cw') - lane_current.gnav('left'))

        # get width parms
        width_parms = {(0, True): (-1, 2), (0, False): (1, 3),
                       (1, True): (1, 3), (1, False): (-1, 2),
                       (2, True): (1, 1), (2, False): (-1, 0),
                       (3, True): (-1, 0), (3, False): (1, 1)}
        parms = width_parms[(dir_road, moving_left)]
        width_dir_origin = parms[0]
        width_dir_guide = parms[1]

        # first arc
        origin = create_origin(start, radius, width_dir_origin, 1)
        points = self.get_arc_points(origin, radius, dir_road, width_dir_guide)

        # second arc
        origin = create_origin(start, radius, width_dir_origin, 3)
        points.extend(self.get_arc_points(origin, radius, width_dir_guide, dir_road))

        return points
