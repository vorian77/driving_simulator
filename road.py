import math
import numpy as np
import obj as obj_lib
import rect as rect_lib
import road_artifact as ra
import utilities as u

class Road(obj_lib.Obj, rect_lib.RectDirection):
    LANE_WIDTH = 5.0  # 3.7 meters + buffer for lines

    def __init__(self, pygame, screen, rect_parms, direction_road, direction_lanes, road_prev, lane_cnt, artifacts_def=None):
        obj_lib.Obj.__init__(self, pygame, screen)
        rect_lib.RectDirection.__init__(self, rect_parms, direction_road)

        self.road_prev = road_prev
        self.lane_cnt = lane_cnt
        self.lanes = self.init_lanes(direction_lanes, lane_cnt)
        self.artifacts = self.init_artifacts(artifacts_def)
        self.drive_guides = self.init_drive_guide()

    def get_lane_width(self):
        return u.convert_car(self.LANE_WIDTH)

    def init_lanes(self, direction, lane_cnt):
        lanes = []
        for lane_id in range(lane_cnt):
            lanes.append(Lane(self, direction, lane_cnt, lane_id))
        return lanes

    def init_artifacts(self, artifacts_def):
        artifacts = []
        if not artifacts_def:
            return artifacts

        for artifact_def in artifacts_def:
            type = artifact_def[0]
            artifact_class = ra.CLASSES[type]
            artifacts.append(artifact_class(self.pygame, self.screen, self, artifact_def))
        return artifacts

    def init_drive_guide(self):
        pass

    def update(self, car):
        for artifact in self.artifacts:
            artifact.update(car)

    def draw(self):
        for artifact in self.artifacts:
            artifact.draw()

    def draw_line(self, color, p0, p1):
        self.pygame.draw.lines(self.screen, color, False, [p0, p1], 2)

    def draw_border(self, border, color):
        if border == 'top':
            p0 = self.topleft
            p1 = self.topright
        elif border == 'bottom':
            p0 = self.bottomleft
            p1 = self.bottomright
        elif border == 'left':
            p0 = self.topleft
            p1 = self.bottomleft
        elif border == 'right':
            p0 = self.topright
            p1 = self.bottomright
        else:
            raise ValueError(f"Invalid border: {border}. Must be top, bottom, left, or right.")
        self.draw_line(color, p0, p1)

    def draw_drive_guide(self, car, drive_guide, f_dir_val):
        car_center = car.gnav('center')
        for p in drive_guide:
            if f_dir_val(p, car_center):
                self.pygame.draw.circle(self.screen, self.COLOR_RED, (p[0], p[1]), 0)

    def get_lane_obj(self, obj):
        for lane in self.lanes:
            if obj.in_rect(lane):
                return lane
        return None

class RoadStraight(Road):
    def __init__(self, pygame, screen, road_prev, length, direction_road, lane_cnt, artifacts_def=None):
        rect_parms = self.init_parms(screen, road_prev, lane_cnt, length, direction_road)
        super().__init__(pygame, screen, rect_parms, direction_road, direction_road, road_prev, lane_cnt, artifacts_def)

    def init_parms(self, screen, road_prev, lane_cnt, length, direction):
        rw = self.get_lane_width() * lane_cnt
        if length is None:
            # intersection
            rl = rw
        else:
            # regular rect.py
            rl = u.convert_road(length)

        starting_point = self.get_starting_point(screen, road_prev, rw, rl, direction)
        size = ((rw, rl), (rw, rl), (rl, rw), (rl, rw))[direction]
        return (starting_point[0], starting_point[1], size[0], size[1])

    def get_starting_point(self, screen, road_prev, road_width, road_length, direction):
        # get the starting end for a rect.py in "initial_direction"
        # originating from self.road_prev

        def starting_point_road_prev(road_prev, rw, rl, direction):
            parms = (
                (road_prev.topleft, 0, -rl), (road_prev.bottomleft, 0, 0),
                (road_prev.topleft, -rl, 0), (road_prev.topright, 0, 0))[direction]

            refn_point = parms[0]
            delta_x = parms[1]
            delta_y = parms[2]

            x = refn_point[0] + delta_x
            y = refn_point[1] + delta_y
            return (x, y)

        def starting_point_initial(screen, road_width, road_length, direction):
            sw = screen.get_size()[0]
            sh = screen.get_size()[1]

            def axis_start(dimension):
                return int((dimension - road_width) / 2)

            ## starting_point_initial()
            return (
                (axis_start(sw), sh - road_length),
                (axis_start(sw), 0),
                (sw - road_length, axis_start(sh)),
                (0, axis_start(sh))
            )[direction]

        ## get_starting_point()
        if road_prev:
            return starting_point_road_prev(road_prev, road_width, road_length, direction)
        else:
            return starting_point_initial(screen, road_width, road_length, direction)


