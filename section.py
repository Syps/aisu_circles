from typing import List
import random

import math
import pdb

from . import definitions, position, timing


def mid_point(p1, p2) -> tuple:
    x = p1[0] + (p2[0] - p1[0]) / 2
    y = p1[1] + (p2[1] - p1[1]) / 2

    return x, y


def random_bezier_path(duration, start_pos, end_pos, repeats=1, seed=None):
    pass


def get_pixel_length(frame_duration, slider_multiplier, beat_duration_mls,
                     **kwargs):
    """
    Reverse solve for pixel length given duration_frames
    """
    mls_duration = timing.frames_to_mls(frame_duration, **kwargs)
    velocity = 100.0 * slider_multiplier
    n_beats = mls_duration / float(beat_duration_mls)

    return n_beats * velocity


def intersperse(indexes):
    '''
    Return new array with indexes halved and spread equal distances apart
    '''
    first, last = indexes[0], indexes[-1]
    total_dist = last - first
    step = int(total_dist / math.ceil(len(indexes) / 2))

    return [i for i in range(first, last, step)]


class Section:
    def __init__(
            self,
            section_start,
            last_hit_index,
            last_hit_position,
            destination_position,
            hit_events,
            beat_duration_mls,
            slider_multiplier,
            new_combo_section=False
    ):

        if last_hit_index > section_start:
            raise ValueError('last hit position must come before section start')

        self.last_hit_index = last_hit_index
        self.last_hit_position = last_hit_position
        self.destination_position = destination_position
        self.section_start = section_start
        self.hit_events = hit_events
        self.new_combo_section = new_combo_section
        self._path_types = ['linear', 'bezier']
        self._path = None
        self._slider_multiplier = slider_multiplier
        self._beat_duration_mls = beat_duration_mls

    @property
    def len_frames(self):
        return len(self.hit_events)

    def define_circle(self, start_pos, end_pos, offset):

        direction = end_pos[0] - start_pos[0], end_pos[1] - start_pos[1]
        midpt = start_pos[0] + direction[0] / 2, start_pos[1] + direction[
            1] / 2
        ctrl_pt = midpt[0] + direction[1] / offset, midpt[1] - direction[
            0] / offset

        if not position.valid_coord(*ctrl_pt):
            ctrl_pt = midpt[0] - direction[1] / 2, midpt[1] + direction[
                0] / 2

        return position.define_circle(start_pos, ctrl_pt, end_pos)

    def random_circle_path(self, duration, start_pos, end_pos, repeats=1):
        offset = 4
        iteration = 0
        ii = 0

        while True:
            if iteration > 3:
                if ii > 5:
                    raise ValueError(
                        "Unable to find valid path from {} to {} in {} time"
                            .format(start_pos, end_pos, duration))
                iteration = 0
                offset = 4
                end_pos = self.random_next_stop()
                ii += 1

            c_x, c_y, r = self.define_circle(start_pos, end_pos, offset)

            try:
                osu_pixel_dist = (timing.frames_to_mls(
                    duration) / self._beat_duration_mls) * 100 * self._slider_multiplier
                path = position.find_valid_path(
                    c_x,
                    c_y,
                    r,
                    start_pos,
                    end_pos,
                    duration,
                    slider_multiplier=self._slider_multiplier,
                    osu_pixel_dist=osu_pixel_dist
                )
            except position.InvalidPathException:
                pass
            else:
                if path:
                    break

            offset *= 2
            iteration += 1

        return path

    def _pick_path_type(self) -> str:
        raise NotImplementedError

    def get_hits(self, ) -> List[dict]:
        raise NotImplementedError

    def random_angle(self, start_radians, end_radians) -> float:
        """
        Returns random angle (in radians) occurring in the given range
        """
        start = int(min(start_radians, end_radians) * 100)
        end = int(max(start_radians, end_radians) * 100)

        if start_radians < end_radians:
            angle = random.choice(list(range(start, end))) / 100
        else:
            range1 = list(range(end, int(200 * math.pi)))
            range2 = list(range(0, start))

            angle = random.choice(range1 + range2) / 100

        return angle

    def random_next_stop(self):
        max_radius = position.max_dist_from_edge(self.last_hit_position)
        first_hit_index = next((i for i, e in enumerate(self.hit_events) if e == 1)) + self.section_start
        radius = min(get_pixel_length(
            first_hit_index - self.last_hit_index,
            self._slider_multiplier,
            self._beat_duration_mls
        ), max_radius)

        c_x, c_y = self.last_hit_position
        angle = self.random_angle(
            *position.valid_radian_range(c_x, c_y, radius)
        )

        pos = (
            c_x + radius * math.cos(angle),
            c_y - radius * math.sin(angle)
        )

        if not position.valid_coord(*pos):
            print('Invalid position reached in random_next_stop: {}'.format(pos))

        return pos

    @property
    def path(self):
        if self._path is not None:
            return self._path
        else:
            path_type = self._pick_path_type()
            frames_since_last = self.section_start - self.last_hit_index
            duration = self.len_frames + frames_since_last

            if path_type == 'linear':
                path = position.linear_positions(
                    duration,
                    self.random_next_stop(),
                    self.destination_position
                )
                if not position.valid_coord(*path[-1]):
                    pdb.set_trace()
            elif path_type == 'bezier':
                path = random_bezier_path(
                    duration,
                    self.last_hit_position,
                    self.destination_position
                )
            elif path_type == 'circle':
                try:
                    path = self.random_circle_path(
                        duration,
                        self.random_next_stop(),
                        self.destination_position,
                    )
                except:
                    path = position.linear_positions(
                        duration,
                        self.random_next_stop(),
                        self.destination_position
                    )
            else:
                raise ValueError('Unknown path type \'{}\''.format(path_type))

            self._path = path[frames_since_last:]

            return self._path

    @property
    def end_position(self):
        return self.path[-1]

    def _get_hit_circle(self, frame_index):
        pos = self.path[frame_index]
        time = timing.frames_to_mls(
            frame_index + self.section_start,
            hop_length=definitions.hop_length,
            n_fft=definitions.n_fft
        )

        if self.new_combo_section:
            hit_type = 5
            self.new_combo_section = False
        else:
            hit_type = 1

        return {
            'x': int(pos[0]),
            'y': int(pos[1]),
            'time': int(time),
            'type': hit_type,
            'hit_sound': '0',
            'extras': '0:0:0:0:'
        }

    def _get_slider(self, start_pos, time, curve_pts, pixel_length):

        if self.new_combo_section:
            hit_type = 6
            self.new_combo_section = False
        else:
            hit_type = 2

        return {
            'x': int(start_pos[0]),
            'y': int(start_pos[1]),
            'time': int(time),
            'type': hit_type,
            'hit_sound': 0,
            'slider_type': 'P',
            'curve_points': '|'.join(
                ['{}:{}'.format(*map(int, c)) for c in curve_pts]),
            'repeat': 1,
            'pixel_length': int(pixel_length),
            'edge_hit_sounds': '0|0',
            'edge_additions': '0:0|0:0',
            'extras': '0:0:0:0:'
        }


