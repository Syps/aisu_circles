import random
from typing import List, Dict
import pdb

# grid
grid_width = 512
grid_height = 384
padding_x = 64
padding_y = 48

width_pixels = grid_width + padding_x * 2
height_pixels = grid_height + padding_y * 2
width_squares = 5
height_squares = 2
path_len = 2

# interval
position_interval = 1.0
interval_leniency = 0.2

# from osu-map-generator
leniency_frames = 16
interval_frames = 85

square_shape = (grid_width // width_squares, grid_height // height_squares)


def random_area(start_area, seed=None) -> int:
    """
    Return a random area that is close to the given area
    """
    r = random.Random(seed)

    x_pos = start_area % width_squares

    y_choices = [0, 1]
    x_choices = [x for x in range(x_pos - 2, x_pos + 3) if
                 0 <= x < width_squares and x != x_pos]

    grid_y = r.choice(y_choices)
    grid_x = r.choice(x_choices)

    new_index = grid_x, grid_y
    new_area = new_index[1] * width_squares + new_index[0]

    if new_area < 0 or new_area > 9:
        pdb.set_trace()

    return new_area


def get_area_number(
        x_pos: int,
        y_pos: int,
        width: int = width_squares,
        height: int = height_squares
) -> int:
    """
    Returns
    -------
    Area number for given position

    Params
    ------
    x - x coordinate on 512 x 384 grid
    y - y coordinate on 512 x 384 grid
    square_len - side length of square

    NOTE: x,y do not include padding so could be negative
    """
    x = int((x_pos + padding_x) / (width_pixels // width))
    y = int((y_pos + padding_y) / (height_pixels // height))
    number = int(y * width_squares + x)

    if number > 9 or number < 0:
        number = -1

    return number


def positions_to_areas(positions: List[tuple]):
    return [get_area_number(*position) if position != (
        -1, -1) else -1 for position in positions]


def random_position_in_square(area_number, seed=None) -> tuple:
    """
    Returns
    -------
    position: tuple - random position in the given area. Position will have
    padding removed so as to match .osu file coordinate scheme,
    so values might be negative.
    """
    r = random.Random(seed)

    x_start = (area_number % width_squares) * square_shape[0]
    y_start = (area_number // width_squares) * square_shape[1]

    try:
        x = r.randrange(x_start,
                        min(x_start + square_shape[0] - padding_x, grid_width)
                        )
        y = r.randrange(y_start,
                        min(y_start + square_shape[1] - padding_y, grid_height))
    except Exception as e:
        pdb.set_trace()
        raise e

    if x < 0 or y < 0:
        pdb.set_trace()

    return x, y


def area_key(*areas: int) -> str:
    """
    Params
    ------
    areas: List of area numbers. Length is equal to len_path
    """
    return '_'.join(map(str, areas))


def filter_valid_paths(pm: dict) -> Dict[str, List[int]]:
    return {key: value for key, value in pm.items() if '-' not in
            key}


def interval_positions(positions) -> List[tuple]:
    intervals = int(len(positions) / interval_frames)

    positions_at_intervals = []

    for i in range(intervals):

        frame = i * interval_frames

        min_dist = leniency_frames + 1

        closest_hit_position = (-1, -1)

        for f in range(frame - leniency_frames, frame + leniency_frames):

            if f > len(positions):
                break
            elif f < 0:
                continue

            if not positions[f] == (-1, -1):
                dist = abs(f - frame)
                if dist < min_dist:
                    min_dist = dist
                    closest_hit_position = positions[f]

        positions_at_intervals.append(tuple(closest_hit_position))

    return positions_at_intervals