class RoadStraightPrimary(RoadStraight):
    def __init__(self, pygame, screen, road_prev, lane_cnt, length, direction_road, artifacts_def):
        super().__init__(pygame, screen, road_prev, length, direction_road, lane_cnt, artifacts_def)

    def draw(self):
        super().draw()

        # draw edges
        self.draw_line(self.COLOR_WHITE, self.gnav("bottomright"), self.gnav("topright"))
        self.draw_line(self.COLOR_WHITE, self.gnav("bottomleft"), self.gnav("topleft"))

        # draw lane markers
        for lane in self.lanes[:-1]:
            lane.draw()


class RoadStraightIntersection(RoadStraight):
    def __init__(self, pygame, screen, road_prev):
        lane_cnt = road_prev.lane_cnt
        length = None
        direction = road_prev.direction
        super().__init__(pygame, screen, road_prev, length, direction, lane_cnt)


class Lane(rect_lib.RectDirection):
    # create lane_cnt moving from right to left side of rect.py
    LANE_MARKER_LENGTH = 10  # pixels
    LANE_MARKER_GAP_LENGTH = 20  # pixels

    def __init__(self, road_current, direction, lane_cnt, lane_id):
        rect_parms = self.init_rect_parms(direction, road_current, lane_cnt, lane_id)
        super().__init__(rect_parms, direction)
        self.road_current = road_current
        self.lane_cnt = lane_cnt
        self.lane_id = lane_id
        self.drive_guide = self.init_drive_guide()

    def init_rect_parms(self, direction, road_current, lane_cnt, lane_id):
        lane_width = road_current.get_lane_width()
        road_length = road_current.gnav('height')
        top_left = road_current.topleft

        if direction == 0:
            # north
            left = top_left[0] + ((lane_cnt - lane_id - 1) * lane_width)
            top = top_left[1]
            width = lane_width
            height = road_length
        elif direction == 1:
            # south
            left = top_left[0] + (lane_id * lane_width)
            top = top_left[1]
            width = lane_width
            height = road_length
        elif direction == 2:
            # west
            left = top_left[0]
            top = top_left[1] + (lane_id * lane_width)
            width = road_length
            height = lane_width
        else:
            # east
            left = top_left[0]
            top = top_left[1] + ((lane_cnt - lane_id - 1) * lane_width)
            width = road_length
            height = lane_width
        return (left, top, width, height)

    def init_drive_guide(self):
        points = []

        center = self.gnav('cw')
        bottom = self.gnav('bottom')
        top = bottom + (self.graph_dir_length * self.gnav('height'))

        for length_pos in range(bottom, top, self.graph_dir_length * 3):
            c = [0, 0]
            c[self.axis_idx_width] = center
            c[self.axis_idx_length] = length_pos
            points.append(c)
        return points

    def draw(self):
        def less_than(v1, v2):
            return v1 < v2

        def greater_than(v1, v2):
            return v1 > v2

        ## draw()
        left = self.gnav('left')
        top = self.gnav('top')
        bottom = self.gnav('bottom')
        height = self.gnav('height')

        axis_idx_width = self.axis_idx_width
        axis_idx_length = self.axis_idx_length
        graph_dir_length = self.graph_dir_length

        marker_cnt = math.ceil(height / (self.LANE_MARKER_LENGTH + self.LANE_MARKER_GAP_LENGTH))
        f_compare = (less_than, greater_than)[bottom < top]

        p0 = [0, 0]
        p1 = [0, 0]
        p0[axis_idx_width] = left
        p1[axis_idx_width] = left

        marker = 0
        line_start = bottom
        while marker < marker_cnt:
            # p0 end
            p0[axis_idx_length] = line_start

            # p1 end
            line_end = line_start + (graph_dir_length * self.LANE_MARKER_LENGTH)
            if f_compare(line_end, top):
                line_end = top
            p1[axis_idx_length] = line_end

            # draw & increment
            self.road_current.draw_line(self.road_current.COLOR_WHITE, p0, p1)
            line_start = line_end + (graph_dir_length * self.LANE_MARKER_GAP_LENGTH)
            marker += 1


