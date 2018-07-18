import math
from typing import List, Tuple
import pdb

X_LOWER_BOUND = 0
X_UPPER_BOUND = 640
Y_LOWER_BOUND = 48
Y_UPPER_BOUND = 334


def linspace(a, b, num):
    diff = b - a + (1 if b > a else -1)
    step = diff / num
    return [a + step * i for i in range(num)]


def max_dist_from_edge(position: Tuple):
    x, y = position
    edges = [(0, y), (x, 0), (584, y), (x, 364)]
    dists = [distance_between_positions(position, edge) for edge in edges]

    return int(max(dists) * .75)


def distance_between_positions(a: Tuple, b: Tuple):
    return distance_between(a[0], a[1], b[0], b[1])


def distance_between(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def arc_len(a: tuple, b: tuple, center: tuple, radius: int) -> int:
    """
    Return the arc length between points `a` and `b` on a circle with
    the given `radius`, moving clockwise (`left`) or
    counter-clockwise (`!left`)
    """
    start_angle = get_angle_radians(center, a)
    end_angle = get_angle_radians(center, b)

    reflex = start_angle > end_angle and start_angle - end_angle < math.pi
    angle = abs(start_angle - end_angle)

    return 2 * math.pi - angle * radius if reflex else angle * radius


def get_quadrant(origin, point):
    """
    Return the circle quadrant the vector lies in

    NOTE: Y-axis is INVERTED
    """
    if origin[0] < point[0] and origin[1] == point[1]:
        return 0

    if origin[0] >= point[0] and origin[1] > point[1]:
        quadrant = 1
    elif origin[0] <= point[0] and origin[1] < point[1]:
        quadrant = 3
    elif origin[0] <= point[0]:
        quadrant = 0
    else:
        quadrant = 2

    return quadrant


def get_angle_radians(origin, point):
    """
    Return angle of line connecting points 1 and 2
    """
    quadrant = get_quadrant(origin, point)

    if quadrant in (1, 3):
        point3 = origin[0], point[1]
    else:
        point3 = point[0], origin[1]

    a = distance_between(point3[0], point3[1], point[0], point[1])
    c = distance_between(origin[0], origin[1], point[0], point[1])

    sin_A = a / c  # backwards solve using law of sines (w/ C being right angle)

    try:
        return math.asin(sin_A) + quadrant * math.pi / 2
    except ValueError:
        pdb.set_trace()


def solve_x_for_circle(c_x, c_y, radius, y):
    v = radius ** 2 - (y - c_y) ** 2

    return None if v < 0 else ((c_x - v ** 0.5, y), (c_x + v ** 0.5, y))


def solve_y_for_circle(c_x, c_y, radius, x):
    u = radius ** 2 - (x - c_x) ** 2

    return None if u < 0 else ((x, c_y - u ** 0.5), (x, c_y + u ** 0.5))


def is_between(a, b, c) -> bool:
    """
    Returns whether point `c` lies between `a` and `b` on a circle.
    Movement along the circle path is always counter-clockwise
    """
    # m = (b[1] - a[1]) / (b[0] - a[0])
    # b = a[1] - m * a[0]
    #
    # return float(c[1]) < float(m * c[0] + b)

    return is_left(a, c, b)


def move_counter_clockwise(a, b, c) -> bool:
    return is_between(a, b, c)


class InvalidPathException(BaseException):
    pass


def find_valid_path(c_x, c_y, radius, start_pos, end_pos, duration, slider_multiplier=1, osu_pixel_dist=None):
    """
    Returns list of points on a valid path from `start_pos` to `end_pos` if
    such a path exists. Otherwise, returns None
    """
    intersect_pts = find_intersect_pts(c_x, c_y, radius)
    center = c_x, c_y
    reverse = False

    if not [pt for pt in intersect_pts if is_between(start_pos, end_pos, pt)]:
        distance = arc_len(start_pos, end_pos, center, radius)
    elif not [pt for pt in intersect_pts if
                    is_between(end_pos, start_pos, pt)]:
        distance = arc_len(end_pos, start_pos, center, radius)
        reverse = True
    else:
        return None

    if osu_pixel_dist and osu_pixel_dist > abs(distance):
        distance = osu_pixel_dist if distance > 0 else osu_pixel_dist * -1

    step_length = distance * slider_multiplier / duration
    path = []

    for i in range(duration):
        radians = i * step_length / distance
        path.append(next_circle_point(
            start_pos[0],
            start_pos[1],
            c_x,
            c_y,
            radians if not reverse else radians * -1
        ))

    if list(filter(lambda i: invalid_coord(*i), path)):
        raise InvalidPathException

    return path


def find_intersect_pts(c_x, c_y, radius) -> List[tuple]:
    """
    Return a list of all points on the given circle that intersect with
    the grid bounds (512x384)
    """
    x_bounds = [0, 512]
    y_bounds = [0, 384]

    solve_x = lambda y: solve_x_for_circle(c_x, c_y, radius, y)
    solve_y = lambda x: solve_y_for_circle(c_x, c_y, radius, x)

    x_intersects = list(map(solve_x, y_bounds))
    y_intersects = list(map(solve_y, x_bounds))

    intersects = [i for i in x_intersects + y_intersects if i]
    pts = [pt for p in intersects for pt in p]

    return pts


def has_valid_path(c_x, c_y, radius, start_pos, end_pos) -> bool:
    """
    Returns whether the given circle has a valid path from `start_pos`
    to `end_pos`. The path is valid if all points between the two positions
    are valid
    """
    intersect_pts = find_intersect_pts(c_x, c_y, radius)

    return not [pt for pt in intersect_pts if
                is_between(start_pos, end_pos, pt)] or \
           not [pt for pt in intersect_pts if
                is_between(end_pos, start_pos, pt)]


def valid_radian_range(c_x, c_y, radius) -> tuple:
    '''
    Returns tuple representing start radian and end radian. Direction is always
    counter clockwise
    '''
    intersect_pts = find_intersect_pts(c_x, c_y, radius)
    center = c_x, c_y

    if len(intersect_pts) < 2:
        start_a, end_a = 0, 2 * math.pi
    else:
        intersect_angles = [get_angle_radians(center, pt) for pt in intersect_pts]
        intersect_angles = sorted(intersect_angles)
        intersect_angles.append(intersect_angles[0])

        max_dist = 0
        start_a = intersect_angles[0]
        end_a = intersect_angles[0]

        for index, a in enumerate(intersect_angles[:-1]):
            next_a = intersect_angles[index + 1]
            diff = next_a - a if next_a > a else math.pi * 2 - a + next_a
            mid_a = a + diff / 2

            pt_mid = get_point(c_x, c_y, radius, mid_a)

            if valid_coord(*pt_mid) and diff > max_dist:
                    start_a = a
                    end_a = next_a
                    max_dist = next_a - a

    if start_a == end_a:
        print('warning: start_radian == end_radian: start: {}, end {}'
              .format(start_a, end_a))

    return start_a, end_a


def extend_positions(positions, repeats) -> List:
    extended_positions = positions[:]
    for repeat in range(repeats - 1):
        if repeat % 2 == 0:
            repeat_positions = reversed(positions)
        else:
            repeat_positions = positions
        extended_positions.extend(repeat_positions)

    return extended_positions


def define_circle(a, b, c):
    """
    https://github.com/nojhamster/osu-parser/blob/master/lib/slidercalc.js
    """
    x1, y1 = a
    x2, y2 = b
    x3, y3 = c

    bc_y = y2 - y3
    ca_y = y3 - y1
    ab_y = y1 - y2

    cb_x = x3 - x2
    ac_x = x1 - x3
    ba_x = x2 - x1

    d = 2 * (x1 * bc_y + x2 * ca_y + x3 * ab_y)

    c_x = ((x1 ** 2 + y1 ** 2) * bc_y + (x2 ** 2 + y2 ** 2) * ca_y + (
        x3 ** 2 + y3 ** 2) * ab_y) / d
    c_y = ((x1 ** 2 + y1 ** 2) * cb_x + (x2 ** 2 + y2 ** 2) * ac_x + (
        x3 ** 2 + y3 ** 2) * ba_x) / d
    r = distance_between(c_x, c_y, x1, y1)

    return c_x, c_y, r


def get_point(c_x, c_y, radius, angle):
    end_x = c_x + radius * math.cos(angle)
    end_y = c_y - radius * math.sin(angle)

    return end_x, end_y


def next_circle_point(start_x, start_y, c_x, c_y, radians) -> tuple:
    start_angle = get_angle_radians((c_x, c_y), (start_x, start_y))
    angle = start_angle + radians
    radius = distance_between(start_x, start_y, c_x, c_y)

    return get_point(c_x, c_y, radius, angle)


def valid_coord(x, y) -> bool:
    """
    Return whether or not the given x,y coordinate is within
    the bounds of the grid
    """
    return X_LOWER_BOUND <= x <= X_UPPER_BOUND and Y_LOWER_BOUND <= y <= Y_UPPER_BOUND


def invalid_coord(*args) -> bool:
    return not valid_coord(*args)


def linear_positions(duration, start, end, repeats=1):
    x1, y1 = start
    x2, y2 = end

    x_coords = linspace(x1, x2, duration // repeats)
    y_coords = linspace(y1, y2, duration // repeats)

    positions = list(zip(x_coords, y_coords))

    negative_pos = next((i for i in positions if i[0] < -64 or i[1] < -32),
                        None)

    if negative_pos is not None:
        pdb.set_trace()

    return extend_positions(positions, repeats)


def is_left(a, b, c):
    """
    Params
    ------
    3 points - start, pass_through, end

    Returns
    -------
    is_left: Boolean - True if end is on left of start and passthrough
    """

    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) < 0


def circle_positions(pixel_len, duration, start, pass_through, end, repeats):
    """
    Params
    ------

    pixel_len: int - length in pixels of the slider
    duration: int - number of frames for which this slider lasts
    repeats: int - number of times the slider path will be traversed
    """
    c_x, c_y, radius = define_circle(start, pass_through, end)

    radians = pixel_len / radius
    if is_left(start, pass_through, end):
        radians *= -1

    steps = linspace(0, radians, duration // repeats)

    positions = [next_circle_point(start[0], start[1], c_x, c_y, r) for
                 r in
                 steps]

    negative_pos = next((i for i in positions if i[0] < -64 or i[1] < -32),
                        None)

    if negative_pos is not None:
        pdb.set_trace()

    return extend_positions(positions, repeats)


# def bezier_positions(duration, points, repeats):
#     pl = len(points)
#     points_array = np.asarray(points, dtype=np.float).reshape((2, pl))
#     nodes = np.asfortranarray(points_array)
#     degree = nodes.shape[1]
#     curve = bezier.Curve(nodes, degree=degree)
#
#     s_vals = np.linspace(0.0, 1.0, duration // repeats)
#     positions = curve.evaluate_multi(s_vals)
#     positions = [tuple(p) for p in positions.T]
#
#     positions = extend_positions(positions, repeats)
#
#     negative_pos = next((i for i in positions if i[0] < -64 or i[1] < -32),
#                         None)
#
#     if negative_pos is not None:
#         pdb.set_trace()
#
#     return positions
