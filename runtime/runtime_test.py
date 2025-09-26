import argparse
import time

import numpy as np
import soundfile

from engine import (
    Engine,
    Engines
)
from mixer import DEFAULT_SAMPLERATE


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wav_path', required=True)
    parser.add_argument('--engine', choices=[x.value for x in Engines])
    parser.add_argument('--access_key', default=None)
    args = parser.parse_args()

    wav_path = args.wav_path
    engine = args.engine
    access_key = args.access_key

    pcm, sample_rate = soundfile.read(wav_path, dtype=np.int16)
    model = Engine.create(Engines(engine), threshold=0, access_key=access_key)

    assert sample_rate == DEFAULT_SAMPLERATE

    frame_length = model.frame_length()
    frame_count = pcm.size // frame_length

    total_cpu_time_sec = 0.0
    total_processed_time_sec = 0.0
    for i in range(frame_count):
        _pcm = pcm[i * frame_length: (i + 1) * frame_length]
        start_time = time.monotonic()
        model.process(_pcm, i)
        end_time = time.monotonic()

        total_cpu_time_sec += (end_time - start_time)
        total_processed_time_sec += (frame_length / DEFAULT_SAMPLERATE)
    real_time_factor = total_cpu_time_sec / total_processed_time_sec
    print(f"{engine} real-time factor is {real_time_factor}\n")


if __name__ == '__main__':
    main()
