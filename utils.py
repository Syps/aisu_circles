import os
import json
import glob
from zipfile import ZipFile
from . import definitions
from .serialize import Serializer
from .predictor import SectionPredictor



def get_medium_diff_data():
    return {
        'slider_multiplier': 1.6,
        'overall_difficulty': 6,
        'approach_rate': 7,
        'hp_drain_rate': 5,
        'name': 'Medium'
    }


def get_hard_diff_data():
    return {
        'slider_multiplier': 1.8,
        'overall_difficulty': 7,
        'approach_rate': 8,
        'hp_drain_rate': 7,
        'name': 'Hard'
    }


def load_path_map():
    with open(definitions.AREA_MAP, 'r') as f:
        return json.load(f)


def bpm_to_beat_duration_mls(bpm):
    return (1 / (int(bpm) / 60)) * 1000


def get_hit_objects(
        hit_events,
        predictor,
        remove_extras=True,
        return_areas=False
):
    print('loading probability matrix...')
    if remove_extras:
        adjacent_hit_event = False
        for i, x in enumerate(hit_events):
            if adjacent_hit_event and x == 1:
                hit_events[i] = 0
            elif adjacent_hit_event:
                adjacent_hit_event = False
            elif x == 1:
                adjacent_hit_event = True

    return predictor.predict(return_areas=return_areas)


def build_osu_files(hit_event_set, bpm, song_name, song_file_name,
                    osu_file_name):
    hit_events = [hit_event_set['medium'], hit_event_set['hard']]
    difficulty_data = [get_medium_diff_data(), get_hard_diff_data()]

    for hit_events, difficulty_data in zip(hit_events, difficulty_data):
        model_version = definitions.MODEL_VERSION

        beats_duration = bpm_to_beat_duration_mls(bpm)
        prob_mat = load_path_map()
        predictor = SectionPredictor(prob_mat, hit_events, beats_duration,
                                     difficulty_data['slider_multiplier'])
        hit_objects = get_hit_objects(hit_events, predictor, return_areas=False)

        print('Writing hit objects to .osu file...')
        serializer = Serializer(
            hit_objects,
            model_version,
            song_file_name,
            song_name,
            beats_duration,
            difficulty_data
        )

        file_name_with_difficulty = osu_file_name.format(
            difficulty_data['name']
        )
        serializer.write(file_name_with_difficulty)
        print('finished writing osu file to tmp')


def zip_osz_file(osz_file, osu_files_dir):
    with ZipFile(osz_file, 'w') as f:
        files = glob.glob('{}/*'.format(osu_files_dir))
        for file_name in files:
            print('writing {} to osz archive'.format(file_name))
            f.write(file_name, os.path.basename(file_name))
    print('finished archiving.')