class RoadIntersectionTurn(Road):
    def __init__(self, pygame, screen, road_prev, speed, direction_next_road, lane_cnt):
        self.speed = speed
        rect_parms = self.get_rect_parms(road_prev)
        super().__init__(pygame, screen, rect_parms, direction_next_road, road_prev.direction, road_prev, lane_cnt)
        self.drive_guides = self.set_drive_guides()

    def get_rect_parms(self, road_prev):
        def modify_pt(rect_road, point, length_axis_value_factor, length_axis_value):
            new_point = [0, 0]
            new_point[rect_road.axis_idx_width] = point[rect_road.axis_idx_width]
            new_point[rect_road.axis_idx_length] = point[rect_road.axis_idx_length] + length_axis_value_factor * length_axis_value
            return new_point

        ## get_rect_parms()
        rw = road_prev.gnav('width')

        parms = (
            (road_prev.topleft, -1),
            (road_prev.bottomleft, 0),
            (road_prev.topleft, -1),
            (road_prev.topright, 0)
        )[road_prev.direction]
        starting_point = modify_pt(road_prev, parms[0], parms[1], rw)
        return (starting_point[0], starting_point[1], rw, rw)

    def set_drive_guides(self):
        def set_drive_guide_lane(lane_start_idx, lane_start):
            def get_intersection_parms(pr_dir, nr_dir):
                #central_point, radians_headings_value_offset, radians_start_idx, radians_end_idx
                parms = (
                        ((), (), ('topleft', 3, 1, 0), ('topright', 2, 0, 1)),
                        ((), (), ('topright', 0, 0, 1), ('topleft', 1, 1, 0)),
                        (('topright', 1, 0, 1), ('topleft', 2, 1, 0), (), ()),
                        (('topleft', 0, 1, 0), ('topright', 3, 0, 1), (), ())
                    )[pr_dir][nr_dir]
                return parms

            def get_plot_point(hk, radius, theta):
                x = hk[0] + round((radius * np.cos(theta)))
                y = hk[1] + round((radius * np.sin(theta)))
                return x, y

            def get_path_turn(center_point, radius, intersection_parms):
                pi = math.pi
                points = []
                offset = (pi / 2) * intersection_parms[1]
                radian_range = (0, pi / 2)
                radian_start = radian_range[intersection_parms[2]] + offset
                radian_end = radian_range[intersection_parms[3]] + offset
                thetas = np.linspace(radian_start, radian_end, 18)
                for t in thetas:
                    points.append((get_plot_point(center_point, radius, t)))
                return points

            ## set_drive_guide_lane()

            # prev_road parms
            pr_dir = self.road_prev.direction
            start_point = lane_start.gnav('midtop')

            # next rect.py parms
            nr_dir = self.direction

            # get center end
            intersection_parms = get_intersection_parms(pr_dir, nr_dir)
            center_point = self.road_prev.gnav(intersection_parms[0])

            # radius
            width_axis_idx = self.road_prev.axis_idx_width
            hk_width_axis_val = center_point[width_axis_idx]
            p_start_width_axis_val = start_point[width_axis_idx]
            radius = abs(hk_width_axis_val - p_start_width_axis_val)

            # path points
            return get_path_turn(center_point, radius, intersection_parms)

        ## set_drive_guides()
        drive_guides = []
        for lane_idx, lane in enumerate(self.lanes):
            drive_guides.append(set_drive_guide_lane(lane_idx, lane))
        return drive_guides

    def draw(self):
        def draw_border(direction, border_map):
            border = border_map[direction]
            self.draw_border(border, self.COLOR_WHITE)

        ## draw()
        draw_border(self.road_prev.direction, ('top', 'bottom', 'left', 'right'))  # opposite to previous rect.py
        draw_border(self.direction, ('bottom', 'top', 'right', 'left'))  # opposite to next_road
