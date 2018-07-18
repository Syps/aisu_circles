from . import definitions


def serialize_hit_circle(hit_circle):
    template = '{x},{y},{time},{type},{hit_sound},{extras}'

    return template.format(**hit_circle)


def serialize_slider(slider):
    template = (
        '{x},{y},{time},{type},{hit_sound},{slider_type}|{curve_points},'
        '{repeat},{pixel_length},{edge_hit_sounds},{edge_additions},'
        '{extras}'
    )

    return template.format(**slider)


def get_colors(colors=None):
    '''
    Desired format
    --------------
    Combo1 : 111,174,238
    Combo2 : 13,78,185
    Combo3 : 206,206,255
    '''
    if not colors:
        colors = [[111, 174, 238], [13, 78, 185], [206, 206, 255]]

    combo_template = 'Combo{} : {}'
    combo_strings = [combo_template.format(str(i + 1), ','.join(map(str, c)))
                     for i, c in enumerate(colors)]

    return '\n'.join(combo_strings)


class Serializer:
    def __init__(self, hit_objects, model_version, song_path, song_name,
                 beat_duration_mls, difficulty_settings):
        self._hit_objects = hit_objects
        self._version = model_version
        self._song_path = song_path
        self._song_name = song_name
        self._beat_duration_mls = beat_duration_mls
        self._file_header = definitions.FILE_HEADER
        self._colors = get_colors()
        self._hp_drain_rate = difficulty_settings['hp_drain_rate']
        self._approach_rate = difficulty_settings['approach_rate']
        self._overall_difficulty = difficulty_settings['overall_difficulty']
        self._slider_multiplier = difficulty_settings['slider_multiplier']
        self._difficulty_name = difficulty_settings['name']

    def write(self, file_name):
        file_contents = self._file_contents()

        with open(file_name, 'w') as f:
            f.write(file_contents)

    def _file_contents(self) -> str:
        file_contents = self._file_header_sections()

        hit_object_lines = []

        for obj in self._hit_objects:

            if obj['type'] in (1, 5):
                hit_object_lines.append(serialize_hit_circle(obj))
            elif obj['type'] in (2, 6):
                hit_object_lines.append(serialize_slider(obj))

        hit_object_lines = '\n'.join(hit_object_lines)

        return '{}\n{}\n'.format(file_contents, hit_object_lines)

    def _file_header_sections(self):
        with open(self._file_header, 'r') as f:
            return f.read().format(
                title=self._song_name,
                version=self._version,
                song_path=self._song_path,
                song_name=self._song_name,
                beat_duration_mls=self._beat_duration_mls,
                colors=self._colors,
                hp_drain_rate=self._hp_drain_rate,
                slider_multiplier=self._slider_multiplier,
                approach_rate=self._approach_rate,
                overall_difficulty=self._overall_difficulty,
                difficulty_name=self._difficulty_name
            )
