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
from collections import namedtuple
from enum import Enum

import numpy as np
import webrtcvad
import pvcobra


DEFAULT_SAMPLERATE = 16000


class Engines(Enum):
    WEBRTC = 'WebRTC'
    COBRA = 'Cobra'


SensitivityInfo = namedtuple('SensitivityInfo', 'min, max, step')


class Engine(object):
    def process(self, pcm):
        raise NotImplementedError()

    def release(self):
        raise NotImplementedError()

    def __str__(self):
        raise NotImplementedError()

    @staticmethod
    def sensitivity_info(engine_type):
        if engine_type is Engines.COBRA:
            return SensitivityInfo(0.0, 1.0, 0.005)
        elif engine_type is Engines.WEBRTC:
            return SensitivityInfo(0, 3, 1)
        else:
            raise ValueError("no sensitivity range for '%s'", engine_type.value)

    @staticmethod
    def create(engine, sensitivity, access_key=None):
        if engine is Engines.COBRA:
            return CobraEngine(sensitivity, access_key)
        elif engine is Engines.WEBRTC:
            return RTCEngine(sensitivity)
        else:
            ValueError("cannot create engine of type '%s'", engine.value)


class CobraEngine(Engine):
    cache = dict()

    def __init__(self, sensitivity, access_key):
        self._cobra = pvcobra.Cobra(access_key=access_key, library_path=pvcobra.LIBRARY_PATH)
        self._threshold = sensitivity

    def process(self, pcm, frame_key):
        assert pcm.dtype == np.int16

        voice_probability = None
        if frame_key in self.cache:
            voice_probability = self.cache[frame_key]
        else:
            voice_probability = self._cobra.process(pcm)
            self.cache[frame_key] = voice_probability

        return voice_probability >= self._threshold

    def frame_length(self):
        return self._cobra.frame_length

    def release(self):
        self._cobra.delete()

    def __str__(self):
        return 'Cobra'


class RTCEngine(Engine):
    def __init__(self, sensitivity):
        self._vad = webrtcvad.Vad(int(sensitivity))

    def process(self, pcm, frame_key):
        assert pcm.dtype == np.int16

        return self._vad.is_speech(pcm.tobytes(), DEFAULT_SAMPLERATE)

    def frame_length(self):
        return int((DEFAULT_SAMPLERATE / 1000) * 30)  # 30ms

    def release(self):
        pass

    def __str__(self):
        return 'WebRTC'
