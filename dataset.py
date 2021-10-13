#
# Copyright 2021 Picovoice Inc.
#
# You may not use this file except in compliance with the license.
# A copy of the license is located in the "LICENSE" file accompanying this source.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#

import os
from enum import Enum

import numpy as np
import soundfile


class Datasets(Enum):
    DEMAND = 'DEMAND'
    LIBRI_SPEECH = "LibriSpeech"


class Dataset(object):
    def __init__(self):
        self._random = np.random.RandomState(seed=778)

    def get(self, index, dtype=np.int16):
        pcm, sample_rate = soundfile.read(self._paths[index], dtype=dtype)
        assert sample_rate == self.sample_rate()

        return pcm

    def random(self, dtype=np.int16):
        return self.get(self._random.randint(low=0, high=self.size()), dtype=dtype)

    def size(self):
        return len(self._paths)

    @staticmethod
    def sample_rate():
        return 16000

    @classmethod
    def create(cls, dataset, path, **kwargs):
        if dataset is Datasets.DEMAND:
            return DEMANDDataset(path)
        elif dataset is Datasets.LIBRI_SPEECH:
            return LibriSpeechDataset(path, *kwargs)
        else:
            raise ValueError("cannot create dataset of type '%s'", dataset.value)

    @property
    def _paths(self):
        raise NotImplementedError()


class DEMANDDataset(Dataset):
    def __init__(self, path):
        super(DEMANDDataset, self).__init__()

        blocklist = [
            "OMEETING",
            "PCAFETER",
            "PRESTO",
            "SCAFE",
            "SPSQUARE",
            "TBUS",
            "TMETRO",
        ]

        self.__paths = list()
        for noise_type in os.listdir(path):
            if noise_type not in blocklist:
                noise_dir = os.path.join(path, noise_type)
                for audio_file in os.listdir(noise_dir):
                    if 'wav' in audio_file:
                        self.__paths.append(os.path.join(noise_dir, audio_file))
        self.__paths.sort()

    @property
    def _paths(self):
        return self.__paths


class LibriSpeechDataset(Dataset):
    def __init__(self, path):
        super(LibriSpeechDataset, self).__init__()

        self.__paths = list()
        for speaker_id in os.listdir(path):
            speaker_dir = os.path.join(path, speaker_id)
            for chapter_id in os.listdir(speaker_dir):
                chapter_dir = os.path.join(speaker_dir, chapter_id)
                for audio_file in os.listdir(chapter_dir):
                    if 'flac' in audio_file:
                        self.__paths.append(os.path.join(chapter_dir, audio_file))
        self.__paths.sort()

    @property
    def _paths(self):
        return self.__paths
