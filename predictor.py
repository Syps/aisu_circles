from typing import List

import random
from . import markov
from .section import ComboSection
import pdb


class HitCirclePredictor:
    def __init__(self,
                 path_map: dict,
                 hit_events,
                 beat_duration_mls,
                 slider_multiplier,
                 random_seed=None):
        self._path_map = path_map
        self._hit_events = hit_events
        self._beat_duration_mls = beat_duration_mls
        self._slider_multiplier = slider_multiplier
        self._screen_width = 512
        self._screen_height = 384
        self._random = random.Random(random_seed)
        self._slider_types = ['linear', 'bezier']

    @property
    def len_frames(self):
        return len(self._hit_events)

    def _next_area(self, area1, area2):
        attempts = 0
        key = 'bad_key'
        while key not in self._path_map:
            if attempts > 3:
                key = self._random.choice(list(self._path_map.keys()))
                break

            key = markov.area_key(area1, area2)
            attempts += 1

        next_area = self._random.choice(self._path_map[key])

        while next_area == area2:
            next_area = self._random.choice(self._path_map[key])

        if next_area < 0:
            pdb.set_trace()

        return next_area

    def _generate_areas(self):
        """
        Return generated, ordered list of area numbers that hit events will
        pass through as the song progresses.
        List length = song_length_frames // length_interval_frames
        """
        print('generating area checkpoints...')
        first_x = self._random.randrange(self._screen_width)
        first_y = self._random.randrange(self._screen_height)

        area1 = markov.get_area_number(first_x, first_y)
        area2 = markov.random_area(area1)
        area3 = markov.random_area(area2)

        areas = [area1, area2, area3]

        if -1 in areas or 10 in areas:
            pdb.set_trace()

        for t in range(3 * markov.interval_frames,
                       self.len_frames + markov.interval_frames,
                       markov.interval_frames):
            next_area = self._next_area(*areas[-2:])

            if next_area == -1 or next_area > 9:
                pdb.set_trace()
            areas.append(next_area)

        return areas

    def _get_interval_sections(self) -> List[tuple]:
        """
        Split the song into list of sections - either:
            A - slider
            B - space between slider

        Return a list of tuples representing start/end of sections
        """
        intervals = []
        index = 1

        section_start = 0
        while index < self.len_frames:
            value = self._hit_events[index]
            start_value = self._hit_events[section_start]

            if value == 1:
                if start_value == 0:
                    if index < self.len_frames - 1 and \
                                    self._hit_events[index + 1] == 1:
                        intervals.append((section_start, index))
                        section_start = index

            if value == 0:
                if start_value == 1:
                    intervals.append((section_start, index))
                    section_start = index

            index += 1

        if section_start != self.len_frames - 1:
            intervals.append((section_start, self.len_frames))

        return intervals

    def _get_section(self, start, end, last_hit_index, last_hit_position,
                     destination_position, new_combo=False):
        """
        Returns
        -------
        section.Section object for the given params
        """
        raise NotImplementedError

    def _get_section_objects(self, interval_checkpoints, interval_sections):
        sections = []
        last_hit_index = 0
        last_hit_position = interval_checkpoints[0]
        print('building sections list...')
        for start, end in interval_sections:
            destination = end // markov.interval_frames
            destination_position = interval_checkpoints[destination]
            s = self._get_section(start, end, last_hit_index,
                                  last_hit_position, destination_position)

            sections.append(s)

            i = end - 1
            while i >= start:
                if self._hit_events[i] == 1:
                    last_hit_index = i
                    last_hit_position = s.path[i - start]
                    break
                i -= 1

        return sections

    def _get_sections(self, checkpoints):
        raise NotImplementedError

    def predict(self, return_areas=False):
        """
        Returns
        -------
        List of dictionaries representing hit/slider events
        """
        areas = self._generate_areas()
        print('translating areas to random positions...')
        interval_checkpoints = [markov.random_position_in_square(n) for n in
                                areas]

        print('getting section start/end times...')
        sections = self._get_sections(interval_checkpoints)

        print('building list of hit objects...')
        result = [h for s in sections for h in s.get_hits()]

        if return_areas:
            return result, (areas, interval_checkpoints)
        else:
            return result


class SectionPredictor(HitCirclePredictor):
    """
    As long as not breaking up a stack, split sections based on markov interval.
    Start each interval from the end of the previous section.
    """

    def _divides_stack(self, section_start, index) -> bool:

        stack_threshold = 20
        if section_start + markov.interval_frames > index + stack_threshold:
            return False

        closest_left = 1

        left_start = index - closest_left
        left_end = min(section_start, index - stack_threshold)
        left_index = left_start

        for i in range(left_start, left_end, -1):
            if self._hit_events[i] == 1:
                left_index = i
                break

        end_range = min(len(self._hit_events), index + stack_threshold - (
                    section_start - left_index) - 1)
        for i in range(index + 1, end_range):
            if self._hit_events[i] == 1:
                return True

        return False

    def _get_section(self, start, end, last_hit_index, last_hit_position,
                     destination_area, new_combo=False):
        """
        Returns a ComboSection containing all the hits
        occuring inside this section
        """
        destination_position = markov.random_position_in_square(
            destination_area)

        return ComboSection(
            start,
            last_hit_index,
            last_hit_position,
            destination_position,
            self._hit_events[start:end],
            self._beat_duration_mls,
            self._slider_multiplier,
            new_combo
        )

    def __get_section_start_stops(self):
        section_start_stops = []
        index = 0

        while index < self.len_frames:

            section_start = section_end = index
            while index < self.len_frames and index < section_start +\
                    markov.interval_frames:
                if self._hit_events[index] == 1 and not self._divides_stack(
                        section_start, index):
                    section_end = index + 1

                index += 1

            if section_start != section_end:
                section_start_stops.append((section_start, section_end))
                index = section_end + 1
            else:
                index += 1

        return section_start_stops

    def _get_sections(self, checkpoints):
        first_x = self._random.randrange(self._screen_width)
        first_y = self._random.randrange(self._screen_height)

        area1 = markov.get_area_number(first_x, first_y)
        area2 = markov.random_area(area1)
        section_start_stops = self.__get_section_start_stops()

        sections = []
        last_pos = first_x, first_y
        last_index = 0
        previous_areas = [area1, area2]

        for section_index, start_stop in enumerate(section_start_stops):
            new_combo = section_index % 3 == 0
            # new_combo = True  # DEBUG
            start, stop = start_stop
            next_destination = self._next_area(*previous_areas[-2:])
            section = self._get_section(start, stop, last_index, last_pos,
                                        next_destination, new_combo)
            sections.append(section)
            last_pos = section.end_position

            last_index = stop
            previous_areas.extend(markov.positions_to_areas([last_pos]))

        return sections