class HitCircleSection(Section):
    def _pick_path_type(self) -> str:
        return random.choice(self._path_types, weights=[0.2, 0.8])

    def get_hits(self) -> List[dict]:
        return [self._get_hit_circle(0, self.random_next_stop())]


class SliderSection(Section):
    def _pick_path_type(self) -> str:
        return random.choice(self._path_types, weights=[0.3, 0.7])

    def get_hits(self) -> List[dict]:
        '''
        need to finish
        :return:
        '''
        duration = self.len_frames
        time = timing.frames_to_mls(self.section_start,
                                    hop_length=definitions.hop_length,
                                    n_fft=definitions.n_fft)

        pixel_length = get_pixel_length(
            duration,
            self._slider_multiplier,
            self._beat_duration_mls,
            hop_length=definitions.hop_length,
            n_fft=definitions.n_fft
        )

        ctrl_pt_indexes = random.choice(range(0, duration), k=2)
        ctrl_pt_positions = [self.path[i] for i in ctrl_pt_indexes]
        curve_points = [(int(p[0]), int(p[1])) for p in ctrl_pt_positions]

        return [
            self._get_slider(self.path[0], time, curve_points, pixel_length)]


class ComboSection(Section):
    '''
    Section comprised of both hit circles and sliders
    '''

    def _pick_path_type(self) -> str:
        # return 'circle' if bool(random.randint(0, 1)) else 'linear'
        return 'circle'

    def _pixel_len_path(self, start, stop):
        pts = self.path[start:stop]
        total_len = 0
        for i, pt in enumerate(pts[1:]):
            prev_x, prev_y = pts[i - 1]
            d = position.distance_between(prev_x, prev_y, pt[0], pt[1])
            total_len += d

        return total_len

    def get_slider(self, start_index, end_index):
        mid_index = start_index + int((end_index - start_index) / 2)
        start_pos = self.path[start_index]
        curve_pts = self.path[mid_index], self.path[end_index]

        time = timing.frames_to_mls(self.section_start + start_index)

        osu_pixel_len = get_pixel_length(
            end_index - start_index,
            self._slider_multiplier,
            self._beat_duration_mls
        )

        return self._get_slider(start_pos, time, curve_pts, osu_pixel_len)

    def get_hits(self) -> List[dict]:
        hit_indexes = [i for i, x in enumerate(self.hit_events) if x == 1]
        n_hits = len(hit_indexes)
        hit_objects = []

        if n_hits == 0:
            raise ValueError('Section must contain at least 1 hit')
        elif n_hits == 1:
            index = hit_indexes[0]
            hit_objects.append(self._get_hit_circle(index))
        elif n_hits == 2:
            if bool(random.choices([0, 1], [0.4, 0.6])):
                hit_objects.append(self.get_slider(*hit_indexes))
            else:
                index1, index2 = hit_indexes
                hit_objects.append(self._get_hit_circle(index1))
                hit_objects.append(self._get_hit_circle(index2))
        else:
            min_slider_threshold = 15  # min frame dist to use slider
            i = 0
            while i < n_hits:
                hit_index = hit_indexes[i]
                last_hit_in_section = i < n_hits - 1
                if last_hit_in_section and hit_indexes[i + 1] - hit_index >= min_slider_threshold:
                    hit_objects.append(self.get_slider(*hit_indexes[i:i + 2]))
                    i += 2
                else:
                    hit_circles, new_i = self.clean_stack(hit_indexes, i)
                    hit_objects.extend(hit_circles)
                    i = new_i

        return hit_objects

    def clean_stack(self, hit_indexes, i, min_slider_threshold=15):
        '''
        If a stack exists in the hit indexes with length >= 4,
        divide stack number by 2 (round up),
        and evenly intersperse that number of hit events
        between stack_Start and stack_end.

        Return stack and next section index to continue at

        If no stack exists, return empty list and first index
        '''
        hit_index = hit_indexes[i]
        remaining_hit_indexes = hit_indexes[i:]

        if len(remaining_hit_indexes) < 4:
            stack = [self._get_hit_circle(hit_index)]
            new_i = i + 1
        else:
            j = 0
            stack_indexes = []
            while j < len(remaining_hit_indexes) - 1 \
                    and remaining_hit_indexes[j + 1] - remaining_hit_indexes[
                        j] >= min_slider_threshold:
                stack_indexes.append(remaining_hit_indexes[j])
                j += 1

            if len(stack_indexes) >= 4:
                if j == remaining_hit_indexes - 1:
                    stack_indexes.append(remaining_hit_indexes[j])
                    j += 1
                stack_indexes = intersperse(stack_indexes)

            stack = [self._get_hit_circle(index) for index in stack_indexes]
            j += 1

            new_i = i + j

        return stack, new_i







