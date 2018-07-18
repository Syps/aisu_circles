from numbers import Number
from .definitions import hop_length, n_fft


def frames_to_mls(frames, hop_length=hop_length, n_fft=n_fft):
    """
    Convert list of frame indices to list of milliseconds
    """
    if hop_length is None or hop_length <= 0:
        raise ValueError(
            'hop_length must be positive integer. Received {}'.format(
                hop_length))

    if n_fft is None or n_fft <= 0:
        raise ValueError(
            'n_fft must be positive integer. Received {}'.format(n_fft))

    if type(frames) != list and not isinstance(frames, Number):
        raise ValueError(
            'frames must be either list of floats or a number. Received object {} of type {}'.format(
                frames, type(frames)))
    elif type(frames) == float:
        frames = [frames]

    times = frame_to_time(
        frames,
        hop_length=hop_length,
        n_fft=n_fft
    ) * 1000

    return times


"""
    adapted from librosa.core.time_frequency
"""


def sample_to_time(sample, sr=22050):
    return sample / float(sr)


def frame_to_samples(frame, hop_length=512, n_fft=None):
    offset = 0
    if n_fft is not None:
        offset = int(n_fft // 2)

    return int(frame * hop_length + offset)


def frame_to_time(frame, sr=22050, hop_length=512, n_fft=None):
    sample = frame_to_samples(
        frame,
        hop_length=hop_length,
        n_fft=n_fft
    )

    return sample_to_time(sample, sr=sr)
