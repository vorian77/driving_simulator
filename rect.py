import pygame


class Rect(pygame.Rect):
    def __init__(self, rect_parms):
        super().__init__(rect_parms)

    def is_equal(self, rect):
        return self.left == rect.left and self.top == rect.top and self.w == rect.w and self.h == rect.h

    def is_clear(self, objects):
        # returns true if there are no objects in rect
        if self is None:
            return None
        else:
            return self.collidelist(objects) == -1

    def contains(self, objects):
        # returns sub-list of objects that are within the rect
        contents = []
        for o in objects:
            if self.colliderect(o):
                contents.append(o)
        return contents

class RectDirection(Rect):
    def __init__(self, rect_parms, direction):
        super().__init__(rect_parms)
        self.direction = None
        self.axis_idx_width = None
        self.axis_idx_length = None
        self.graph_dir_width = None  # towards left side of road
        self.graph_dir_length = None  # towards top of road

        self.primary_attributes = ['top', 'topleft', 'midtop', 'right', 'topright', 'midright', 'bottom', 'bottomright', 'midbottom', 'left', 'bottomleft', 'midleft']
        self.axis_attributes = {'x': ('x', 'y'), 'y': ('y', 'x'), 'cw': ('centerx', 'centery'),
                                'cl': ('centery', 'centerx'), 'width': ('width', 'height'), 'height': ('height', 'width')}
        self.persist_attributes = {'center': 'center', 'centerx': 'centerx', 'centery': 'centery'}
        self.set_direction(direction)

    def set_direction(self, direction):
        self.direction = direction  # 0-north, 1-south, 2-west, 3-east
        self.normailze_factor = (0, -2, -1, -3)[direction]
        direction_parms = ((0, 1, -1, -1), (0, 1, 1, 1), (1, 0, 1, -1), (1, 0, -1, 1))[direction]
        self.axis_idx_width = direction_parms[0]
        self.axis_idx_length = direction_parms[1]
        self.graph_dir_width = direction_parms[2]  # towards left side of road
        self.graph_dir_length = direction_parms[3]  # towards top of road

    def get_angle(self, direction):
        return (90, 270, 180, 0)[direction]

    def get_angle_current(self):
        return self.get_angle(self.direction)

    def gnal_element_primary(self, attribute):
        attribute_idx = self.primary_attributes.index(attribute)
        normalized_idx = (attribute_idx + (self.normailze_factor * 3)) % len(self.primary_attributes)
        normalized_attribute = self.primary_attributes[normalized_idx]
        return normalized_attribute

    def gnal_axis(self, attribute):
        attribute_values = self.axis_attributes[attribute]
        normalized_attribute = attribute_values[self.axis_idx_width == 1]
        return normalized_attribute

    def gnal(self, attribute):
        # get normalized attribute label
        if attribute in self.primary_attributes:
            normalized_attribute = self.gnal_element_primary(attribute)
            return normalized_attribute
        elif attribute in self.axis_attributes:
            normalized_attribute = self.gnal_axis(attribute)
            return normalized_attribute
        else:
            return self.persist_attributes[attribute]

    def gnav(self, attribute):
        # get normalized attribute value
        normalized_attribute = self.gnal(attribute)
        value = getattr(self, normalized_attribute)
        return list(value) if isinstance(value, tuple) else value

    def snav(self, attribute, value):
        # set normalized attribute value
        normalized_attribute = self.gnal(attribute)
        return setattr(self, normalized_attribute, value)

    def pos_obj(self, rect_target_attribute, obj_rect, obj_rect_attribute):
        obj_rect.set_direction(self.direction)
        value = self.gnav(rect_target_attribute)
        normalized_obj_rect_attribute = self.gnal(obj_rect_attribute)
        setattr(obj_rect, normalized_obj_rect_attribute, value)

    def get_dir_val_function(self, direction):
        def f_dir_val_greater_north(p0, p1):
            return p0[1] < p1[1]

        def f_dir_val_greater_south(p0, p1):
            return p0[1] > p1[1]

        def f_dir_val_greater_west(p0, p1):
            return p0[0] < p1[0]

        def f_dir_val_greater_east(p0, p1):
            return p0[0] > p1[0]

        ## set_dir_val_function()
        return (f_dir_val_greater_north,
                f_dir_val_greater_south,
                f_dir_val_greater_west,
                f_dir_val_greater_east)[direction]

    def dir_val_exceeds(self, p0, p1):
        # returns true if length axis value of p0 exceeds that of p1
        f_dir_val = self.get_dir_val_function(self.direction)
        return f_dir_val(p0, p1)
