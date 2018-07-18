import os
from pathlib import Path

ROOT_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
FILE_HEADER = '{}/osu_file_header.txt'.format(ROOT_DIR)
AREA_MAP = '{}/area_path_map.json'.format(ROOT_DIR)
MODEL_VERSION = '1.1.0'

n_fft = 512
hop_length = 256  # default = win_length / 4
